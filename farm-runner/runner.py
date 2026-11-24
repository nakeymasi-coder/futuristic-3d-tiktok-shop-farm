#!/usr/bin/env python3
"""
FARM RUNNER — the executor for Glam's TikTok Shop farm.

Built Nov 24, 2026, after the full critical audit found the farm had no runner:
the page performed runs instead of conducting them, status was whatever a
dropdown said, and the real "runner" was a prompt pasted into a chat.

This runner fixes that mechanically:

- A run is a folder on disk: ~/workspace/farm-runs/run-<date>-<n>/
- Status is DERIVED from evidence in the folder. There is no status field
  anyone can edit and no set-status command. `status` recomputes from the
  files every time and rewrites the derived block on the run sheet.
- Gates have teeth: `check` verifies every prior gate's evidence and fails
  loudly (nonzero exit + the reason written onto the run sheet) when it
  doesn't hold.
- `drive` advances a run automatically through every step that does not
  need a human, and stops cold at the human gates:
    * Step 6  — Glam's script approval
    * Step 10 — Mila's QC verdict (Mila is QC owner; Glam is final gate)
    * Review  — Glam's final review of the finished video
- Step 11 (Caption & Post) is FREEZE-LOCKED in code. The runner has no
  posting action of any kind. A finished run ends at
  "Ready for Glam — freeze on." Automation NEVER posts.

On-demand or scheduled: `drive-all` is what a scheduler calls. The driver
works whatever run folders exist — no product, product plan, or script is
hard-coded anywhere in this file or in any job body.

Evidence map (what clears each step):
  1 Start Run      config.json exists (the run was created)
  2 Scout          steps/step2-scout/scout.md with real findings AND a
                   "Story:" line — one real sentence in Glam's voice: who
                   this is for and why they'd care. No story line, no
                   handoff: findings alone never clear this step.
  3 Pick           steps/step3-pick/pick.md, non-empty (pick also in config)
  4 Product Photo  an image file in steps/step4-photo/
  5 Photo Match    steps/step5-match/match-verdict.md with verdict: MATCH,
                   signed by a checker who is NOT the grabber of record
  6 Script         steps/step6-script/script.md non-empty AND
                   steps/step6-script/glam-approval.md (approved_by: Glam)
  7 Styled Image   an image file in steps/step7-styled/
  8 Package        steps/step8-package/package.md present AND passing lint
                   (references-only, no product words, staging bar)
  9 Build          a video file in steps/step9-builds/
 10 Checks         steps/step10-qc/mila-verdict.md with verdict: PASS,
                   checker: Mila (collected from the QC handoff folder)
 11 Caption & Post FREEZE-LOCKED — never clears, by design
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / "workspace"
RUNS_DIR = WORKSPACE / "farm-runs"
HANDOFF_DIR = WORKSPACE / "farm-qc-handoff"
RUNNER_DIR = WORKSPACE / "farm-runner"
MANIFEST_JSON = RUNNER_DIR / "review-manifest.json"
REVIEW_HTML = RUNNER_DIR / "review-section.html"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}

STEP_DEFS = [
    (1, "Start Run"),
    (2, "Scout"),
    (3, "Pick"),
    (4, "Product Photo"),
    (5, "Photo Match Check"),
    (6, "Script"),
    (7, "Styled Image"),
    (8, "Package"),
    (9, "Build"),
    (10, "Checks — Mila (QC owner)"),
    (11, "Caption & Post"),
]

STEP_DIRS = {
    2: "step2-scout",
    3: "step3-pick",
    4: "step4-photo",
    5: "step5-match",
    6: "step6-script",
    7: "step7-styled",
    8: "step8-package",
    9: "step9-builds",
    10: "step10-qc",
}

# ----------------------------------------------------------------------------
# Package lint — the bars the Nov 24 failures proved are needed.
# PRODUCT RULE (Glam, Nov 24, Emma's diagnosis): never describe the product in
# words in a prompt. The actual listing photo is the reference; word prompts
# make the model invent the product and its lettering.
# STAGING BAR (farm Steps 6 & 8): product stationary by default — on the
# counter, no hands on it, clean close-up at the end. A pour, hand-off, or any
# handling/full-motion product shot is a send-back unless a staging proof
# (steps/step8-package/staging-proof.md) records a test build that proved
# that exact staging.
# ----------------------------------------------------------------------------

LABEL_WORDING_PATTERNS = [
    r"label\s+(reads|says|shows|that\s+reads)",
    r"the\s+label\s+(reads|says|shows)",
    r"\blabel\s*:\s*[\"“\w]",
    r"\breads\s+[\"“][^\"”]{2,}[\"”]\s+on\s+(the\s+)?(label|bottle|packaging)",
]

PRODUCT_DESCRIPTION_TERMS = [
    "the exact product",
    "clear bottle", "rectangular bottle", "tall bottle", "small bottle",
    "amber bottle", "white bottle", "glass bottle", "plastic bottle",
    "gold cap", "screw cap", "dropper cap", "metallic cap", "small cap",
    "golden oil", "yellow-gold", "yellow gold oil",
    "200ml", "6.76oz", "6.76 oz",
]

PRODUCT_DESCRIPTION_PATTERNS = [
    r"\b(tall|small|clear|rectangular|amber|white|glass|plastic|slim)\s+(\w+\s+)?bottle\b",
    r"\bbottle\s+of\s+[^,.\"]{0,50}\boil\b",
]

STAGING_PATTERNS = [
    r"\bpour(s|ing|ed)?\b",
    r"\btips?\s+the\s+bottle\b",
    r"\btipping\b",
    r"\bhand-?off\b",
    r"\bhands?\s+(her|him|them|the\s+model)\s+the\s+bottle\b",
    r"\bpasses\s+the\s+bottle\b",
    r"\braises?\s+the\s+bottle\b",
    r"\braised\s+beside\b",
    r"\bholds?\s+the\s+bottle\b",
    r"\bholding\s+the\s+bottle\b",
    r"\bbottle\s+in\s+(her|his|one|the)\s+hand\b",
    r"\bin\s+her\s+other\s+hand\b",
    r"\bshakes?\s+the\s+bottle\b",
    r"\bunscrew",
    r"\bopens?\s+the\s+bottle\b",
    r"\bpools?\s+in\s+(her|his|the)\s+palm\b",
    r"\bsmooths?\s+[^.]{0,40}\bbottle\s+in\s+hand\b",
]

GUARD_PATTERNS = [
    r"never\s+spoken,\s+never\s+mouthed",
    r"the\s+only\s+spoken\s+words\s+in\s+this\s+entire\s+video",
    r"silent\s+visual\s+direction",
]

REFERENCES_LINE = re.compile(r"references?\s*:", re.IGNORECASE)
LISTING_PHOTO_MENTION = re.compile(r"listing\s+photo", re.IGNORECASE)


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def resolve_run(arg):
    p = Path(arg).expanduser()
    if p.is_dir():
        return p
    cand = RUNS_DIR / arg
    if cand.is_dir():
        return cand
    raise SystemExit(f"Run not found: {arg} (looked for {p} and {cand})")


def load_config(run):
    cfg_path = run / "config.json"
    if not cfg_path.exists():
        raise SystemExit(f"Not a runner run folder (no config.json): {run}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def parse_kv(path):
    """Parse simple 'key: value' lines from a small record file."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*([A-Za-z_][\w ]*?)\s*:\s*(.+?)\s*$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


def files_with_ext(folder, exts):
    if not folder.is_dir():
        return []
    return sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in exts
    )


def nonempty_file(path):
    return path.exists() and path.read_text(
        encoding="utf-8", errors="replace").strip() != ""


# Spec / label words that make a "story sentence" label copy, not a story
# (Glam + Claude, Nov 24 — the smart story check, first version).
STORY_SPEC_WORDS = (
    "ml", "milliliter", "milliliters", "millilitre", "millilitres",
    "oz", "ounce", "ounces", "gram", "grams", "kg", "mg", "percent", "%",
    "plant-based", "plant based", "made with", "formula", "ingredient",
    "ingredients", "net wt", "fl oz",
)
# The sentence must be about a PERSON — one of these has to be in it. The
# list is spelled out on purpose (Claude, Nov 24): the check needs something
# concrete to look for.
STORY_PERSON_WORDS = (
    "you", "your", "yours", "her", "hers", "she", "i", "i'm", "my", "me",
    "we", "our", "mom", "grandma", "sister", "friend", "girl", "woman",
    "women", "ladies", "he", "his", "him",
)


def story_sentence_state(path):
    """The Scout's story sentence, checked the smart way. Returns
    (ok, reason). The 'Story:' line in scout.md must carry ONE real sentence
    in Glam's voice that (1) is a real sentence (>= 5 words), (2) contains
    NO spec/label word and no number — label copy fails, and (3) names a
    PERSON (you, her, my, she, a mom, a grandma, a friend...) and her
    moment. Findings without a passing sentence do not hand off."""
    if not path.exists():
        return (False, "no scout file on file")
    sentence = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip().lstrip("#").strip()
        if s.lower().startswith("story:"):
            sentence = s.split(":", 1)[1].strip()
            break
    if sentence is None:
        return (False, "no 'Story:' line in scout.md")
    if len(sentence.split()) < 5:
        return (False, "the 'Story:' line is under 5 words — not a real sentence")
    if any(ch.isdigit() for ch in sentence):
        return (False, "story sentence FAILED the smart story check — it "
                       "contains a number: it names a spec, not a person "
                       "(label copy does not leave the Scout)")
    low = sentence.lower()
    for w in STORY_SPEC_WORDS:
        hit = (re.search(r"\b" + re.escape(w) + r"\b", low)
               if w.replace("-", "").isalpha() else w in low)
        if hit:
            return (False, f"story sentence FAILED the smart story check — "
                           f"it contains the spec/label word '{w}': it names "
                           "a spec, not a person (label copy does not leave "
                           "the Scout)")
    tokens = set(re.findall(r"[a-z']+", low))
    if not tokens.intersection(STORY_PERSON_WORDS):
        return (False, "story sentence FAILED the smart story check — it "
                       "names nobody: no person word (you, her, my, she, a "
                       "mom, a grandma, a friend) and no real moment")
    return (True, "story sentence on file and passing the smart story check")


def sheet_log(run, message):
    """Append one line to the run sheet's GATE LOG (runner-written only)."""
    sheet = run / "RUN-SHEET.md"
    line = f"- [{now_stamp()}] {message}\n"
    if sheet.exists():
        text = sheet.read_text(encoding="utf-8")
        if "## GATE LOG" not in text:
            text += "\n## GATE LOG (appended by the runner only — never hand-edited)\n"
        sheet.write_text(text + line, encoding="utf-8")


# ----------------------------------------------------------------------------
# Package lint
# ----------------------------------------------------------------------------

def lint_package(run):
    """Return a list of findings: (category, line_no, line_text)."""
    pkg_path = run / "steps" / STEP_DIRS[8] / "package.md"
    findings = []
    if not pkg_path.exists():
        return [("MISSING", 0, "package.md not present")]
    text = pkg_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    staging_proof = (run / "steps" / STEP_DIRS[8] / "staging-proof.md").exists()

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        low = line.lower()
        if not line:
            continue
        for pat in LABEL_WORDING_PATTERNS:
            if re.search(pat, low):
                findings.append(("LABEL WORDING", i, line))
                break
        for term in PRODUCT_DESCRIPTION_TERMS:
            if term in low:
                findings.append(("PRODUCT DESCRIPTION", i, line))
                break
        else:
            for pat in PRODUCT_DESCRIPTION_PATTERNS:
                if re.search(pat, low):
                    findings.append(("PRODUCT DESCRIPTION", i, line))
                    break
        for pat in GUARD_PATTERNS:
            if re.search(pat, low):
                findings.append(("RETIRED GUARD TEXT", i, line))
                break
        for pat in STAGING_PATTERNS:
            if re.search(pat, low):
                cat = "STAGING (proof on file)" if staging_proof else "STAGING"
                findings.append((cat, i, line))
                break

    if not REFERENCES_LINE.search(text):
        findings.append(("REFERENCES", 0,
                         "no 'References:' line — package must declare its references"))
    elif not LISTING_PHOTO_MENTION.search(text):
        findings.append(("REFERENCES", 0,
                         "references do not name the listing photo — the build's "
                         "references are the approved styled image AND the real "
                         "listing photo"))
    return findings


def blocking_findings(findings):
    """Findings that block Step 8 (staging findings are waived only by proof)."""
    return [f for f in findings if f[0] != "STAGING (proof on file)"]


# ----------------------------------------------------------------------------
# Evidence derivation — the ONLY source of status
# ----------------------------------------------------------------------------

def eval_step(run, cfg, n):
    """Return (state, reason). state: CLEARED | WAITING | INVALID | FROZEN."""
    steps = run / "steps"
    if n == 1:
        return ("CLEARED", "run created; config recorded from operator input")
    if n == 2:
        scout = steps / STEP_DIRS[2] / "scout.md"
        if not nonempty_file(scout):
            return ("WAITING", "no scout findings on file (steps/step2-scout/scout.md)")
        ok, why = story_sentence_state(scout)
        if not ok:
            return ("WAITING", f"scout findings on file but the story sentence "
                               f"does not pass — {why}. The Scout does not hand "
                               "off without one real sentence in Glam's voice: "
                               "who this is for and why they'd care (a 'Story:' "
                               "line in steps/step2-scout/scout.md)")
        return ("CLEARED", "scout findings + story sentence on file "
                           "(smart story check passed)")
    if n == 3:
        if nonempty_file(steps / STEP_DIRS[3] / "pick.md") and cfg.get("pick"):
            return ("CLEARED", f"pick recorded: {cfg['pick']}")
        return ("WAITING", "no pick record on file (steps/step3-pick/pick.md)")
    if n == 4:
        photos = files_with_ext(steps / STEP_DIRS[4], IMAGE_EXTS)
        if photos:
            return ("CLEARED", f"listing photo attached: {photos[0].name}")
        return ("WAITING", "no product photo attached — no photo in hand, "
                           "no scene, no script, full stop")
    if n == 5:
        verdict_path = steps / STEP_DIRS[5] / "match-verdict.md"
        if not verdict_path.exists():
            return ("WAITING", "no match verdict recorded — the grabbed photo "
                               "has not been checked against the listing's own image")
        kv = parse_kv(verdict_path)
        verdict = kv.get("verdict", "").upper()
        checker = kv.get("checker", "")
        grabber = kv.get("grabber", "")
        if verdict != "MATCH":
            return ("INVALID", f"match verdict on file is '{verdict or 'blank'}', "
                               "not MATCH — run is blocked at the Photo Match Check")
        if not checker or not grabber:
            return ("INVALID", "match verdict is missing its checker or grabber name")
        if checker.strip().lower() == grabber.strip().lower():
            return ("INVALID", f"match verdict was signed by the grabber "
                               f"({checker}) — the checker must NOT be the person "
                               "who grabbed the photo; a self-check does not count")
        grabbed_by_file = steps / STEP_DIRS[4] / "GRABBED-BY.txt"
        if grabbed_by_file.exists():
            recorded = grabbed_by_file.read_text(
                encoding="utf-8", errors="replace").strip()
            if recorded and recorded.lower() != grabber.lower():
                return ("INVALID", f"match verdict names grabber '{grabber}' but "
                                   f"the photo on file was grabbed by '{recorded}' — "
                                   "the record does not line up")
            if recorded and recorded.lower() == checker.lower():
                return ("INVALID", f"match checker ({checker}) is the grabber of "
                                   "record for this photo — checker ≠ grabber")
        return ("CLEARED", f"photo MATCH recorded by {checker} "
                           f"(grabber: {grabber}) against the listing's own image")
    if n == 6:
        script_ok = nonempty_file(steps / STEP_DIRS[6] / "script.md")
        approval = parse_kv(steps / STEP_DIRS[6] / "glam-approval.md")
        approved = approval.get("approved_by", "").lower() == "glam"
        if script_ok and approved:
            return ("CLEARED", "script on file and Glam's approval recorded")
        if script_ok and not approved:
            return ("WAITING", "script is written but Glam has not approved it — "
                               "human gate: Glam's script approval")
        return ("WAITING", "no script on file (steps/step6-script/script.md)")
    if n == 7:
        imgs = files_with_ext(steps / STEP_DIRS[7], IMAGE_EXTS)
        if imgs:
            return ("CLEARED", f"styled image on file: {imgs[0].name}")
        return ("WAITING", "no styled image on file (steps/step7-styled/)")
    if n == 8:
        pkg = steps / STEP_DIRS[8] / "package.md"
        if not pkg.exists():
            return ("WAITING", "no package on file (steps/step8-package/package.md)")
        bad = blocking_findings(lint_package(run))
        if bad:
            cats = ", ".join(sorted({f[0] for f in bad}))
            return ("INVALID", f"package FAILS lint ({cats}) — "
                               f"{len(bad)} blocking finding(s); run `lint` for detail")
        return ("CLEARED", "package on file and passing lint "
                           "(references-only, staging bar holds)")
    if n == 9:
        vids = files_with_ext(steps / STEP_DIRS[9], VIDEO_EXTS)
        if vids:
            names = ", ".join(v.name for v in vids)
            return ("CLEARED", f"build file(s) on file: {names}")
        return ("WAITING", "no build files on file (steps/step9-builds/)")
    if n == 10:
        verdict_path = steps / STEP_DIRS[10] / "mila-verdict.md"
        if not verdict_path.exists():
            return ("WAITING", "no QC verdict collected — human gate: Mila's "
                               "check (QC owner) has not ruled on this build")
        kv = parse_kv(verdict_path)
        verdict = kv.get("verdict", "").upper()
        checker = kv.get("checker", "")
        if verdict == "PASS" and checker.strip().lower() == "mila":
            return ("CLEARED", "Mila's PASS recorded in the run folder")
        if verdict == "PASS":
            return ("INVALID", f"a PASS is on file but signed by '{checker}' — "
                               "only Mila, the QC owner, can pass a build")
        return ("INVALID", f"Mila's verdict on file is '{verdict or 'blank'}' — "
                           "the build was sent back; the run does not advance")
    if n == 11:
        return ("FROZEN", "posting freeze is ON — the runner has no posting "
                          "action; Step 11 never clears here")
    raise ValueError(n)


def derive(run):
    cfg = load_config(run)
    results = []
    blocked = False
    for n, name in STEP_DEFS:
        state, reason = eval_step(run, cfg, n)
        if blocked and state == "CLEARED":
            state = "BLOCKED"
            reason = f"evidence exists, but an earlier gate has not cleared: {reason}"
        if state in ("WAITING", "INVALID") and n != 11:
            blocked = True
        results.append((n, name, state, reason))
    return cfg, results


def headline(results):
    for n, name, state, reason in results:
        if n == 11:
            break
        if state == "INVALID":
            return f"STOPPED at Step {n} ({name}) — {reason}"
        if state in ("WAITING", "BLOCKED"):
            return f"BLOCKED at Step {n} ({name}) — {reason}"
    return "Ready for Glam — freeze on."


def render_status(run):
    cfg, results = derive(run)
    out = []
    out.append(f"RUN {cfg['run_id']} — {cfg['pick']} · {cfg['cast_model']} · "
               f"{cfg['mode']} · {cfg['account']}")
    out.append("Status derived from evidence on disk at "
               f"{now_stamp()} — never set by hand.")
    out.append("")
    for n, name, state, reason in results:
        out.append(f"  Step {n:<2} {name:<28} {state:<8} {reason}")
    out.append("")
    out.append(f"HEADLINE: {headline(results)}")
    return "\n".join(out), results


def write_derived_block(run):
    text, _ = render_status(run)
    sheet = run / "RUN-SHEET.md"
    if not sheet.exists():
        return
    content = sheet.read_text(encoding="utf-8")
    block = ("<!-- DERIVED-STATUS:BEGIN -->\n```\n" + text +
             "\n```\n<!-- DERIVED-STATUS:END -->")
    if "<!-- DERIVED-STATUS:BEGIN -->" in content:
        content = re.sub(
            r"<!-- DERIVED-STATUS:BEGIN -->.*?<!-- DERIVED-STATUS:END -->",
            block, content, flags=re.DOTALL)
    else:
        content += "\n\n## DERIVED STATUS (regenerated by the runner on every status call)\n" + block + "\n"
    sheet.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def cmd_create(args):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    n = 1
    while (RUNS_DIR / f"run-{today}-{n}").exists():
        n += 1
    run_id = f"run-{today}-{n}"
    run = RUNS_DIR / run_id
    (run / "steps").mkdir(parents=True)
    for d in STEP_DIRS.values():
        (run / "steps" / d).mkdir()
    cfg = {
        "run_id": run_id,
        "created_at": now_stamp(),
        "created_by": args.by,
        "account": args.account,
        "pick": args.pick,
        "pick_id": args.pick_id or "",
        "cast_model": args.model,
        "mode": args.mode,
        "freeze": "ON",
    }
    (run / "config.json").write_text(json.dumps(cfg, indent=2) + "\n",
                                     encoding="utf-8")
    sheet = f"""# RUN SHEET — {run_id}

- Account: {cfg['account']}
- Pick: {cfg['pick']}{(' (ID ' + cfg['pick_id'] + ')') if cfg['pick_id'] else ''}
- Cast model: {cfg['cast_model']}
- Mode: {cfg['mode']}
- Created: {cfg['created_at']} by {cfg['created_by']}
- Posting freeze: ON — this run ends at "Ready for Glam — freeze on."

## HOW STATUS WORKS HERE
Statuses are NOT written on this sheet by hand and there is no status field
to edit. The runner derives them from the evidence files in `steps/` every
time `status` runs, and rewrites the block below. Evidence map:
photo in steps/step4-photo/ → Step 4 · match verdict signed by a checker who
is not the grabber → Step 5 · script + Glam's approval marker → Step 6 ·
package passing lint → Step 8 · build files → Step 9 · Mila's PASS verdict
in steps/step10-qc/ → Step 10 · Step 11 is freeze-locked, always.

<!-- DERIVED-STATUS:BEGIN -->
(not derived yet — run: python3 ~/workspace/farm-runner/runner.py status {run_id})
<!-- DERIVED-STATUS:END -->

## GATE LOG (appended by the runner only — never hand-edited)
- [{cfg['created_at']}] Run created by {cfg['created_by']}. Statuses start empty; they are earned by evidence only.
"""
    (run / "RUN-SHEET.md").write_text(sheet, encoding="utf-8")
    print(f"Created {run}")
    print(f"Run ID: {run_id}")
    print("Next: place scout findings at steps/step2-scout/scout.md — including "
          "the Story: line, one real sentence in Glam's voice (who it's for, why "
          "they'd care); Step 2 does not clear without it — then the pick "
          "record at steps/step3-pick/pick.md, then attach the listing photo "
          "with attach-photo. Or just run `drive` — it advances what's ready "
          "and stops at the first gate that needs a human or missing evidence.")
    return 0


def cmd_status(args):
    run = resolve_run(args.run)
    text, _ = render_status(run)
    write_derived_block(run)
    print(text)
    return 0


def cmd_check(args):
    run = resolve_run(args.run)
    target = args.to
    if target == 11:
        msg = ("CHECK to Step 11 REFUSED — Step 11 (Caption & Post) is "
               "FREEZE-LOCKED. The posting freeze is ON and the runner has no "
               "posting action. A finished run ends at 'Ready for Glam — "
               "freeze on.' Only Glam lifts the freeze, outside the runner.")
        print(msg)
        sheet_log(run, "CHECK to Step 11: REFUSED — freeze-locked (posting freeze ON).")
        return 3
    cfg, results = derive(run)
    failures = [(n, name, state, reason) for (n, name, state, reason) in results
                if n < target and state != "CLEARED"]
    if failures:
        print(f"CHECK to Step {target}: REFUSED — prior gate(s) do not hold:")
        for n, name, state, reason in failures:
            print(f"  Step {n} ({name}): {state} — {reason}")
        first = failures[0]
        sheet_log(run, f"CHECK to Step {target}: REFUSED — Step {first[0]} "
                       f"({first[1]}): {first[3]}")
        return 2
    print(f"CHECK to Step {target}: OK — every prior gate (Steps 1–{target - 1}) "
          "holds its evidence.")
    sheet_log(run, f"CHECK to Step {target}: OK — all prior gates hold evidence.")
    return 0


def cmd_attach_photo(args):
    run = resolve_run(args.run)
    src = Path(args.file).expanduser()
    if not src.exists():
        raise SystemExit(f"Photo file not found: {src}")
    if src.suffix.lower() not in IMAGE_EXTS:
        raise SystemExit(f"Not an image file ({src.suffix}); the Step 4 "
                         "evidence must be the listing photo image itself.")
    dest_dir = run / "steps" / STEP_DIRS[4]
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    (dest_dir / "GRABBED-BY.txt").write_text(args.by + "\n", encoding="utf-8")
    sheet_log(run, f"Step 4: listing photo attached ({src.name}), grabbed by {args.by}.")
    print(f"Attached {src.name} to {run.name}/steps/step4-photo/ (grabber of record: {args.by})")
    return 0


def cmd_record_match(args):
    run = resolve_run(args.run)
    dest = run / "steps" / STEP_DIRS[5] / "match-verdict.md"
    body = (
        f"verdict: {args.verdict}\n"
        f"checker: {args.checker}\n"
        f"grabber: {args.grabber}\n"
        f"compared_against: the listing's own product image + the picked product's name\n"
        f"recorded_at: {now_stamp()}\n"
        f"notes: {args.notes or ''}\n"
    )
    dest.write_text(body, encoding="utf-8")
    sheet_log(run, f"Step 5: match verdict recorded — {args.verdict} by "
                   f"{args.checker} (grabber: {args.grabber}).")
    print(f"Recorded match verdict for {run.name}: {args.verdict} "
          f"(checker: {args.checker}, grabber: {args.grabber})")
    if args.checker.strip().lower() == args.grabber.strip().lower():
        print("WARNING: checker == grabber. The derivation will REFUSE to "
              "count this verdict — a self-check is not a check.")
    return 0


def cmd_approve_script(args):
    run = resolve_run(args.run)
    dest = run / "steps" / STEP_DIRS[6] / "glam-approval.md"
    body = (f"approved_by: Glam\n"
            f"recorded_by: {args.recorded_by}\n"
            f"recorded_at: {now_stamp()}\n")
    dest.write_text(body, encoding="utf-8")
    sheet_log(run, "Step 6: Glam's script approval recorded "
                   f"(entered by {args.recorded_by}).")
    print(f"Recorded Glam's script approval for {run.name}. "
          "Only run this after Glam has actually approved the script.")
    return 0


def cmd_lint(args):
    run = resolve_run(args.run)
    findings = lint_package(run)
    if not findings:
        print("LINT: package passes — no label wording, no product description "
              "in words, no retired guard text, staging bar holds, references "
              "declared (styled image + listing photo).")
        return 0
    print(f"LINT: {len(findings)} finding(s):")
    for cat, line_no, text in findings:
        where = f"line {line_no}" if line_no else "package"
        print(f"  [{cat}] {where}: {text[:120]}")
    bad = blocking_findings(findings)
    if bad:
        print(f"LINT RESULT: FAIL — {len(bad)} blocking finding(s). Step 8 cannot clear.")
        return 2
    print("LINT RESULT: PASS with staging proof on file (staging findings waived by proof).")
    return 0


def handoff_dir_for(run_id):
    return HANDOFF_DIR / run_id


def cmd_handoff(args):
    run = resolve_run(args.run)
    cfg = load_config(run)
    builds = sorted(f for f in (run / "steps" / STEP_DIRS[9]).iterdir()
                    if f.is_file()) if (run / "steps" / STEP_DIRS[9]).is_dir() else []
    if not builds:
        print("HANDOFF REFUSED — no build files in steps/step9-builds/. "
              "There is nothing to hand to Mila.")
        sheet_log(run, "HANDOFF refused — no build files on file.")
        return 2
    dest = handoff_dir_for(cfg["run_id"])
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for b in builds:
        shutil.copy2(b, dest / b.name)
        copied.append(b.name)
    script = run / "steps" / STEP_DIRS[6] / "script.md"
    if script.exists():
        shutil.copy2(script, dest / "approved-script.md")
        copied.append("approved-script.md (the approved script lines)")
    photos = files_with_ext(run / "steps" / STEP_DIRS[4], IMAGE_EXTS)
    for p in photos:
        shutil.copy2(p, dest / f"listing-photo{p.suffix.lower()}")
        copied.append(f"listing-photo{p.suffix.lower()} (for Mila's bottle check)")
    manifest = (
        f"# QC HANDOFF — {cfg['run_id']}\n"
        f"Handed off at {now_stamp()} by the farm runner.\n"
        f"Product: {cfg['pick']} · Model: {cfg['cast_model']} · Mode: {cfg['mode']}\n"
        f"Build files in the run folder: {len(builds)} — files copied here: "
        f"{len(copied)} (every build, good and bad; the builder selects nothing).\n"
        + "".join(f"- {c}\n" for c in copied)
        + "\nMila: check per ~/workspace/farm-qc-handoff/README.md — frame by "
          "frame through the motion, bottle first, then ASR diff against "
          "approved-script.md. Write your verdict to verdict.md in this "
          "folder (verdict: PASS or FAIL, checker: Mila, with the frames/"
          "lines behind it).\n"
    )
    (dest / "HANDOFF.md").write_text(manifest, encoding="utf-8")
    sheet_log(run, f"Step 9→10: QC handoff copied EVERY build "
                   f"({len(builds)} file(s)) + script + listing photo to "
                   f"farm-qc-handoff/{cfg['run_id']}/.")
    print(f"Handed off {len(builds)} build file(s) for {cfg['run_id']} to {dest}")
    print("Mila pulls from there. The builder selected nothing — every build went.")
    return 0


def cmd_collect_verdict(args):
    run = resolve_run(args.run)
    cfg = load_config(run)
    src = handoff_dir_for(cfg["run_id"]) / "verdict.md"
    if not src.exists():
        print(f"No verdict.md waiting in farm-qc-handoff/{cfg['run_id']}/ — "
              "Mila has not ruled yet.")
        return 2
    dest = run / "steps" / STEP_DIRS[10] / "mila-verdict.md"
    shutil.copy2(src, dest)
    kv = parse_kv(dest)
    sheet_log(run, f"Step 10: Mila's verdict collected from the QC handoff — "
                   f"{kv.get('verdict', '?')} (checker: {kv.get('checker', '?')}).")
    print(f"Collected Mila's verdict for {cfg['run_id']}: "
          f"{kv.get('verdict', '?')} — now on file at steps/step10-qc/mila-verdict.md")
    return 0


# ----------------------------------------------------------------------------
# The automatic driver
# ----------------------------------------------------------------------------

def drive_run(run):
    """Advance one run as far as evidence + automation allow.

    Returns a list of log lines describing what the driver did and where
    and why it stopped. Human gates stop it cold. It never posts.
    """
    cfg = load_config(run)
    log = []

    def note(msg):
        log.append(msg)
        sheet_log(run, f"DRIVE: {msg}")

    for _ in range(12):  # bounded passes; each pass must do something or stop
        _, results = derive(run)
        states = {n: (state, reason) for n, name, state, reason in results}
        first_open = None
        for n, name in STEP_DEFS:
            if n == 11:
                break
            if states[n][0] != "CLEARED":
                first_open = n
                break
        if first_open is None:
            build_review_manifest()
            note("Run is complete through Step 10 — landed in Review as "
                 "'Waiting for Glam'. STOP — human gate: Glam's final "
                 "review. Freeze on; nothing posts.")
            break
        state, reason = states[first_open]
        if first_open == 6:
            script_exists = nonempty_file(run / "steps" / STEP_DIRS[6] / "script.md")
            if script_exists:
                note("STOP at Step 6 — human gate: Glam's script approval. "
                     "The script is written; the driver cannot approve it.")
            else:
                note("STOP at Step 6 — no script on file yet. Writing the "
                     "script is an agent step; the driver resumes once the "
                     "script and Glam's approval are on file.")
            break
        if first_open == 8 and state == "INVALID":
            note(f"STOP at Step 8 — {reason}")
            break
        if first_open == 10:
            builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
            dest = handoff_dir_for(cfg["run_id"])
            handed = dest.is_dir() and all(
                (dest / b.name).exists() for b in builds) and builds
            verdict_waiting = (dest / "verdict.md").exists()
            if builds and not handed:
                cmd_handoff(argparse.Namespace(run=str(run)))
                note("Auto-handoff: every build copied to the QC handoff "
                     "folder for Mila.")
                continue
            if verdict_waiting:
                cmd_collect_verdict(argparse.Namespace(run=str(run)))
                note("Auto-collected Mila's verdict from the QC handoff folder.")
                continue
            if state == "INVALID":
                note(f"STOP at Step 10 — {reason}")
            else:
                note("STOP at Step 10 — human gate: Mila's QC verdict. "
                     "Builds are in the handoff folder; the driver cannot "
                     "check its own build.")
            break
        # Any other open step: evidence is missing or invalid and producing
        # it is an agent/human step, not something the driver can fabricate.
        note(f"STOP at Step {first_open} — {reason}")
        break
    write_derived_block(run)
    return log


def cmd_drive(args):
    run = resolve_run(args.run)
    print(f"DRIVING {run.name} …")
    for line in drive_run(run):
        print(f"  {line}")
    build_review_manifest()
    return 0


def cmd_drive_all(args):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted(d for d in RUNS_DIR.iterdir()
                  if d.is_dir() and (d / "config.json").exists())
    if not runs:
        print("drive-all: no runs in ~/workspace/farm-runs/ — nothing to drive.")
        return 0
    for run in runs:
        print(f"DRIVING {run.name} …")
        for line in drive_run(run):
            print(f"  {line}")
    build_review_manifest()
    print(f"drive-all: drove {len(runs)} run(s); review manifest refreshed.")
    return 0


# ----------------------------------------------------------------------------
# Review manifest — every finished video lands on the farm's Review section
# ----------------------------------------------------------------------------

def review_entry(run):
    cfg, results = derive(run)
    states = {n: state for n, name, state, reason in results}
    builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
    if not builds:
        return None
    verdict_kv = parse_kv(run / "steps" / STEP_DIRS[10] / "mila-verdict.md")
    mila_verdict = verdict_kv.get("verdict", "").upper() or "NONE"
    decision = parse_kv(run / "review-decision.md")
    decision_val = decision.get("decision", "").lower()
    if decision_val == "approved" and states.get(10) == "CLEARED":
        status = "Approved"
    elif decision_val == "sent-back" and states.get(10) == "CLEARED":
        status = "Sent back"
    elif states.get(10) == "CLEARED":
        status = "Waiting for Glam"
    else:
        status = "Not ready — waiting on Mila's check"
    return {
        "run_id": cfg["run_id"],
        "product": cfg["pick"],
        "cast_model": cfg["cast_model"],
        "mode": cfg["mode"],
        "account": cfg["account"],
        "mila_verdict": mila_verdict,
        "videos": [f"~/workspace/farm-runs/{cfg['run_id']}/steps/step9-builds/{v.name}"
                   for v in builds],
        "review_status": status,
        "ready_for_review": states.get(10) == "CLEARED",
    }


def build_review_manifest():
    RUNNER_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    if RUNS_DIR.is_dir():
        for run in sorted(d for d in RUNS_DIR.iterdir()
                          if d.is_dir() and (d / "config.json").exists()):
            e = review_entry(run)
            if e:
                entries.append(e)
    manifest = {
        "generated_at": now_stamp(),
        "source": "derived by ~/workspace/farm-runner/runner.py from the run folders",
        "entries": entries,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8")
    html = render_review_html(entries)
    REVIEW_HTML.write_text(html, encoding="utf-8")
    return manifest


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_review_html(entries):
    """The Review section's entries block for the farm page.

    This exact markup sits between REVIEW-ENTRIES:BEGIN / :END markers on
    the farm page; `sync-review` output (this file) is what an artifact
    edit pastes between those markers.
    """
    if not entries:
        return ('<div class="review-empty">No finished videos yet. When a run '
                'finishes its build and clears Mila\'s check, the video '
                'lands here for Glam\'s review.</div>')
    cards = []
    for e in entries:
        test_badge = (' <span class="review-test">TEST</span>'
                      if "TEST" in e["product"].upper() or "MOCK" in e["product"].upper()
                      else "")
        vids = "".join(
            f'<div class="review-video">🎬 {esc(v)}</div>' for v in e["videos"])
        cards.append(
            f'<div class="review-card">'
            f'<div class="review-run">{esc(e["run_id"])}{test_badge}</div>'
            f'<div class="review-product">{esc(e["product"])}</div>'
            f'<div class="review-meta">{esc(e["cast_model"])} · {esc(e["mode"])} · {esc(e["account"])}</div>'
            f'{vids}'
            f'<div class="review-verdict">Mila\'s verdict: {esc(e["mila_verdict"])}</div>'
            f'<div class="review-status">{esc(e["review_status"])}</div>'
            f'</div>')
    return "\n".join(cards)


def cmd_review_manifest(args):
    manifest = build_review_manifest()
    print(f"Review manifest written: {MANIFEST_JSON}")
    print(f"Review section HTML written: {REVIEW_HTML}")
    for e in manifest["entries"]:
        print(f"  {e['run_id']} — {e['product']} — Mila: {e['mila_verdict']} "
              f"— {e['review_status']}")
    if not manifest["entries"]:
        print("  (no runs with build files yet — Review section shows its empty state)")
    return 0


def cmd_review_decision(args):
    run = resolve_run(args.run)
    cfg, results = derive(run)
    states = {n: state for n, name, state, reason in results}
    if states.get(10) != "CLEARED":
        print("REVIEW DECISION REFUSED — this run has not cleared Mila's "
              "check (Step 10), so there is no finished video for Glam to "
              "rule on. A run cannot be approved or sent back before QC.")
        sheet_log(run, f"REVIEW DECISION refused — Step 10 not cleared; "
                       f"attempted decision: {args.decision}.")
        return 2
    body = (f"decision: {args.decision}\n"
            f"decided_by: Glam\n"
            f"recorded_by: {args.recorded_by}\n"
            f"recorded_at: {now_stamp()}\n")
    (run / "review-decision.md").write_text(body, encoding="utf-8")
    sheet_log(run, f"REVIEW: Glam's decision recorded — {args.decision} "
                   f"(entered by {args.recorded_by}). Freeze stays ON; "
                   "approval here is a review verdict, never a post.")
    build_review_manifest()
    print(f"Recorded Glam's review decision for {run.name}: {args.decision}. "
          "The freeze stays on — this records her verdict, it does not post.")
    return 0


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        prog="runner.py",
        description="Farm Runner — evidence-derived executor for the TikTok "
                    "Shop farm. Status comes from evidence, gates have "
                    "teeth, human gates stop the driver, Step 11 is "
                    "freeze-locked. It never posts.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create", help="create a run folder with an empty, earned-only run sheet")
    p.add_argument("--pick", required=True)
    p.add_argument("--pick-id", default="")
    p.add_argument("--model", required=True)
    p.add_argument("--mode", required=True)
    p.add_argument("--account", default="@glamorousgrammyglowup")
    p.add_argument("--by", default="Indigo")
    p.set_defaults(fn=cmd_create)

    p = sub.add_parser("status", help="derive and print the run's true status from evidence")
    p.add_argument("run")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("check", help="verify every prior gate before a target step; fails loudly")
    p.add_argument("run")
    p.add_argument("--to", type=int, required=True)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("attach-photo", help="attach the listing photo as Step 4 evidence")
    p.add_argument("run")
    p.add_argument("file")
    p.add_argument("--by", default="Indigo", help="who grabbed the photo (grabber of record)")
    p.set_defaults(fn=cmd_attach_photo)

    p = sub.add_parser("record-match", help="record the Step 5 Photo Match verdict")
    p.add_argument("run")
    p.add_argument("--checker", required=True)
    p.add_argument("--grabber", required=True)
    p.add_argument("--verdict", required=True, choices=["MATCH", "NO-MATCH"])
    p.add_argument("--notes", default="")
    p.set_defaults(fn=cmd_record_match)

    p = sub.add_parser("approve-script", help="record Glam's Step 6 script approval (only after she approves)")
    p.add_argument("run")
    p.add_argument("--recorded-by", default="Indigo")
    p.set_defaults(fn=cmd_approve_script)

    p = sub.add_parser("lint", help="lint the run's Step 8 package (references-only + staging bar)")
    p.add_argument("run")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("handoff", help="copy EVERY build + script + listing photo to the QC handoff folder")
    p.add_argument("run")
    p.set_defaults(fn=cmd_handoff)

    p = sub.add_parser("collect-verdict", help="collect Mila's verdict from the QC handoff into the run folder")
    p.add_argument("run")
    p.set_defaults(fn=cmd_collect_verdict)

    p = sub.add_parser("drive", help="automatically advance one run until a human gate or missing evidence stops it")
    p.add_argument("run")
    p.set_defaults(fn=cmd_drive)

    p = sub.add_parser("drive-all", help="drive every run in ~/workspace/farm-runs/ (what a scheduler calls)")
    p.set_defaults(fn=cmd_drive_all)

    p = sub.add_parser("review-manifest", help="rebuild the review manifest + farm Review section HTML from the run folders")
    p.set_defaults(fn=cmd_review_manifest)

    p = sub.add_parser("review-decision", help="record Glam's review verdict on a finished video (never posts)")
    p.add_argument("run")
    p.add_argument("--decision", required=True, choices=["approved", "sent-back"])
    p.add_argument("--recorded-by", default="Indigo")
    p.set_defaults(fn=cmd_review_decision)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
