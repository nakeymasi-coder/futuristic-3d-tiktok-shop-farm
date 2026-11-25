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
    * Step 6  — Mila's script approval
    * Step 7  — Mila's model photo approval
    * Step 10 — Mila's QC verdict (Mila is QC owner; Glam is final gate)
    * Review  — Glam's final review of the finished video (Approve or Redo)
  Glam, Nov 25: "Don't wait for my approval to make the video." Nothing
  before the video waits on Glam; she rules once, on the finished video.
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
  3 Pick           steps/step3-pick/pick.md, non-empty — the pick is its
                   "product:" line (a run is created empty; the Shop Agent
                   picks here, not at create)
  4 Product Photo  an image file in steps/step4-photo/
  5 Photo Match    steps/step5-match/match-verdict.md with verdict: MATCH,
                   signed by a checker who is NOT the grabber of record
  6 Script         steps/step6-script/script.md non-empty AND passing the
                   Step 6 script check (script_findings: farm-rules.json word cap a line,
                   person-first hook not just the mode name, soft CTA on
                   file, no specs/prices/sold counts/use claims) AND
                   steps/step6-script/mila-script-approval.md (approved_by: Mila)
                   whose script_sha256 matches the script on file — an edit
                   after her approval needs her approval again
  7 Styled Image   an image file in steps/step7-styled/
  8 Package        steps/step8-package/package.md present AND passing lint
                   (references-only, no product words, staging bar)
  9 Build          a video file in steps/step9-builds/
 10 Checks         steps/step10-qc/mila-verdict.md with verdict: PASS,
                   checker: Mila (collected ONCE from the QC handoff folder)
                   covering exactly the current build files (verdict-
                   covers.json) — a new or changed build waits on Mila
 11 Caption & Post FREEZE-LOCKED — never clears, by design
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / "workspace"
RUNS_DIR = WORKSPACE / "farm-runs"
HANDOFF_DIR = WORKSPACE / "farm-qc-handoff"
RUNNER_DIR = WORKSPACE / "farm-runner"
MANIFEST_JSON = RUNNER_DIR / "review-manifest.json"
REVIEW_HTML = RUNNER_DIR / "review-section.html"

# ----------------------------------------------------------------------------
# THE MASTER RULES FILE (Glam, Nov 24: "Yes, that's how it's supposed to be")
# Every rule this runner checks — word limits, clip rule, spec words, person
# words, mode names, use claims, CTAs, staging/handling patterns — lives in
# ONE file: farm-rules.json. The runner keeps NO copy of its own. If the file
# is missing or broken, every command stops (exit 4); there is no silent
# fallback. Lookup order: $FARM_RULES, next to runner.py, its parent folder,
# ~/workspace/farm-rules.json.
# ----------------------------------------------------------------------------

REQUIRED_RULE_KEYS = {
    "numbers": ["max_spoken_words_per_line", "clip_seconds",
                "clips_per_video", "closeup_seconds", "video_seconds_about"],
    "checks": ["spec_words", "spec_exempt_phrases", "person_words",
               "first_person_words", "mode_names", "use_claim_patterns",
               "health_claim_patterns", "health_claim_hashtag_patterns",
               "before_after_patterns", "drawn_product_nouns",
               "spoken_cta_patterns", "banned_spoken_phrases",
               "banned_spoken_patterns", "price_patterns",
               "urgency_patterns", "sold_count_patterns",
               "label_wording_patterns", "product_description_terms",
               "product_description_patterns", "staging_patterns",
               "handling_nouns", "handling_verbs", "guard_patterns"],
    "laws": [], "run_order": [], "mila_scorecard": [], "form": [],
    "version": [], "agents": [], "mila_signing": ["public_key"],
}


def rules_candidates():
    import os
    here = Path(__file__).resolve().parent
    out = []
    if os.environ.get("FARM_RULES"):
        return [Path(os.environ["FARM_RULES"]).expanduser()]
    out.append(here / "farm-rules.json")
    out.append(here.parent / "farm-rules.json")
    out.append(Path.home() / "workspace" / "farm-rules.json")
    return out


def rules_problems(data):
    probs = []
    for top, subs in REQUIRED_RULE_KEYS.items():
        if top not in data:
            probs.append(f"missing '{top}'")
            continue
        for k in subs:
            if k not in data[top]:
                probs.append(f"missing '{top}.{k}'")
    return probs


def load_rules():
    tried = rules_candidates()
    for p in tried:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as e:
                print(f"FARM RULES BROKEN — {p} is not valid JSON ({e}). "
                      "The runner keeps no copy of the rules, so it stops "
                      "here. Fix farm-rules.json, then run check-rules.")
                sys.exit(4)
            probs = rules_problems(data)
            if probs:
                print(f"FARM RULES INCOMPLETE — {p}: " + "; ".join(probs) +
                      ". The runner stops here.")
                sys.exit(4)
            return p, data
    print("FARM RULES NOT FOUND — the runner reads every rule from "
          "farm-rules.json and keeps no copy of its own, so it stops here. "
          "Looked in: " + ", ".join(str(p) for p in tried) +
          ". Put farm-rules.json next to runner.py (or set FARM_RULES).")
    sys.exit(4)


RULES_PATH, RULES = load_rules()
NUM = RULES["numbers"]
CHK = RULES["checks"]
MAX_WORDS = int(NUM["max_spoken_words_per_line"])
CLIP_SECONDS = float(NUM["clip_seconds"])
CLIPS_PER_VIDEO = int(NUM["clips_per_video"])
CLOSEUP_SECONDS = str(NUM["closeup_seconds"])


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
# handling of the product container is a send-back, ALWAYS — no proof waives
# it. SHOW-IT SHOT (Glam + Claude, Nov 24 — the texture rule, gone deeper so
# every category has one): a package may declare exactly ONE show-it shot —
# the product shown doing what it is for. Skincare: a "Texture shot:" line,
# the product on skin only, the bottle stays on the counter. Other
# categories: a "Show-it shot:" line stating the action — fabric moving for
# clothes, shoes on feet walking, a gadget in use. ANY show-it shot needs
# steps/step8-package/staging-proof.md on file first: a test build that
# proved that exact shot holds the product true. The proof clears that one
# shot and nothing else.
# ----------------------------------------------------------------------------





# Generic handling (audit fix #4, Nov 24): the staging bar holds for ANY
# product, not just bottles — a jar, tube, spray, compact or "the product in
# her hand" is handling too. These are NOT applied to the one declared
# Texture shot: / Show-it shot: line (that shot is judged by its own rules).


LABEL_WORDING_PATTERNS = CHK["label_wording_patterns"]
PRODUCT_DESCRIPTION_TERMS = CHK["product_description_terms"]
PRODUCT_DESCRIPTION_PATTERNS = CHK["product_description_patterns"]
STAGING_PATTERNS = CHK["staging_patterns"]
HANDLING_NOUNS = CHK["handling_nouns"]
HANDLING_VERBS = CHK["handling_verbs"]
GENERIC_HANDLING_PATTERNS = [
    r"\b" + HANDLING_VERBS + r"\s+(?:up\s+)?(?:the|her|his|a|an|one|this|that|"
    r"their)\s+(?:\w+\s+){0,2}?" + HANDLING_NOUNS + r"\b",
    r"\b" + HANDLING_NOUNS + r"\s+in\s+(?:her|his|one|both|the|their)\s+hands?\b",
] + list(CHK.get("handling_extra_patterns", []))
GUARD_PATTERNS = CHK["guard_patterns"]

CLIP_HEADER = re.compile(r"(?i)\s*(?:\*\*)?(?:C\d{2}\b|clip\s+\d+\b)")
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_set(folder):
    """{name: sha256} for the video files in a folder."""
    return {v.name: sha256_file(v) for v in files_with_ext(folder, VIDEO_EXTS)}


def image_set_sha(folder):
    """One fingerprint for the image(s) in a folder (Glam's image approval
    covers exactly these files)."""
    h = hashlib.sha256()
    for f in files_with_ext(folder, IMAGE_EXTS):
        h.update(f.name.encode() + b"\0" + sha256_file(f).encode() + b"\n")
    return h.hexdigest()


def pick_from_record(run, cfg):
    """The pick is whatever steps/step3-pick/pick.md names (a 'product:' line,
    else its first non-empty line); the config pick is used only if present
    and the record is missing (audit fix #13 — a run starts empty and the
    Shop Agent picks at Step 3)."""
    rec = run / "steps" / "step3-pick" / "pick.md"
    if rec.exists():
        lines = [l.strip() for l in rec.read_text(
            encoding="utf-8", errors="replace").splitlines() if l.strip()]
        for l in lines:
            m = re.match(r"(?i)\s*(?:product|pick)\s*:\s*(.+)", l)
            if m:
                return m.group(1).strip()
        if lines:
            return lines[0].lstrip("#").strip()
    return (cfg.get("pick") or "").strip()


def nonempty_file(path):
    return path.exists() and path.read_text(
        encoding="utf-8", errors="replace").strip() != ""


# Spec / label words that make a "story sentence" label copy, not a story
# (Glam + Claude, Nov 24 — the smart story check, first version). WIDENED
# Nov 24 (Glam's worry: it only worked for turmeric oil) — the list now
# covers fashion and general categories too: fabric percentages and
# materials, true to size, sizes, stretchy, waterproof, and measures and
# tech specs of every kind. One shared list: the story check and the
# Step 6 script check both read it.
# The sentence must be about a PERSON — one of these has to be in it. The
# list is spelled out on purpose (Claude, Nov 24): the check needs something
# concrete to look for.
# First-person words: a hook built only on these speaks for the model, not
# to the viewer (audit fix #26 — "the hook speaks to the VIEWER's moment").


# Everyday phrases that contain a spec word but are not specs (audit fix #25).


STORY_SPEC_WORDS = tuple(CHK["spec_words"])
STORY_PERSON_WORDS = tuple(CHK["person_words"])
FIRST_PERSON_WORDS = tuple(CHK["first_person_words"])
SPEC_EXEMPT_PHRASES = tuple(CHK["spec_exempt_phrases"])


def spec_text(low):
    for ph in SPEC_EXEMPT_PHRASES:
        low = low.replace(ph, " ")
    return low


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
    low = spec_text(sentence.lower())
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


# Spec words banned from SPOKEN script lines — the same shared, widened
# list the story check reads (beauty measures, fashion specs, general
# tech/home specs), so the bars hold for any product, not just the oil.
SCRIPT_SPEC_WORDS = STORY_SPEC_WORDS
MODE_NAMES = tuple(CHK["mode_names"])
USE_CLAIM_PATTERNS = tuple(CHK["use_claim_patterns"])
SPOKEN_CTA_PATTERNS = tuple(CHK["spoken_cta_patterns"])
BANNED_SPOKEN_PHRASES = tuple(CHK["banned_spoken_phrases"])
BANNED_SPOKEN_PATTERNS = tuple(CHK["banned_spoken_patterns"])
PRICE_PATTERNS = tuple(CHK["price_patterns"])
URGENCY_PATTERNS = tuple(CHK["urgency_patterns"])
SOLD_COUNT_PATTERNS = tuple(CHK["sold_count_patterns"])
# Glam, Nov 25: banned health and beauty claims are LAW in farm-rules.json,
# not something an agent has to remember. Spoken lines, the CTA: line and
# any caption line in the script fail here, before a video is made.
HEALTH_CLAIM_PATTERNS = tuple(CHK["health_claim_patterns"])


HEALTH_HASHTAG_PATTERNS = tuple(CHK["health_claim_hashtag_patterns"])
BEFORE_AFTER_PATTERNS = tuple(CHK["before_after_patterns"])
DRAWN_PRODUCT_NOUNS = tuple(CHK["drawn_product_nouns"])


def hashtag_claim_hit(text):
    """Glam, Nov 25: hashtags never promise results either (#hairgrowth)."""
    for tag in re.findall(r"#(\w+)", text.lower()):
        for pat in HEALTH_HASHTAG_PATTERNS:
            if re.search(pat, tag):
                return "#" + tag
    return None


def before_after_hit(text):
    low = text.lower()
    for pat in BEFORE_AFTER_PATTERNS:
        m = re.search(pat, low)
        if m:
            return m.group(0).strip()
    return None


def drawn_product_hit(text):
    """A clip that puts the product in frame (Glam, Nov 25: the AI never
    draws a product; it shows only as the real listing photo close-up)."""
    low = text.lower()
    if "listing photo" in low:
        return None
    for w in DRAWN_PRODUCT_NOUNS:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            return w
    return None


def health_claim_hit(text):
    """The first banned health/beauty/results claim in text, or None.
    Hashtags are skipped (the caption check holds them to the product)."""
    low = re.sub(r"#\w+", " ", text.lower())
    for pat in HEALTH_CLAIM_PATTERNS:
        m = re.search(pat, low)
        if m:
            return m.group(0).strip()
    return None
# Mode names (the Mode Barn) — a first line that is ONLY the mode name is a
# label, not a hook (Claude, Nov 24).
# Use claims the AI model can never make (the hook speaks to the VIEWER's
# moment, never "I used it" — Claude's line, Nov 24).


# Any spoken call to buy (audit fix #5): allowed once, in the closing line.


def spoken_lines(script_path):
    """The script's spoken lines: the quoted text on LINE rows of script.md."""
    out = []
    if not script_path.exists():
        return out
    for raw in script_path.read_text(
            encoding="utf-8", errors="replace").splitlines():
        head = raw.strip().lstrip("*-# ").lower()
        if not (head.startswith("line") or head.startswith("hook")
                or head.startswith("clip") or re.match(r"c\d{2}\b", head)):
            continue
        m = re.search(r'"([^"]+)"', raw) or re.search(r"“([^”]+)”", raw)
        if m:
            out.append(m.group(1).strip())
    return out


def script_findings(run):
    """The Step 6 SCRIPT CHECK (Glam + Claude, Nov 24): the mechanical bars
    a script must pass BEFORE Glam's approval gate, so she is not the first
    filter. Returns a list of (category, message); empty = passing.
    Bars (all read from farm-rules.json): every spoken line within the word cap; one short spoken CTA allowed in
    the final line only (like 'tap the orange cart') — 'tap the link'
    never; no spec/measure
    words or numbers in spoken lines; no price and no sold counts; no
    'I used it' use claims (the model is AI); the first spoken line is a
    person-first HOOK, not just the mode name; and the soft CTA up top is
    on file (a 'CTA:' line pointing below — on screen + the caption's
    first line)."""
    findings = []
    script = run / "steps" / STEP_DIRS[6] / "script.md"
    lines = spoken_lines(script)
    if not lines:
        return [("no-spoken-lines", "script.md carries no LINE rows with "
                 "quoted spoken lines — there is nothing the script check "
                 "can read")]
    cta_lines = []
    for i, line in enumerate(lines, 1):
        low = line.lower()
        n_words = len(line.split())
        if n_words > MAX_WORDS:
            findings.append(("line-length", f"LINE {i} is {n_words} spoken "
                             f"words (bar: {MAX_WORDS} max)"))
        if (any(re.search(p, low) for p in BANNED_SPOKEN_PATTERNS)
                or any(ph in low for ph in BANNED_SPOKEN_PHRASES)):
            findings.append(("tap-the-link", f"LINE {i} says 'tap/click the "
                             "link' — that phrase is banned; the one "
                             "allowed spoken CTA sits in the final line, "
                             "like 'tap the orange cart'"))
        elif any(re.search(p, low) for p in SPOKEN_CTA_PATTERNS):
            cta_lines.append(i)
            if i != len(lines):
                findings.append(("cta-position", f"LINE {i} carries a spoken "
                                 "call to buy — only the final line may "
                                 "carry one, one short CTA at the end"))
        if any(ch.isdigit() for ch in line):
            findings.append(("spec", f"LINE {i} contains a number — spoken "
                             "lines carry no specs"))
        slow = spec_text(low)
        for w in SCRIPT_SPEC_WORDS:
            hit = (re.search(r"\b" + re.escape(w) + r"\b", slow)
                   if w.replace("-", "").isalpha() else w in slow)
            if hit:
                findings.append(("spec", f"LINE {i} contains the spec word "
                                 f"'{w}' — label copy is not spoken"))
                break
        if any(re.search(p, low) for p in PRICE_PATTERNS):
            findings.append(("price", f"LINE {i} carries a price — no "
                             "prices in spoken lines"))
        if any(re.search(p, low) for p in URGENCY_PATTERNS):
            findings.append(("urgency", f"LINE {i} makes an urgency/sold-out "
                             "claim — the GG shield bans invented urgency "
                             "claims"))
        elif any(re.search(p, low) for p in SOLD_COUNT_PATTERNS):
            findings.append(("sold-count", f"LINE {i} carries a sold "
                             "count — never in a script"))
        ba = before_after_hit(line)
        if ba:
            findings.append(("before-after", f"LINE {i} sets up a "
                             f"before-and-after ('{ba}') — never, for any "
                             "product"))
        hit = health_claim_hit(line)
        if hit:
            findings.append(("health-claim", f"LINE {i} makes a banned "
                             f"health/beauty claim ('{hit}') — never "
                             "spoken, even if the listing says it"))
        claimed = False
        for pat in USE_CLAIM_PATTERNS:
            if re.search(pat, low):
                findings.append(("use-claim", f"LINE {i} makes an 'I used "
                                 "it' claim — the model is AI and never "
                                 "used it"))
                claimed = True
                break
        if not claimed and any(re.search(p, low) for p in
                               CHK.get("first_person_use_claim_patterns", [])):
            # "all week / all month" is a use claim only in the model's own
            # mouth (first person) — in the viewer's moment ("your feet
            # hurt all week") it is a hook, and it passes.
            toks = set(re.findall(r"[a-z']+", low))
            if toks.intersection(FIRST_PERSON_WORDS):
                findings.append(("use-claim", f"LINE {i} makes an 'I used "
                                 "it' claim ('all week/month' in the "
                                 "model's own voice) — the model is AI and "
                                 "never used it"))
    first_low = re.sub(r"\s+", " ", re.sub(
        r"[^a-z' ]", " ", lines[0].lower())).strip()
    for mode in MODE_NAMES:
        if first_low == mode or first_low.startswith(mode + " "):
            findings.append(("mode-name-hook", "LINE 1 opens with the mode "
                             f"name ('{mode}') — the hook leads with a "
                             "label, not the viewer's moment (Claude, "
                             "Nov 24: opening with it fails, even with "
                             "more words after it)"))
            break
    tokens = set(re.findall(r"[a-z']+", lines[0].lower()))
    persons = tokens.intersection(STORY_PERSON_WORDS)
    if not persons:
        findings.append(("hook", "LINE 1 names no person (you, her, my, "
                         "she...) — the hook is person-first or it fails"))
    elif persons.issubset(FIRST_PERSON_WORDS):
        findings.append(("hook", "LINE 1 speaks only in the model's own "
                         "voice (I/my/me) — the hook speaks to the VIEWER's "
                         "moment (you, your, her, a mom...)"))
    text = (script.read_text(encoding="utf-8", errors="replace")
            if script.exists() else "")
    # STAGING in the script's own directions (Nov 24, Indigo's first script:
    # "she holds the bottle, a drop on her hand"). The staging bar is already
    # law — product stationary, no hands on it, one declared show-it shot only
    # — so the script check reads every line OUTSIDE the quoted spoken words.
    for no, raw in enumerate(text.splitlines(), 1):
        direction = re.sub(r'"[^"]*"|“[^”]*”', " ", raw).lower()
        if not direction.strip():
            continue
        if any(re.search(p, direction) for p in
               list(STAGING_PATTERNS) + GENERIC_HANDLING_PATTERNS):
            findings.append(("drawn-product", f"script line {no} puts the "
                             "product itself in a shot (held, poured or "
                             "handled) — the AI never draws a product; she "
                             "can use it with the product off frame, and "
                             "the product shows only as the real listing "
                             "photo close-up"))
        ba = before_after_hit(direction)
        if ba:
            findings.append(("before-after", f"script line {no} sets up a "
                             f"before-and-after ('{ba}') — never, for any "
                             "product"))
    soft = CHK.get("soft_cta_line", {"starts_with": "cta:",
                                     "must_mention": "below"})
    cta_ok = any(l.strip().lower().startswith(soft["starts_with"])
                 and soft["must_mention"] in l.lower()
                 for l in text.splitlines())
    for no, raw in enumerate(text.splitlines(), 1):
        head = raw.strip().lstrip("*-# ").lower()
        if head.startswith("cta:") or head.startswith("caption"):
            hit = (health_claim_hit(raw.split(":", 1)[-1])
                   or hashtag_claim_hit(raw))
            if hit:
                findings.append(("health-claim", f"script line {no} (CTA/"
                                 f"caption) makes a banned health/beauty "
                                 f"claim ('{hit}') — never on screen or "
                                 "in the caption, even if the listing "
                                 "says it"))
    if not cta_ok:
        findings.append(("no-cta", "no soft CTA up top on file — script.md "
                         "needs a 'CTA:' line pointing below (on screen + "
                         "the caption's first line)"))
    return findings


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
        is_shot = bool(CLIP_HEADER.match(raw)) or bool(re.match(
            r"(?i)\s*[*#-]*\s*(texture|show-it|use)\s+shot\s*:", raw))
        staged = False
        for pat in list(STAGING_PATTERNS) + GENERIC_HANDLING_PATTERNS:
            if re.search(pat, low):
                findings.append(("DRAWN PRODUCT", i, line))
                staged = True
                break
        if not staged and is_shot and "close-up" not in low \
                and "close up" not in low:
            w = drawn_product_hit(line)
            if w:
                findings.append(("DRAWN PRODUCT", i, f"the clip puts the "
                                 f"product in frame ('{w}') — the AI never "
                                 "draws a product; it shows only as the "
                                 "real listing photo close-up"))
        ba = before_after_hit(line)
        if ba:
            findings.append(("BEFORE-AFTER", i, f"'{ba}' — no "
                             "before-and-after, for any product"))
        # CLIP RULE (Glam + Claude, Nov 24 — audit fix #28): every clip is
        # (numbers from farm-rules.json) N seconds flat, max N spoken words in a clip, N clips make the
        # video; the 1-2 second clean close-up of the listing photo is kept.
        for q in re.findall(r'"([^"]+)"|“([^”]+)”', line):
            qt = (q[0] or q[1]).strip()
            if len(qt.split()) > MAX_WORDS:
                findings.append(("CLIP RULE", i, f"{len(qt.split())} spoken "
                                 f"words in one clip — max {MAX_WORDS} spoken "
                                 "words in a clip"))
                break
        is_clip = bool(CLIP_HEADER.match(raw))
        if is_clip and "close-up" not in low and "close up" not in low:
            for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:-|–|to)?\s*"
                                 r"(?:s|sec|secs|second|seconds)\b", low):
                if float(m.group(1)) != CLIP_SECONDS:
                    findings.append(("CLIP RULE", i, f"clip length "
                                     f"{m.group(1)} seconds — every clip is "
                                     f"{CLIP_SECONDS:g} seconds flat"))
                    break

    clip_headers = [raw for raw in lines if CLIP_HEADER.match(raw)
                    and "close-up" not in raw.lower()
                    and "close up" not in raw.lower()]
    if len(clip_headers) > CLIPS_PER_VIDEO:
        findings.append(("CLIP RULE", 0, f"{len(clip_headers)} clips declared "
                         f"— {CLIPS_PER_VIDEO} clips make the video (plus the "
                         f"{CLOSEUP_SECONDS} second close-up)"))

    # USE SHOTS (Glam, Nov 25): allowed for every product, no proof build —
    # the product itself stays off frame (checked above as DRAWN PRODUCT).

    # CAPTION (farm laws: caption keywords, 3-5 hashtags, soft CTA up top in
    # the caption's first line) — the caption is a Step 8 deliverable.
    findings.extend(caption_findings(run, lines))

    if not REFERENCES_LINE.search(text):
        findings.append(("REFERENCES", 0,
                         "no 'References:' line — package must declare its references"))
    elif not LISTING_PHOTO_MENTION.search(text):
        findings.append(("REFERENCES", 0,
                         "references do not name the listing photo — the build's "
                         "references are the approved styled image AND the real "
                         "listing photo"))
    return findings


def caption_findings(run, lines):
    """Read the package's Caption: block and hold it to the farm laws."""
    out = []
    start = None
    for i, raw in enumerate(lines):
        if re.match(r"(?i)\s*[*#-]*\s*caption\s*:", raw):
            start = i
            break
    if start is None:
        return [("CAPTION", 0, "no 'Caption:' in the package — the caption "
                 "(product keyword first line, soft CTA, hashtags) is part "
                 "of the Next package")]
    block = [lines[start].split(":", 1)[1].strip()]
    for raw in lines[start + 1:]:
        if not raw.strip() or re.match(r"\s*[*#-]*\s*[A-Za-z][\w -]{0,30}:\s", raw):
            break
        block.append(raw.strip())
    block = [b for b in block if b]
    if not block:
        return [("CAPTION", start + 1, "the Caption: block is empty")]
    first = block[0].lower()
    cfg = {}
    try:
        cfg = load_config(run)
    except SystemExit:
        pass
    pick = (pick_from_record(run, cfg) or "").lower()
    words = [w for w in re.findall(r"[a-z]{4,}", pick)]
    if words and not any(w in first for w in words):
        out.append(("CAPTION", start + 1, "the caption's first line doesn't "
                    "name the product in words buyers search — caption "
                    "keywords are a farm law"))
    cta_words = CHK.get("caption_cta_words", ["below", "linked"])
    if not any(w in first for w in cta_words):
        out.append(("CAPTION", start + 1, "the caption's first line has no "
                    "soft CTA pointing below (on screen, linked below, "
                    "caption's first line)"))
    tags = re.findall(r"#\w+", " ".join(block).lower())
    lo, hi = int(NUM.get("hashtags_min", 3)), int(NUM.get("hashtags_max", 5))
    if not (lo <= len(tags) <= hi):
        out.append(("CAPTION", start + 1, f"{len(tags)} hashtags — every "
                    f"caption carries {lo} to {hi} tied to the product"))
    for k, b in enumerate(block):
        hit = health_claim_hit(b) or hashtag_claim_hit(b)
        if hit:
            out.append(("CAPTION", start + 1 + k, f"the caption makes a "
                        f"banned health/beauty claim ('{hit}') — never in "
                        "the caption, even if the listing says it"))
    generic = set(t.lower() for t in CHK.get("generic_hashtags", []))
    bad = [t for t in tags if t in generic]
    if bad:
        out.append(("CAPTION", start + 1, "generic hashtags " + ", ".join(bad)
                    + " — never generic tags"))
    return out


def blocking_findings(findings):
    """Every lint finding blocks Step 8. (Nov 24 narrowing: a staging proof
    no longer waives handling findings — it only validates the one declared
    texture shot, which produces no finding when it is in order.)"""
    return list(findings)


# ----------------------------------------------------------------------------
# Evidence derivation — the ONLY source of status
# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Glam, Nov 25 — enforcement so the rules can't be skipped
# ----------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed25519 as _ed  # noqa: E402

# Glam, Nov 25: Mila's private key lives ONLY in Mila's own session (its own
# home folder), never in the shared project files, so no other agent or
# session can sign as her. The runner refuses to sign from a shared folder.
MILA_KEY_DEFAULT = Path.home() / ".mila" / "mila-signing-key"
SHARED_ROOTS = ("/mnt/project-files", "/mnt/attach/project-files")
SIGNED_FIELDS = ("kind", "run", "step", "verdict", "covers", "notes",
                 "session", "signed_at")


def test_mode():
    return os.environ.get("FARM_TEST_MODE") == "1"


def mila_key_path():
    return Path(os.environ.get("MILA_SIGNING_KEY") or MILA_KEY_DEFAULT)


def mila_public_key():
    if test_mode() and os.environ.get("FARM_TEST_MILA_PUBKEY"):
        return os.environ["FARM_TEST_MILA_PUBKEY"]
    return (RULES.get("mila_signing", {}) or {}).get("public_key", "")


def key_in_shared_folder(p):
    try:
        rp = str(Path(p).expanduser().resolve())
    except OSError:
        rp = str(p)
    return any(rp.startswith(r) for r in SHARED_ROOTS)


# ---- Each agent is its own session (Glam, Nov 25: "No session plays another
# agent's role"). Every hand-in names the session that did it; one session
# acts as one role per run; the ledger is the proof per step.
SESSION_RE = re.compile(r"^session_[A-Za-z0-9]{8,}$")
# Glam, Nov 25: "This is Muse job." Muse (Indigo) runs the agent steps as
# separate scheduled jobs; each hands in with its own Muse job id, written
# muse_<job id>. Mila's gates still need her signed verdict (Claude session +
# the Mila sign workflow); Muse never gets her key.
MUSE_JOB_RE = re.compile(r"^muse_[A-Za-z0-9][A-Za-z0-9_-]{3,79}$")


def id_kind(sid):
    if SESSION_RE.match(sid):
        return "Claude session"
    if MUSE_JOB_RE.match(sid):
        return "Muse job"
    return ""


def ledger_path(run):
    return run / "sessions.jsonl"


def read_ledger(run):
    p = ledger_path(run)
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def session_guard(run, role, step, args, what):
    """Return the session id, or None (and print REFUSED) when the hand-in
    doesn't name a real session, or the session already played another
    role on this run."""
    sid = (getattr(args, "session", None) or os.environ.get("FARM_SESSION_ID")
           or "").strip()
    if not sid and test_mode():
        sid = "session_TESTMODE" + re.sub(r"[^A-Za-z0-9]", "", role)[:20]
    is_mila = role.strip().lower() == "mila"
    if is_mila and not SESSION_RE.match(sid):
        print(f"{what} REFUSED — Mila's verdicts carry her own Claude session "
              "id (session_...) and come only through the Mila sign workflow.")
        return None
    if not id_kind(sid):
        print(f"{what} REFUSED — every hand-in names the agent's own id with "
              "--session: muse_<your Muse job id> for a Muse job, or a Claude "
              "session id (session_...). Each farm agent runs as its own job.")
        return None
    norm = role.strip().lower()
    for rec in read_ledger(run):
        if rec.get("session") == sid and rec.get("role", "").lower() != norm:
            print(f"{what} REFUSED — {sid} already acted as "
                  f"{rec.get('role')} on this run. One session, one role: "
                  f"{role} must be its own session.")
            return None
    with ledger_path(run).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": now_stamp(), "step": step, "role": role,
                             "session": sid, "what": what}) + "\n")
    clear_blocked_report(run, step, f"{role} handed in")
    return sid


# ---- An agent that can't do its step says so on the board at once (Glam,
# Nov 25: "the scout hit the security wall and never told me").
def blocked_report_path(run, step):
    d = STEP_DIRS.get(step)
    return (run / "steps" / d / "BLOCKED.md") if d else None


def blocked_report(run, step):
    p = blocked_report_path(run, step) if step else None
    if p and p.is_file():
        kv = parse_kv(p)
        if kv.get("reason"):
            return kv
    return None


def clear_blocked_report(run, step, why):
    p = blocked_report_path(run, step)
    if p and p.is_file():
        kv = parse_kv(p)
        p.unlink()
        sheet_log(run, f"BLOCKED report on Step {step} cleared ({why}) — "
                       f"was: {kv.get('by', '?')}: {kv.get('reason', '')}")


def covers_for(paths):
    return ",".join(sorted(sha256_file(Path(p)) for p in paths))


def _signed_message(kv):
    return "\n".join(f"{k}: {kv.get(k, '')}" for k in SIGNED_FIELDS).encode()


def mila_sign_text(run_id, step, verdict, paths, notes="", session=""):
    """Mila's signed verdict (only where her private key lives)."""
    seed = bytes.fromhex(mila_key_path().read_text().strip())
    kv = {"kind": "mila-verdict", "run": run_id, "step": str(step),
          "verdict": verdict.upper(), "covers": covers_for(paths),
          "notes": " ".join(str(notes).split()), "session": session,
          "signed_at": now_stamp()}
    sig = _ed.sign(seed, _signed_message(kv)).hex()
    return "".join(f"{k}: {kv[k]}\n" for k in SIGNED_FIELDS) + \
        "checker: Mila\n" + f"signature: {sig}\n"


def mila_verify(path, run_id, step, paths):
    """(ok, why, kv): a verdict counts only if Mila's key signed it, for this
    run and step, covering exactly these files."""
    kv = parse_kv(Path(path))
    if not kv:
        return False, "no verdict file", kv
    pub = mila_public_key()
    if not pub:
        return False, ("Mila's key isn't registered yet (farm-rules.json "
                       "mila_signing.public_key is empty) — Glam registers "
                       "the key the Mila sign workflow shows in show-key "
                       "mode"), kv
    try:
        ok = _ed.verify(bytes.fromhex(pub), _signed_message(kv),
                        bytes.fromhex(kv.get("signature", "")))
    except ValueError:
        ok = False
    if not ok:
        return False, ("it is not Mila's signed verdict (no valid "
                       "signature) — a typed 'checker: Mila' never "
                       "counts"), kv
    if kv.get("run") != run_id or kv.get("step") != str(step):
        return False, (f"Mila's signature is for {kv.get('run')} Step "
                       f"{kv.get('step')}, not this run and step"), kv
    if kv.get("covers") != covers_for(paths):
        return False, ("Mila's signed verdict covers different files — "
                       "she must check the exact files on file now"), kv
    return True, "signed by Mila", kv


def mp4_seconds(path):
    """Read a .mp4/.mov length from its mvhd box (no ffprobe needed)."""
    import struct
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None

    def boxes(buf, start, end):
        i = start
        while i + 8 <= end:
            size, typ = struct.unpack(">I4s", buf[i:i + 8])
            hdr = 8
            if size == 1:
                size = struct.unpack(">Q", buf[i + 8:i + 16])[0]
                hdr = 16
            elif size == 0:
                size = end - i
            if size < hdr:
                return
            yield typ, i + hdr, i + size
            i += size
    for typ, a, b in boxes(data, 0, len(data)):
        if typ == b"moov":
            for t2, a2, b2 in boxes(data, a, b):
                if t2 == b"mvhd":
                    ver = data[a2]
                    if ver == 1:
                        ts, dur = struct.unpack(">IQ", data[a2 + 20:a2 + 32])
                    else:
                        ts, dur = struct.unpack(">II", data[a2 + 12:a2 + 20])
                    return dur / ts if ts else None
    return None


def build_length_problem(path):
    """Glam, Nov 25: clip length is measured before Mila ever sees it."""
    secs = mp4_seconds(path)
    name = Path(path).name
    if secs is None:
        return (f"{name}: can't read its length — submit the build as an "
                ".mp4 straight from Video Express")
    clip = CLIP_SECONDS
    full_lo = CLIPS_PER_VIDEO * clip
    full_hi = full_lo + 3.0
    if abs(secs - clip) <= 0.6 or full_lo - 0.5 <= secs <= full_hi:
        return None
    return (f"{name} runs {secs:.1f} seconds — every clip is {clip:g} "
            f"seconds flat and the finished video is {CLIPS_PER_VIDEO} clips "
            f"plus the {CLOSEUP_SECONDS} second close-up "
            f"(about {full_lo + 1.5:g} seconds)")


LIVE_RULES_URLS = (
    "https://raw.githubusercontent.com/nakeymasi-coder/"
    "futuristic-3d-tiktok-shop-farm/main/farm-rules.json",
    "https://nakeymasi-coder.github.io/futuristic-3d-tiktok-shop-farm/"
    "farm-rules.json",
)


def live_rules_problem():
    """Glam, Nov 25: a run never starts or moves on an old copy of the rules.
    Returns None when this copy matches the live farm, else the reason."""
    env = os.environ.get("FARM_LIVE_RULES_URL")
    urls = [env] if env else list(LIVE_RULES_URLS)
    reached = False
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                live = json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001 — any failure means "not reached"
            continue
        reached = True
        if live == RULES:
            return None
        return (f"this copy of farm-rules.json is version "
                f"{RULES.get('version')} but the live farm is version "
                f"{live.get('version')} (or the two copies differ). Reload "
                "farm-rules.json and runner.py from the live farm first")
    if not reached:
        return ("BLOCKED: can't reach the live farm rules to prove this copy "
                "is current — stop and report it; no run moves on an "
                "unchecked copy")
    return None


def refuse_if_old_rules(what):
    why = live_rules_problem()
    if why:
        print(f"{what} REFUSED — {why}.")
        return True
    return False


STATUS_BRANCH = "farm-status"
SYNC_MARK = ".farm-sync"          # per-run note of the shared copy it last matched
BIG_FILE = 95 * 1024 * 1024      # GitHub refuses files over 100 MB


class _FarmGit:
    """Git plumbing for the shared farm-status branch (Glam, Nov 25: a run
    started from the farm page lives on GitHub where every agent and the
    Live Run Board can see it). Never touches the clone's own branch,
    index or files."""

    def __init__(self):
        import subprocess
        import tempfile
        self.sp = subprocess
        self.repo = Path(__file__).resolve().parent.parent
        self.ok = (self.repo / ".git").exists()
        self.tmp = Path(tempfile.mkdtemp(prefix="farmgit-"))
        self.env = dict(os.environ,
                        GIT_AUTHOR_NAME="Farm runner",
                        GIT_AUTHOR_EMAIL="farm-runner@users.noreply.github.com",
                        GIT_COMMITTER_NAME="Farm runner",
                        GIT_COMMITTER_EMAIL="farm-runner@users.noreply.github.com",
                        GIT_INDEX_FILE=str(self.tmp / "index"))
        self.head = ""

    def git(self, *a, inp=None, text=True):
        r = self.sp.run(["git", "-C", str(self.repo), *a], input=inp,
                        capture_output=True, text=text, env=self.env, timeout=120)
        if r.returncode != 0:
            err = r.stderr if text else r.stderr.decode("utf-8", "replace")
            raise RuntimeError(f"git {a[0]}: {(err or '').strip()[:300]}")
        return r.stdout.strip() if text else r.stdout

    def fetch(self):
        """Fetch the shared branch. '' when it doesn't exist yet."""
        try:
            self.git("fetch", "-q", "origin",
                     f"+refs/heads/{STATUS_BRANCH}:refs/farm/{STATUS_BRANCH}")
        except RuntimeError as e:
            if "couldn't find remote ref" in str(e).lower():
                self.head = ""
                return ""
            raise
        self.head = self.git("rev-parse", f"refs/farm/{STATUS_BRANCH}")
        return self.head

    def remote_runs(self):
        if not self.head:
            return {}
        try:
            out = self.git("ls-tree", f"{self.head}:runs")
        except RuntimeError:
            return {}
        res = {}
        for line in out.splitlines():
            meta, name = line.split("\t", 1)
            if meta.split()[1] == "tree":
                res[name] = meta.split()[2]
        return res

    def run_files(self, run):
        files = []
        for f in sorted(run.rglob("*")):
            if f.is_file() and f.name != SYNC_MARK and not f.name.endswith(".tmp"):
                files.append(f)
        return files

    def local_tree(self, run, write=True):
        """Tree hash of a local run folder (what it would be on the branch).
        Files over 95 MB are left out and named."""
        idx = self.tmp / ("idx-" + run.name)
        env = dict(self.env, GIT_INDEX_FILE=str(idx))
        if idx.exists():
            idx.unlink()
        skipped = []
        lines = []
        for f in self.run_files(run):
            if f.stat().st_size > BIG_FILE:
                skipped.append(f.relative_to(run).as_posix())
                continue
            args = ["hash-object"] + (["-w"] if write else []) + [str(f)]
            blob = self.sp.run(["git", "-C", str(self.repo), *args],
                               capture_output=True, text=True, env=env,
                               timeout=120).stdout.strip()
            lines.append(f"100644 {blob}\t{f.relative_to(run).as_posix()}")
        r = self.sp.run(["git", "-C", str(self.repo), "update-index",
                         "--add", "--index-info"],
                        input="\n".join(lines) + ("\n" if lines else ""),
                        capture_output=True, text=True, env=env, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"git update-index: {r.stderr.strip()[:300]}")
        tree = self.sp.run(["git", "-C", str(self.repo), "write-tree",
                            "--missing-ok"],
                           capture_output=True, text=True, env=env,
                           timeout=120).stdout.strip()
        return tree, skipped


def _sync_mark(run):
    f = run / SYNC_MARK
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""


def sync_runs():
    """Before every command: bring down runs other agents (or Start Run on
    the farm page) put on the shared branch. A run changed here AND there
    since the last sync is a CONFLICT and is never overwritten — it's said
    out loud. Off when FARM_NO_PUBLISH is set (tests, offline work)."""
    import shutil
    import tarfile
    import io
    if os.environ.get("FARM_NO_PUBLISH"):
        return
    fg = _FarmGit()
    if not fg.ok:
        return
    try:
        if not fg.fetch():
            return
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        for name, rtree in fg.remote_runs().items():
            local = RUNS_DIR / name
            if local.exists():
                ltree, _ = fg.local_tree(local, write=False)
                base = _sync_mark(local)
                if ltree == rtree:
                    (local / SYNC_MARK).write_text(rtree + "\n", encoding="utf-8")
                    continue
                if base and ltree != base and rtree != base:
                    print(f"RUN CONFLICT — {name} changed here and on the shared "
                          "farm since the last sync. Nothing was overwritten. "
                          "Report it to Claude before going on.")
                    continue
                if ltree != base and base:
                    continue  # only changed here: it goes up on the next publish
                if not base and ltree != rtree:
                    print(f"RUN CONFLICT — {name} exists here and on the shared "
                          "farm with different files. Nothing was overwritten. "
                          "Report it to Claude before going on.")
                    continue
            data = fg.git("archive", "--format=tar", f"{fg.head}:runs/{name}",
                          text=False)
            tmpd = RUNS_DIR / (name + ".sync-tmp")
            if tmpd.exists():
                shutil.rmtree(tmpd)
            tmpd.mkdir()
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                for m in tf.getmembers():
                    if m.name.startswith("/") or ".." in Path(m.name).parts:
                        raise RuntimeError(f"unsafe path in shared run {name}")
                tf.extractall(tmpd, filter="data")
            # git keeps no empty folders: put every step folder back.
            for d in STEP_DIRS.values():
                (tmpd / "steps" / d).mkdir(parents=True, exist_ok=True)
            (tmpd / SYNC_MARK).write_text(rtree + "\n", encoding="utf-8")
            if local.exists():
                shutil.rmtree(local)
            tmpd.rename(local)
    except Exception as e:  # noqa: BLE001
        print(f"SHARED RUNS NOT SYNCED — {e}. You may be working on an old "
              "copy of the run. Report it.")


def publish_status(out):
    """Publish farm-status.json, farm-jobs.json and every run folder to the
    farm repo's 'farm-status' branch after every step, so the Live Run Board
    on the live farm page — and every agent — sees the same runs.
    Glam, Nov 25: never fail silently — every outcome is printed."""
    if os.environ.get("FARM_NO_PUBLISH"):
        return
    fg = _FarmGit()
    if not fg.ok:
        print("STATUS NOT PUBLISHED — this runner is not inside a clone of the "
              "farm repo, so the Live Run Board can't see this run. Run the "
              "farm from a clone of nakeymasi-coder/futuristic-3d-tiktok-shop-"
              "farm. Report it.")
        return
    try:
        parent = fg.fetch()
        remote = fg.remote_runs()
        if parent:
            fg.git("read-tree", parent)
        else:
            fg.git("read-tree", "--empty")
        published = {}
        problems = []
        if RUNS_DIR.is_dir():
            for run in sorted(d for d in RUNS_DIR.iterdir()
                              if d.is_dir() and (d / "config.json").exists()):
                ltree, skipped = fg.local_tree(run)
                base = _sync_mark(run)
                rtree = remote.get(run.name)
                if rtree and rtree != ltree and rtree != base:
                    problems.append(f"{run.name} changed on the shared farm "
                                    "since this copy synced — not overwritten")
                    continue
                for sk in skipped:
                    problems.append(f"{run.name}/{sk} is over 95 MB and stays "
                                    "only on this computer")
                if rtree:
                    fg.git("rm", "-r", "-q", "--cached", f"runs/{run.name}")
                fg.git("read-tree", f"--prefix=runs/{run.name}/", ltree)
                published[run] = ltree
        for name in ("farm-status.json", "farm-jobs.json"):
            f = out if name == "farm-status.json" else out.parent / name
            if f.exists():
                blob = fg.git("hash-object", "-w", str(f))
                fg.git("update-index", "--add", "--cacheinfo",
                       f"100644,{blob},{name}")
        tree = fg.git("write-tree")
        if parent and tree == fg.git("rev-parse", f"{parent}^{{tree}}"):
            print("Status published to the Live Run Board (nothing new).")
        else:
            args = ["commit-tree", tree, "-m", f"Farm status {now_stamp()}"]
            if parent:
                args += ["-p", parent]
            commit = fg.git(*args)
            try:
                fg.git("push", "-q", "origin",
                       f"{commit}:refs/heads/{STATUS_BRANCH}")
            except RuntimeError as e:
                if "non-fast-forward" in str(e) or "rejected" in str(e):
                    raise RuntimeError("another agent published at the same "
                                       "moment — run the same command again")
                raise
            print("Status published to the Live Run Board.")
        for run, t in published.items():
            (run / SYNC_MARK).write_text(t + "\n", encoding="utf-8")
        for pr in problems:
            print(f"STATUS NOTE — {pr}. Report it.")
    except Exception as e:  # noqa: BLE001
        print(f"STATUS NOT PUBLISHED — {e}. The Live Run Board won't show "
              "this step. Report it.")


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
        if nonempty_file(steps / STEP_DIRS[3] / "pick.md"):
            return ("CLEARED", f"pick recorded: {pick_from_record(run, cfg)}")
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
        script = steps / STEP_DIRS[6] / "script.md"
        if not nonempty_file(script):
            return ("WAITING", "no script on file (steps/step6-script/script.md)")
        bad = script_findings(run)
        if bad:
            cats = ", ".join(sorted({f[0] for f in bad}))
            return ("INVALID", f"script FAILS the Step 6 script check "
                               f"({cats}) — {bad[0][1]}; fix the script — "
                               "Glam is not the first filter")
        back = parse_kv(steps / STEP_DIRS[6] / "mila-script-sendback.md")
        if back.get("script_sha256") == sha256_file(script):
            return ("INVALID", "Mila sent the script back: "
                               f"{back.get('notes', '(no notes)')}")
        apath = steps / STEP_DIRS[6] / "mila-script-approval.md"
        if apath.exists():
            ok, why, kv = mila_verify(apath, run.name, 6, [script])
            if ok and kv.get("verdict") == "APPROVE":
                return ("CLEARED", "script on file, passing the script check, "
                                   "and Mila's signed approval on file")
            if "different files" in why:
                return ("WAITING", "script changed after Mila's approval — "
                                   "needs her approval again (her approval "
                                   "covers the exact script she saw)")
            return ("WAITING", f"an approval is on file but {why} — waiting "
                               "on Mila's signed script approval")
        return ("WAITING", "script on file and passing the script check — "
                           "waiting on Mila's script approval")
    if n == 7:
        imgs = files_with_ext(steps / STEP_DIRS[7], IMAGE_EXTS)
        if not imgs:
            return ("WAITING", "no model photo on file (steps/step7-styled/) — "
                               "the Casting / Image Agent submits Glam's "
                               "uploaded model photo")
        back = parse_kv(steps / STEP_DIRS[7] / "mila-image-sendback.md")
        if back.get("image_sha256") == image_set_sha(steps / STEP_DIRS[7]):
            return ("INVALID", "Mila sent the model photo back: "
                               f"{back.get('notes', '(no notes)')}")
        apath = steps / STEP_DIRS[7] / "mila-image-approval.md"
        if not apath.exists():
            return ("WAITING", f"model photo on file ({imgs[0].name}) — "
                               "waiting on Mila's model photo approval")
        ok, why, kv = mila_verify(apath, run.name, 7, imgs)
        if not ok and "different files" in why:
            return ("WAITING", "model photo changed after Mila's approval — "
                               "needs her approval again (her approval covers "
                               "the exact photo she saw)")
        if not ok or kv.get("verdict") != "APPROVE":
            return ("WAITING", f"an approval is on file but {why} — waiting "
                               "on Mila's signed model photo approval")
        return ("CLEARED", f"model photo on file ({imgs[0].name}) and Mila's "
                           "approval recorded")
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
                           "(references-only, no drawn product)")
    if n == 9:
        vids = files_with_ext(steps / STEP_DIRS[9], VIDEO_EXTS)
        if vids:
            probs = [p for p in (build_length_problem(v) for v in vids) if p]
            if probs:
                return ("INVALID", "clip length check FAILS before Mila — "
                                   + "; ".join(probs))
            names = ", ".join(v.name for v in vids)
            return ("CLEARED", f"build file(s) on file and measured: {names}")
        return ("WAITING", "no build files on file (steps/step9-builds/)")
    if n == 10:
        verdict_path = steps / STEP_DIRS[10] / "mila-verdict.md"
        if not verdict_path.exists():
            return ("WAITING", "no QC verdict collected — human gate: Mila's "
                               "check (QC owner) has not ruled on this build")
        kv = parse_kv(verdict_path)
        verdict = kv.get("verdict", "").upper()
        checker = kv.get("checker", "")
        covers_path = steps / STEP_DIRS[10] / "verdict-covers.json"
        try:
            covers = json.loads(covers_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            covers = None
        current = build_set(steps / STEP_DIRS[9])
        if covers is None:
            return ("WAITING", "the verdict on file was collected before "
                               "verdicts were tied to the exact builds — "
                               "Mila's check needs to be collected again for "
                               "these builds")
        if covers != current:
            return ("WAITING", "new build since Mila's verdict — waiting on "
                               "her check (her verdict covers only the exact "
                               "build files she was handed)")
        vids = files_with_ext(steps / STEP_DIRS[9], VIDEO_EXTS)
        ok, why, _ = mila_verify(verdict_path, run.name, 10, vids)
        if verdict == "PASS" and not ok:
            return ("INVALID", f"a PASS is on file but {why}")
        if verdict == "PASS" and checker.strip().lower() == "mila":
            return ("CLEARED", "Mila's signed PASS on file in the run folder")
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
    out.append(f"RUN {cfg['run_id']} — "
               f"{pick_from_record(run, cfg) or '(pick at Step 3)'} · "
               f"{cfg.get('cast_model') or '(model at Step 7)'} · "
               f"{cfg.get('mode') or '(mode open)'} · {cfg.get('account', '')}")
    out.append("Status derived from evidence on disk at "
               f"{now_stamp()} — never set by hand.")
    out.append("")
    for n, name, state, reason in results:
        out.append(f"  Step {n:<2} {name:<28} {state:<8} {reason}")
    out.append("")
    info = open_job_info(run)
    br = blocked_report(run, info.get("step")) \
        if info["kind"] in ("agent", "mila") else None
    if br:
        out.append(f"HEADLINE: BLOCKED at Step {info['step']} — "
                   f"{br.get('by', info['agent'])} reported BLOCKED: "
                   f"{br['reason']} ({br.get('at', '')})")
    else:
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
    if refuse_if_old_rules("START A RUN"):
        return 2
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
    if getattr(args, "request", ""):
        cfg["request"] = args.request
    (run / "config.json").write_text(json.dumps(cfg, indent=2) + "\n",
                                     encoding="utf-8")
    sheet = f"""# RUN SHEET — {run_id}

- Account: {cfg['account']}
- Pick: {cfg['pick'] or '(picked at Step 3 by the Shop Agent — steps/step3-pick/pick.md)'}{(' (ID ' + cfg['pick_id'] + ')') if cfg['pick_id'] else ''}
- Cast model: {cfg['cast_model'] or "(Glam's uploaded model, picked at Step 7)"}
- Mode: {cfg['mode'] or '(open)'}
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
    info = sync_chain(run, actor="Start a Run")
    print(f"Chain: job opened for {info.get('agent') or info.get('to')} "
          f"(Step {info.get('step')}).")
    write_status_file()
    return 0


def cmd_report_blocked(args):
    """An agent that can't do its step reports BLOCKED; the board shows it at
    once. Nothing moves. --clear takes the report down once it's fixed."""
    run = resolve_run(args.run)
    info = open_job_info(run)
    n = args.step
    if args.clear:
        if not blocked_report(run, n):
            print(f"No BLOCKED report on Step {n}.")
            return 0
        clear_blocked_report(run, n, f"cleared by {args.by}")
        write_status_file()
        print(f"BLOCKED report on Step {n} cleared by {args.by}.")
        return 0
    if info["kind"] not in ("agent", "mila") or info["step"] != n:
        now = (f"Step {info['step']} — {info['to']}" if info["step"]
               else "Glam's final review")
        print(f"REPORT REFUSED — Step {n} isn't the open job. The chain is at "
              f"{now}.")
        return 2
    who_ok = (args.by.strip().lower() == "mila") if info["kind"] == "mila" \
        else by_allowed(n, args.by)
    if not who_ok:
        print(f"REPORT REFUSED — Step {n} belongs to {info['agent']}; "
              f"'{args.by}' can't report for it.")
        return 2
    reason = " ".join(str(args.reason or "").split())
    if len(reason) < 5:
        print("REPORT REFUSED — say what blocked you and why (--reason).")
        return 2
    p = blocked_report_path(run, n)
    p.write_text(f"by: {args.by}\nstep: {n}\nreason: {reason}\n"
                 f"session: {args.session or ''}\nat: {now_stamp()}\n",
                 encoding="utf-8")
    sheet_log(run, f"BLOCKED: Step {n} — {args.by}: {reason}")
    write_status_file()
    print(f"BLOCKED reported on the board: {load_config(run)['run_id']} Step "
          f"{n} — {args.by}: {reason}. Nothing moves until it's fixed.")
    return 0


REQUEST_KEYS = {"mode", "product", "account"}


def cmd_start_request(args):
    """Open a run from a request file pushed to farm-requests/ (Glam, Nov 25:
    a push from Muse starts the run; no button press needed)."""
    src = Path(args.file)
    try:
        req = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"START REFUSED — {src} is not a readable JSON request: {e}")
        return 2
    if not isinstance(req, dict):
        print(f"START REFUSED — {src} must hold one JSON object.")
        return 2
    extra = set(req) - REQUEST_KEYS
    if extra:
        print(f"START REFUSED — {src} has unknown field(s): "
              f"{', '.join(sorted(extra))}. Allowed: mode, product, account.")
        return 2
    vals = {}
    for k in REQUEST_KEYS:
        v = req.get(k, "")
        if not isinstance(v, str) or len(v) > 300 or "\n" in v:
            print(f"START REFUSED — '{k}' must be one line of text.")
            return 2
        vals[k] = v.strip()
    name = src.name
    if RUNS_DIR.is_dir():
        for d in sorted(RUNS_DIR.iterdir()):
            c = d / "config.json"
            if c.is_file() and json.loads(c.read_text()).get("request") == name:
                print(f"START REFUSED — request {name} already started "
                      f"{d.name}. Push a new request file for a new run.")
                return 2
    ns = argparse.Namespace(mode=vals["mode"], product=vals["product"],
                            account=vals["account"] or "@glamorousgrammyglowup",
                            pick=vals["product"], pick_id="", model="",
                            by=f"Muse request {name}", request=name)
    return cmd_create(ns)


def cmd_status(args):
    run = resolve_run(args.run)
    text, _ = render_status(run)
    write_derived_block(run)
    write_status_file()
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
    if target < 2 or target > 11:
        print(f"CHECK to Step {target}: not a step that can be checked — "
              "use --to 2 through 11 (Step 1 is the run itself; Step 11 is "
              "freeze-locked).")
        return 2
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
    if not session_guard(run, args.by, 4, args, "ATTACH PHOTO"):
        return 2
    dest_dir = run / "steps" / STEP_DIRS[4]
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    (dest_dir / "GRABBED-BY.txt").write_text(args.by + "\n", encoding="utf-8")
    sheet_log(run, f"Step 4: listing photo attached ({src.name}), grabbed by {args.by}.")
    print(f"Attached {src.name} to {run.name}/steps/step4-photo/ (grabber of record: {args.by})")
    sync_chain(run, actor=args.by, submitted=dest)
    write_status_file()
    return 0


def cmd_record_match(args):
    run = resolve_run(args.run)
    if not session_guard(run, args.checker, 5, args, "RECORD MATCH"):
        return 2
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
    sync_chain(run, actor=args.checker,
               submitted=run / "steps" / STEP_DIRS[5] / "match-verdict.md")
    write_status_file()
    return 0


def _mila_only(args, what):
    who = (getattr(args, "by", "") or "").strip()
    if who.lower() != "mila":
        print(f"REFUSED — only Mila approves the {what} (Glam, Nov 25: the "
              "chain goes ahead after Mila approves; Glam rules once, on the "
              f"finished video). Got --by \"{who}\".")
        return False
    return True


def _place_verdict(args, run, step, paths, dest_ok, dest_back):
    """Return 0 when a signed verdict was placed, 2 when refused, None when
    there is no verdict file and the old --by Mila path should run."""
    vf = getattr(args, "verdict_file", None)
    if not vf:
        return None
    ok, why, kv = mila_verify(Path(vf).expanduser(), run.name, step, paths)
    if not ok:
        print(f"REFUSED — the verdict file doesn't count: {why}.")
        return 2
    sid = session_guard(run, "Mila", step, args, "MILA VERDICT")
    if not sid:
        return 2
    if not test_mode() and kv.get("session") != sid:
        print("REFUSED — Mila's verdict was signed in a different session "
              f"({kv.get('session') or 'none'}) than the one placing it "
              f"({sid}). Mila signs and places her own verdict.")
        return 2
    dest = dest_ok if kv.get("verdict") == "APPROVE" else dest_back
    shutil.copy2(Path(vf).expanduser(), dest)
    if kv.get("verdict") != "APPROVE":
        dest.write_text(dest.read_text() + "\n".join([
            f"sent_back_by: Mila",
            f"script_sha256: {sha256_file(paths[0])}" if step == 6 else
            f"image_sha256: {image_set_sha(paths[0].parent)}",
            f"notes: {kv.get('notes', '')}"]) + "\n", encoding="utf-8")
    sheet_log(run, f"Step {step}: Mila's signed verdict placed — "
                   f"{kv.get('verdict')}.")
    print(f"Mila's signed verdict for Step {step}: {kv.get('verdict')}.")
    return 0


def _can_sign():
    p = mila_key_path()
    return p.is_file() and not key_in_shared_folder(p)


def cmd_approve_script(args):
    """Mila's Step 6 gate: approve the exact script, or send it back."""
    run = resolve_run(args.run)
    folder0 = run / "steps" / STEP_DIRS[6]
    if getattr(args, "verdict_file", None):
        r = _place_verdict(args, run, 6, [folder0 / "script.md"],
                           folder0 / "mila-script-approval.md",
                           folder0 / "mila-script-sendback.md")
        if r:
            return r
        info = sync_chain(run, actor="Mila")
        print(f"Chain: next is {info.get('agent') or info.get('to')} "
              f"(Step {info.get('step')}).")
        write_status_file()
        return 0
    if not _mila_only(args, "script"):
        return 2
    if not _can_sign():
        print("REFUSED — Mila's approvals count only from her signed verdict "
              "file (made by the Mila sign workflow, mila-sign.yml); "
              "pass it with --verdict-file. Typing --by Mila is not enough.")
        return 2
    folder = run / "steps" / STEP_DIRS[6]
    script = folder / "script.md"
    if not nonempty_file(script):
        print("REFUSED — no script on file yet; the Story Agent submits it first.")
        return 2
    if args.send_back:
        (folder / "mila-script-sendback.md").write_text(
            f"sent_back_by: Mila\nscript_sha256: {sha256_file(script)}\n"
            f"notes: {args.send_back.strip()}\nrecorded_at: {now_stamp()}\n",
            encoding="utf-8")
        sheet_log(run, f"Step 6: Mila sent the script back — {args.send_back.strip()}")
        print(f"Mila sent the script back to the Story Agent: {args.send_back.strip()}")
    else:
        bad = script_findings(run)
        if bad:
            print("APPROVAL REFUSED — the script FAILS the Step 6 script check; "
                  "an approval is not recorded on a failing script:")
            for cat, msg in bad:
                print(f"  [{cat}] {msg}")
            sheet_log(run, "Step 6: script approval REFUSED — script fails the "
                           f"script check ({len(bad)} finding(s)).")
            return 2
        sid = session_guard(run, "Mila", 6, args, "MILA APPROVAL")
        if not sid:
            return 2
        (folder / "mila-script-approval.md").write_text(
            mila_sign_text(run.name, 6, "APPROVE", [script], session=sid),
            encoding="utf-8")
        sheet_log(run, "Step 6: Mila's script approval recorded.")
        print(f"Recorded Mila's script approval for {run.name}.")
    info = sync_chain(run, actor="Mila")
    print(f"Chain: next is {info.get('agent') or info.get('to')} "
          f"(Step {info.get('step')}).")
    write_status_file()
    return 0


def cmd_approve_image(args):
    """Mila's Step 7 gate: approve the exact model photo, or send it back."""
    run = resolve_run(args.run)
    folder0 = run / "steps" / STEP_DIRS[7]
    if getattr(args, "verdict_file", None):
        r = _place_verdict(args, run, 7, files_with_ext(folder0, IMAGE_EXTS),
                           folder0 / "mila-image-approval.md",
                           folder0 / "mila-image-sendback.md")
        if r:
            return r
        info = sync_chain(run, actor="Mila")
        print(f"Chain: next is {info.get('agent') or info.get('to')} "
              f"(Step {info.get('step')}).")
        write_status_file()
        return 0
    if not _mila_only(args, "model photo"):
        return 2
    if not _can_sign():
        print("REFUSED — Mila's approvals count only from her signed verdict "
              "file (made by the Mila sign workflow, mila-sign.yml); "
              "pass it with --verdict-file. Typing --by Mila is not enough.")
        return 2
    folder = run / "steps" / STEP_DIRS[7]
    imgs = files_with_ext(folder, IMAGE_EXTS)
    if not imgs:
        print("REFUSED — no model photo on file in steps/step7-styled/; the "
              "Casting / Image Agent submits it first.")
        return 2
    if args.send_back:
        (folder / "mila-image-sendback.md").write_text(
            f"sent_back_by: Mila\nimage_sha256: {image_set_sha(folder)}\n"
            f"notes: {args.send_back.strip()}\nrecorded_at: {now_stamp()}\n",
            encoding="utf-8")
        sheet_log(run, f"Step 7: Mila sent the model photo back — {args.send_back.strip()}")
        print(f"Mila sent the model photo back to Casting: {args.send_back.strip()}")
    else:
        sid = session_guard(run, "Mila", 7, args, "MILA APPROVAL")
        if not sid:
            return 2
        (folder / "mila-image-approval.md").write_text(
            mila_sign_text(run.name, 7, "APPROVE", imgs, session=sid),
            encoding="utf-8")
        sheet_log(run, "Step 7: Mila's model photo approval recorded.")
        print(f"Recorded Mila's model photo approval for {run.name}.")
    info = sync_chain(run, actor="Mila")
    print(f"Chain: next is {info.get('agent') or info.get('to')} "
          f"(Step {info.get('step')}).")
    write_status_file()
    return 0


def cmd_mila_sign(args):
    """Mila signs a verdict (only where her private key lives)."""
    if key_in_shared_folder(mila_key_path()):
        print("REFUSED — Mila's key is in a shared folder. It lives only in "
              "Mila's own session (~/.mila); a shared key lets anyone sign "
              "as her.")
        return 2
    if not _can_sign():
        print("REFUSED — Mila's signing key isn't on this machine. Only Mila "
              "signs her verdicts, in her own session.")
        return 2
    sid = (args.session or os.environ.get("FARM_SESSION_ID") or "").strip()
    if not sid and test_mode():
        sid = "session_TESTMODEMila"
    if not SESSION_RE.match(sid):
        print("REFUSED — Mila signs with her own session id "
              "(--session session_...).")
        return 2
    files = [Path(f).expanduser() for f in args.file]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print(f"REFUSED — file(s) not found: {', '.join(missing)}")
        return 2
    text = mila_sign_text(args.run, args.step, args.verdict, files,
                          args.notes or "", session=sid)
    out = Path(args.out or f"mila-verdict-{args.run}-step{args.step}.md")
    out.write_text(text, encoding="utf-8")
    print(f"Signed Mila's {args.verdict.upper()} for {args.run} Step "
          f"{args.step} → {out}")
    return 0


def cmd_mila_keygen(args):
    """Mila's own session makes her key pair. The private key stays in this
    session's home folder; only the public key is printed, for farm-rules.json."""
    p = mila_key_path()
    if key_in_shared_folder(p):
        print("REFUSED — the key may not live in a shared folder.")
        return 2
    if p.is_file() and not args.replace:
        seed = bytes.fromhex(p.read_text().strip())
        print(f"Mila's key already exists here. Public key: "
              f"{_ed.public_key(seed).hex()}")
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    seed = os.urandom(32)
    p.write_text(seed.hex() + "\n", encoding="utf-8")
    os.chmod(p, 0o600)
    print("Mila's private key was made and stays only in this session "
          f"({p}). Public key for farm-rules.json mila_signing.public_key: "
          f"{_ed.public_key(seed).hex()}")
    return 0


def cmd_proof(args):
    """Who did each step: the session id per step, from the run's ledger.
    Check each id against that agent's own run record: its Muse job history
    (muse_...) or its Claude session (session_...)."""
    run = resolve_run(args.run)
    recs = read_ledger(run)
    if not recs:
        print(f"PROOF {run.name}: no hand-ins with a session on file.")
        return 1
    print(f"PROOF {run.name} — the id behind every hand-in (check each "
          "against that agent's own Muse job history or Claude session):")
    roles = {}
    for r in recs:
        print(f"  Step {r.get('step')}  {r.get('role'):<26} {r.get('session')}"
              f"  ({id_kind(r.get('session', '')) or '?'})  {r.get('at')}  "
              f"{r.get('what')}")
        roles.setdefault(r.get("session"), set()).add(r.get("role"))
    multi = {s: sorted(v) for s, v in roles.items() if len(v) > 1}
    if multi:
        print("PROOF FAILS — one id played more than one role: "
              + "; ".join(f"{s}: {', '.join(v)}" for s, v in multi.items()))
        return 2
    print(f"OK — {len(roles)} different id(s), one role each.")
    return 0


def cmd_lint(args):
    run = resolve_run(args.run)
    findings = lint_package(run)
    if not findings:
        print("LINT: package passes — no label wording, no product description "
              "in words, no retired guard text, no drawn product, references "
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
    print("LINT RESULT: PASS.")
    return 0


def handoff_dir_for(run_id):
    return HANDOFF_DIR / run_id


def cmd_handoff(args):
    run = resolve_run(args.run)
    cfg = load_config(run)
    builds = sorted(f for f in (run / "steps" / STEP_DIRS[9]).iterdir()
                    if f.is_file() and f.name != "links.md") if (run / "steps" / STEP_DIRS[9]).is_dir() else []
    if not builds:
        print("HANDOFF REFUSED — no build files in steps/step9-builds/. "
              "There is nothing to hand to Mila.")
        sheet_log(run, "HANDOFF refused — no build files on file.")
        return 2
    dest = handoff_dir_for(cfg["run_id"])
    if (dest / "verdict.md").exists():
        # A verdict Mila wrote covers the builds she was handed BEFORE this
        # handoff — collect it first so it can never be read as covering
        # the new builds (audit fix #1).
        cmd_collect_verdict(argparse.Namespace(run=str(run)))
        sheet_log(run, "HANDOFF: a waiting verdict was collected first — it "
                       "covers only the builds handed before this handoff.")
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
        f"Product: {pick_from_record(run, cfg)} · Model: {cfg.get('cast_model', '')} · Mode: {cfg.get('mode', '')}\n"
        f"Build files in the run folder: {len(builds)} — files copied here: "
        f"{len(copied)} (every build, good and bad; the builder selects nothing).\n"
        + "".join(f"- {c}\n" for c in copied)
        + "\nMila: check per ~/workspace/farm-qc-handoff/README.md — frame by "
          "frame through the motion, bottle first, then ASR diff against "
          "approved-script.md. Write your verdict to verdict.md in this "
          "folder (verdict: PASS or FAIL, checker: Mila, with the frames/"
          "lines behind it).\n"
        + "\n" + render_scorecard_md() + "\n" + render_laws_md()
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
    # The verdict covers exactly the build files sitting in the handoff
    # folder when it is collected (audit fix #1) — a later build is not
    # covered and waits on Mila again.
    covers = build_set(handoff_dir_for(cfg["run_id"]))
    (run / "steps" / STEP_DIRS[10] / "verdict-covers.json").write_text(
        json.dumps(covers, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    moved = src.with_name(f"verdict-collected-{stamp}.md")
    n = 1
    while moved.exists():
        n += 1
        moved = src.with_name(f"verdict-collected-{stamp}-{n}.md")
    src.rename(moved)  # collected once — never re-collected (audit fix #2)
    kv = parse_kv(dest)
    sheet_log(run, f"Step 10: Mila's verdict collected from the QC handoff — "
                   f"{kv.get('verdict', '?')} (checker: {kv.get('checker', '?')}).")
    print(f"Collected Mila's verdict for {cfg['run_id']}: "
          f"{kv.get('verdict', '?')} — now on file at steps/step10-qc/mila-verdict.md")
    sync_chain(run, actor="Mila", submitted=dest)
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

    done_actions = set()
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
            if script_exists and state == "INVALID":
                note(f"STOP at Step 6 — the script FAILS the script check and "
                     f"goes back to the Story Agent to fix ({reason}). Mila "
                     "is not asked to approve a failing script.")
            elif script_exists and "changed after Mila" in reason:
                note("STOP at Step 6 — the script changed after Mila's "
                     "approval; waiting on Mila to approve the new text.")
            elif script_exists:
                note("STOP at Step 6 — waiting on Mila's script approval "
                     "(job open for Mila). Glam is not asked before the video.")
            else:
                note("STOP at Step 6 — no script on file yet. Writing the "
                     "script is an agent step; the driver resumes once the "
                     "script and Mila's approval are on file.")
            break
        if first_open == 8 and state == "INVALID":
            note(f"STOP at Step 8 — {reason}")
            break
        if first_open == 10:
            builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
            dest = handoff_dir_for(cfg["run_id"])
            handed = bool(builds) and dest.is_dir() and all(
                (dest / b.name).exists()
                and sha256_file(dest / b.name) == sha256_file(b)
                for b in builds)
            verdict_waiting = (dest / "verdict.md").exists()
            if builds and not handed and "handoff" not in done_actions:
                done_actions.add("handoff")
                cmd_handoff(argparse.Namespace(run=str(run)))
                note("Auto-handoff: every build copied to the QC handoff "
                     "folder for Mila.")
                continue
            if verdict_waiting and "collect" not in done_actions:
                done_actions.add("collect")
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
    info = sync_chain(run)
    if info.get("kind") in ("agent", "mila"):
        a = AGENTS.get(info["step"], {})
        log.append(f"Job open: {info['agent']} (Step {info['step']}) — "
                   f"needs: {'; '.join(a.get('needs', []))}")
    write_derived_block(run)
    return log


def cmd_drive(args):
    if refuse_if_old_rules("DRIVE"):
        return 2
    run = resolve_run(args.run)
    print(f"DRIVING {run.name} …")
    for line in drive_run(run):
        print(f"  {line}")
    build_review_manifest()
    return 0


def cmd_drive_all(args):
    if refuse_if_old_rules("DRIVE-ALL"):
        return 2
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted(d for d in RUNS_DIR.iterdir()
                  if d.is_dir() and (d / "config.json").exists())
    if not runs:
        print("drive-all: no runs in ~/workspace/farm-runs/ — nothing to drive.")
        write_status_file()
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

def watch_links(run):
    """steps/step9-builds/links.md: one 'filename: https://...' line per
    build (the video's Google Drive link), so Glam can watch it from the
    Review section (audit fix #29). Only https links are kept."""
    out = {}
    path = run / "steps" / STEP_DIRS[9] / "links.md"
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*[-*]?\s*([^:]+?)\s*:\s*(https://\S+)\s*$", line)
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def review_entry(run):
    cfg, results = derive(run)
    states = {n: state for n, name, state, reason in results}
    builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
    redo = parse_kv(run / "steps" / STEP_DIRS[9] / "glam-redo-notes.md")
    if not builds and not redo:
        return None
    verdict_kv = parse_kv(run / "steps" / STEP_DIRS[10] / "mila-verdict.md")
    mila_verdict = verdict_kv.get("verdict", "").upper() or "NONE"
    decision = parse_kv(run / "review-decision.md")
    decision_val = decision.get("decision", "").lower()
    if decision_val == "approved" and states.get(10) == "CLEARED":
        status = "Approved — ready to post (freeze on)"
    elif not builds:
        status = "Redo — being rebuilt with Glam's notes"
    elif states.get(10) == "CLEARED":
        status = "Waiting for Glam"
    else:
        status = "Not ready — waiting on Mila's check"
    links = watch_links(run)
    return {
        "run_id": cfg["run_id"],
        "product": pick_from_record(run, cfg),
        "cast_model": cfg.get("cast_model", ""),
        "mode": cfg.get("mode", ""),
        "account": cfg.get("account", ""),
        "mila_verdict": mila_verdict,
        "videos": [f"~/workspace/farm-runs/{cfg['run_id']}/steps/step9-builds/{v.name}"
                   for v in builds],
        "watch_links": {v.name: links.get(v.name, "") for v in builds},
        "review_status": status,
        "ready_for_review": states.get(10) == "CLEARED" and decision_val != "approved",
        "glam_notes": decision.get("notes", "") or redo.get("notes", ""),
        "redo_count": len(list((run / "redo").glob("redo-*"))) if (run / "redo").is_dir() else 0,
        "is_test": bool(re.search(r"TEST|MOCK", (pick_from_record(run, cfg) or "").upper())),
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
    write_status_file()
    return manifest


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_review_html(entries):
    """The Review section's entries block for the farm page.

    This exact markup sits between REVIEW-ENTRIES:BEGIN / :END markers on
    the farm page; `review-manifest` output (this file) is what an artifact
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
        vids = ""
        for v in e["videos"]:
            name = v.rsplit("/", 1)[-1]
            link = e.get("watch_links", {}).get(name, "")
            if link:
                vids += (f'<div class="review-video">🎬 {esc(name)} — '
                         f'<a href="{esc(link)}" target="_blank" '
                         f'rel="noopener">▶ Watch</a></div>')
            else:
                vids += (f'<div class="review-video">🎬 {esc(name)} — No '
                         'watch link yet — add it to links.md</div>')
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


def apply_review_decision(run, decision, notes, recorded_by):
    """Glam's one ruling on the finished video. approved = ready to post
    (the freeze stays on; nothing posts). redo = the video goes back into
    the chain to the Video Agent with her notes; Mila checks the rebuild."""
    decision = {"sent-back": "redo"}.get(decision, decision)
    cfg, results = derive(run)
    states = {n: state for n, name, state, reason in results}
    if states.get(10) != "CLEARED":
        print("REVIEW DECISION REFUSED — this run has not cleared Mila's "
              "check (Step 10), so there is no finished video for Glam to "
              "rule on. A run cannot be approved or sent back before QC.")
        sheet_log(run, f"REVIEW DECISION refused — Step 10 not cleared; "
                       f"attempted decision: {decision}.")
        return 2
    if decision == "redo" and not notes.strip():
        print("REDO REFUSED — a redo needs Glam's notes so the Video Agent "
              "knows what to change.")
        return 2
    notes = " ".join(notes.split())
    if decision == "approved":
        (run / "review-decision.md").write_text(
            f"decision: approved\ndecided_by: Glam\nnotes: {notes}\n"
            f"recorded_by: {recorded_by}\nrecorded_at: {now_stamp()}\n",
            encoding="utf-8")
        sheet_log(run, "REVIEW: Glam APPROVED the finished video — ready to "
                       "post. Freeze stays ON; nothing posts.")
        append_handoff(run, {"at": now_stamp(), "from": "Glam", "to": "Posting (frozen)",
                             "step": 11, "what": "Glam approved the finished video"
                             + (f" — {notes}" if notes else ""),
                             "inputs": [], "output": "review-decision.md",
                             "result": "approved — freeze on"})
        print(f"Recorded Glam's APPROVAL for {run.name}. Ready to post — the "
              "freeze stays on, nothing posts.")
    else:
        redo_root = run / "redo"
        n = len(list(redo_root.glob("redo-*"))) + 1 if redo_root.is_dir() else 1
        dest = redo_root / f"redo-{n}"
        for sub in ("builds", "qc", "qc-handoff"):
            (dest / sub).mkdir(parents=True, exist_ok=True)
        b_dir = run / "steps" / STEP_DIRS[9]
        for f in list(b_dir.iterdir()):
            if f.is_file() and f.name not in ("JOB.md", "glam-redo-notes.md"):
                f.rename(dest / "builds" / f.name)
        q_dir = run / "steps" / STEP_DIRS[10]
        if q_dir.is_dir():
            for f in list(q_dir.iterdir()):
                if f.is_file() and f.name != "JOB.md":
                    f.rename(dest / "qc" / f.name)
        h_dir = handoff_dir_for(cfg["run_id"])
        if h_dir.is_dir():
            for f in list(h_dir.iterdir()):
                if f.is_file():
                    f.rename(dest / "qc-handoff" / f.name)
        old = run / "review-decision.md"
        if old.exists():
            old.rename(dest / "review-decision.md")
        body = (f"decision: redo\ndecided_by: Glam\nnotes: {notes}\n"
                f"redo: {n}\nrecorded_by: {recorded_by}\nrecorded_at: {now_stamp()}\n")
        (dest / "glam-notes.md").write_text(body, encoding="utf-8")
        (b_dir / "glam-redo-notes.md").write_text(body, encoding="utf-8")
        sheet_log(run, f"REVIEW: Glam asked for a REDO (#{n}) — {notes}. Old "
                       f"builds and Mila's verdict kept in redo/redo-{n}/.")
        print(f"Recorded Glam's REDO for {run.name}: back to the Video Agent "
              f"with her notes. Old builds kept in redo/redo-{n}/.")
        sync_chain(run, actor="Glam")
    build_review_manifest()
    write_status_file()
    return 0


def cmd_review_decision(args):
    run = resolve_run(args.run)
    return apply_review_decision(run, args.decision, args.notes or "",
                                 args.recorded_by)


def cmd_review_feed(args):
    """Write review-feed.json: one row per finished video, in the shape the
    Farm Video Review page reads (its 'videos' collection, keyed by run_id).
    Whoever runs the farm copies these rows into the page's database; Glam's
    taps come back through review-apply."""
    manifest = build_review_manifest()
    rows = []
    for e in manifest["entries"]:
        rows.append({
            "run_id": e["run_id"], "product": e["product"], "mode": e["mode"],
            "account": e["account"], "mila_verdict": e["mila_verdict"],
            "review_status": e["review_status"], "is_test": bool(e.get("is_test")),
            "glam_notes": e.get("glam_notes", ""), "redo_count": e.get("redo_count", 0),
            "videos": [{"file": name, "url": url if url.startswith("https://") else ""}
                       for name, url in e.get("watch_links", {}).items()],
            "updated_at": now_stamp(),
        })
    out = RUNNER_DIR / "review-feed.json"
    out.write_text(json.dumps({"videos": rows}, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"Review feed written: {out} ({len(rows)} video row(s))")
    for r in rows:
        print(f"  {r['run_id']} — {r['review_status']}")
    return 0


def cmd_review_apply(args):
    """Apply Glam's taps from the Farm Video Review page. The file is a JSON
    list exported from the page's saved decisions:
    [{"run_id": ..., "decision": "approved"|"redo", "notes": ..., "at": ...}]
    Each decision is applied once (its 'at' stamp is remembered)."""
    try:
        items = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"review-apply: can't read {args.file}: {e}")
        return 2
    if isinstance(items, dict):
        items = items.get("decisions", [])
    rc = 0
    for it in items:
        rid, dec = str(it.get("run_id", "")), str(it.get("decision", "")).lower()
        if dec not in ("approved", "redo") or not rid:
            print(f"  skip: {it!r} (needs run_id and decision approved|redo)")
            continue
        run = RUNS_DIR / rid
        if not (run / "config.json").exists():
            print(f"  skip: no run {rid}")
            continue
        seen = run / "review-applied.txt"
        key = f"{dec}|{it.get('at', '')}"
        if seen.exists() and key in seen.read_text(encoding="utf-8").splitlines():
            print(f"  {rid}: already applied ({dec} at {it.get('at', '')})")
            continue
        print(f"  {rid}: {dec}")
        r = apply_review_decision(run, dec, str(it.get("notes", "")),
                                  "Farm Video Review page")
        if r == 0:
            with seen.open("a", encoding="utf-8") as fh:
                fh.write(key + "\n")
        rc = rc or r
    return rc


# ----------------------------------------------------------------------------
# Rendering the master rules (farm-rules.json) for Mila's handoff. The old
# books were archived (Glam, Nov 24: "A) Do it") — rules live ONLY in
# farm-rules.json; nothing here reads or writes any archived book.
# Words in {curly braces} inside a law/step/scorecard line are filled from
# "numbers", so a number changes in one spot.
# ----------------------------------------------------------------------------

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def fill(text):
    """Replace {key} with numbers[key] from farm-rules.json."""
    return PLACEHOLDER.sub(
        lambda m: str(NUM[m.group(1)]) if m.group(1) in NUM else m.group(0),
        str(text))


def rule_texts(data):
    """Every rule string that may carry {placeholders}, with where it lives."""
    out = []
    for l in data.get("laws", []):
        out += [(f"laws.{l.get('id')}.title", l.get("title", "")),
                (f"laws.{l.get('id')}.text", l.get("text", ""))]
    for st in data.get("run_order", []):
        out += [(f"run_order.{st.get('n')}.name", st.get("name", "")),
                (f"run_order.{st.get('n')}.text", st.get("text", ""))]
    sc = data.get("mila_scorecard", {})
    for k, v in sc.items():
        for i, x in enumerate(v if isinstance(v, list) else [v]):
            out.append((f"mila_scorecard.{k}[{i}]" if isinstance(v, list)
                        else f"mila_scorecard.{k}", x))
    for a in data.get("agents", []):
        out.append((f"agents.{a.get('step')}.job", a.get("job", "")))
    return out


def missing_placeholders(data):
    nums = data.get("numbers", {})
    bad = []
    for where, text in rule_texts(data):
        for key in PLACEHOLDER.findall(str(text)):
            if key not in nums:
                bad.append(f"{where}: {{{key}}} has no number in \"numbers\"")
    return bad


def render_scorecard_md():
    sc = RULES["mila_scorecard"]
    out = [f"## Mila's scorecard (farm-rules.json, version {RULES['version']})",
           f"CRITICAL — {fill(sc['critical_rule'])}"]
    out += [f"- {fill(x)}" for x in sc["critical"]]
    out.append(f"MAJOR — {fill(sc['major_rule'])}")
    out += [f"- {fill(x)}" for x in sc["major"]]
    out.append(f"MINOR — scored {fill(sc['minor_scale'])}: " +
               ". ".join(fill(x) for x in sc["minor"]) + ".")
    out.append(f"PASS BAR: {fill(sc['pass_bar'])}")
    out.append(f"SIGN-OFF: {fill(sc['sign_off'])}")
    return "\n".join(out) + "\n"


def render_laws_md():
    out = [f"## Farm laws (farm-rules.json, version {RULES['version']})"]
    out += [f"- {fill(l['title'])}: {fill(l['text'])}" for l in RULES["laws"]]
    return "\n".join(out) + "\n"


def cmd_sync_rules(args):
    print("sync-rules: nothing to sync — the old books are archived and the "
          "rules live ONLY in farm-rules.json. The page and the runner read it "
          "live, and Mila's handoff carries it on the next run. Run "
          "check-rules to prove nothing drifted.")
    return 0


# Names of the archived books. Built in pieces so this check never flags
# its own definition.
ARCHIVED_NAMES = ("merged-farm-" + "playbook", "RUNBOOK" + ".md",
                  "VERIFICATION" + ".md", "archive" + "/")


def archived_reads_in_runner(path):
    hits = []
    for i, line in enumerate(path.read_text(encoding="utf-8",
                                            errors="replace").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for name in ARCHIVED_NAMES:
            if name in line:
                hits.append(f"{path.name} line {i} reads '{name}': "
                            f"{line.strip()[:90]}")
    return hits


def archived_reads_in_page(path):
    """A page may LINK to the archive folder (so everyone can see it); it may
    never fetch or load an archived book as a source of rules."""
    hits = []
    text = path.read_text(encoding="utf-8", errors="replace")
    alt = "|".join(re.escape(n) for n in ARCHIVED_NAMES)
    pats = [r"fetch\(\s*['\"`][^'\"`]*(?:" + alt + ")",
            r"\bsrc\s*=\s*['\"][^'\"]*(?:" + alt + ")",
            r"XMLHttpRequest[^;]*(?:" + alt + ")",
            r"import\s*\(\s*['\"][^'\"]*(?:" + alt + ")"]
    for pat in pats:
        for m in re.finditer(pat, text):
            ln = text.count("\n", 0, m.start()) + 1
            hits.append(f"{path.name} line {ln} loads an archived book: "
                        f"{m.group(0)[:90]}")
    return hits


def cmd_check_rules(args):
    drift = []
    print(f"check-rules: farm-rules.json OK — {RULES_PATH} "
          f"(version {RULES['version']}, every key the runner needs present)")
    for b in missing_placeholders(RULES):
        drift.append(b)
    # The chain: one agent per step 2–10, each naming its laws (that exist),
    # its output file and what it needs.
    law_ids = {l.get("id") for l in RULES.get("laws", [])}
    steps_have = {int(a.get("step", 0)) for a in RULES.get("agents", [])}
    for n in range(2, 11):
        if n not in steps_have:
            drift.append(f"agents: no agent for Step {n} — the chain has a gap")
    for a in RULES.get("agents", []):
        for k in ("agent", "job", "output_file", "needs", "hands_to", "laws"):
            if not a.get(k):
                drift.append(f"agents.{a.get('step')}: missing '{k}'")
        for lid in a.get("laws", []):
            if lid not in law_ids:
                drift.append(f"agents.{a.get('step')}: law '{lid}' is not in laws")
        if "own-step-handoff" not in a.get("laws", []):
            drift.append(f"agents.{a.get('step')}: missing Glam's locked rule "
                         "'own-step-handoff' (your step only, hand off, or BLOCKED)")
    runner = Path(args.runner) if getattr(args, "runner", None) else \
        Path(__file__).resolve()
    explicit_page = bool(getattr(args, "page", None))
    page = Path(args.page) if explicit_page else RULES_PATH.parent / "index.html"
    if not explicit_page and not page.exists():
        page = Path(__file__).resolve().parent.parent / "index.html"
    if runner.exists():
        drift += archived_reads_in_runner(runner)
    else:
        drift.append(f"runner not found ({runner})")
    if page.exists():
        ptext = page.read_text(encoding="utf-8", errors="replace")
        for need in ("farm-rules.json", "farm-status.json"):
            if need not in ptext:
                drift.append(f"{page.name} does not read {need}")
        drift += archived_reads_in_page(page)
    elif explicit_page:
        drift.append(f"index.html not found ({page})")
    else:
        print("check-rules: the farm page isn't on this machine — page checks "
              "skipped (run check-rules in the repo, or pass --page).")
    # Glam's rule (law id BANNED_LAW): one retired agent is off the farm for
    # good. Only the law that bans her may say the name; any other mention
    # anywhere in the farm is drift. (The name is assembled so this guard
    # never trips on itself.)
    banned = "N" + "ora"
    banned_law = "no-" + banned.lower()
    root = Path(__file__).resolve().parent.parent
    if (root / "index.html").exists() or (root / ".git").exists():
        for f in sorted(root.rglob("*")):
            if (not f.is_file() or ".git" in f.parts
                    or f.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS):
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if f.name == "farm-rules.json":
                try:
                    data = json.loads(txt)
                    data["laws"] = [l for l in data.get("laws", [])
                                    if l.get("id") != banned_law]
                    txt = json.dumps(data)
                except ValueError:
                    pass
            if f.name == "fixcheck.sh":
                continue
            if re.search(r"\b" + banned + r"\b", txt, re.IGNORECASE):
                drift.append(f"{f.relative_to(root)} mentions {banned} — "
                             f"Glam's rule: {banned} is off the farm for good")
    if drift:
        print("check-rules: DRIFT —")
        for d in drift:
            print(f"  - {d}")
        print("Fix: rules live only in farm-rules.json — edit it there, and "
              "never read a rule from an archived book.")
        return 2
    print("check-rules: OK — farm-rules.json is complete, every {placeholder} "
          "has a number, the page reads farm-rules.json and farm-status.json, "
          "and nothing reads an archived book.")
    return 0


# ----------------------------------------------------------------------------
# farm-status.json — every run's live status, step by step, where everyone
# can see it (Glam, Nov 24: "Nothing should be hidden where no one can see
# what's going on"). The farm page's Live Run Board reads this file.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# THE AGENT CHAIN (Glam, Nov 24: "one agent does something and hands it to
# the other agent"). Every agent's job comes from farm-rules.json → agents.
# When a step clears, the runner opens the NEXT agent's job (JOB.md in that
# step's folder) and logs the handoff in handoffs.jsonl. An agent submits its
# work with `submit`; the step's checks run at once — pass hands off, fail
# sends it straight back to the same agent with the findings on its JOB.md.
# The runner never writes an agent's work, never calls an AI or a website,
# and never posts.
# ----------------------------------------------------------------------------

AGENTS = {int(a["step"]): a for a in RULES.get("agents", [])}
CHAIN_SKIP_NAMES = {"JOB.md", "BLOCKED.md", "GRABBED-BY.txt", "links.md",
                    "verdict-covers.json", "staging-proof.md"}


def agent_name(step):
    return AGENTS.get(step, {}).get("agent", f"Step {step} agent")


def by_allowed(step, by):
    a = AGENTS.get(step, {})
    allowed = [x.lower() for x in a.get("by", [a.get("agent", "")])]
    return by.strip().lower() in allowed


def chain_input_files(run, step):
    out = []
    for pat in AGENTS.get(step, {}).get("input_files", []):
        for f in sorted(run.glob(pat)):
            if (not f.is_file() or f.name in CHAIN_SKIP_NAMES
                    or f.name.startswith(("glam-", "mila-script-", "mila-image-"))
                    or f.suffix == ".tmp"):
                continue
            out.append({"file": str(f.relative_to(run)),
                        "sha256": sha256_file(f)})
    return out


def handoffs_path(run):
    return run / "handoffs.jsonl"


def read_handoffs(run):
    p = handoffs_path(run)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def append_handoff(run, rec):
    with handoffs_path(run).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def chain_state(run):
    try:
        return json.loads((run / "chain-state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_chain_state(run, st):
    (run / "chain-state.json").write_text(json.dumps(st, indent=2) + "\n",
                                          encoding="utf-8")


# Mila's two gates before the video (Glam, Nov 25: "I want it to go ahead
# after Mila approve it ... Don't wait for my approval to make the video.")
MILA_GATES = {
    6: {"what": "approve the exact script (steps/step6-script/script.md) or send it back with notes",
        "job": "Read the script against the farm laws and the real listing photo. Place your verdict ONLY by running the Mila sign workflow (mila-sign.yml) with run <run>, step 6, verdict APPROVE or SENDBACK, notes listing every fix, and your own session id; it signs with the key only it holds and approves or sends back to the Story Agent. Your approval covers this exact script; the Casting / Image Agent starts the moment you approve. Glam is not asked; she rules once, on the finished video.",
        "files": lambda run: [run / "steps" / STEP_DIRS[6] / "script.md"],
        "needs": ["Mila (an AI agent) to read the script against the farm laws"]},
    7: {"what": "approve the model photo (steps/step7-styled/) or send it back with notes",
        "job": "Check the model photo is one of Glam's uploaded models, used as-is, and fits the product and buyer. Place your verdict ONLY by running the Mila sign workflow (mila-sign.yml) with run <run>, step 7, verdict APPROVE or SENDBACK, notes, and your own session id; it signs with the key only it holds. The package and the video build start the moment you approve. Glam is not asked; she rules once, on the finished video.",
        "files": lambda run: files_with_ext(run / "steps" / STEP_DIRS[7], IMAGE_EXTS),
        "needs": ["Mila (an AI agent) to look at the photo"]},
}


def step_findings(run, n, reason):
    if n == 6 and reason.startswith("Mila sent"):
        return [reason]
    if n == 6:
        f = [m for _, m in script_findings(run)]
        return f or [reason]
    if n == 8:
        f = []
        for cat, no, text in lint_package(run):
            where = f"line {no}" if no else "package"
            f.append(f"[{cat}] {where}: {text}")
        return f or [reason]
    return [reason]


def open_job_info(run):
    """Who acts next on this run, from the evidence: an agent's job, Mila,
    Glam's approval gate, or Glam's final review ('done')."""
    cfg, results = derive(run)
    steps = run / "steps"
    for n, name, st, reason in results:
        if n == 11:
            break
        if st == "CLEARED":
            continue
        if n == 1:
            continue
        if n == 6 and nonempty_file(steps / STEP_DIRS[6] / "script.md") \
                and st not in ("INVALID", "BLOCKED"):
            return {"kind": "mila", "step": 6, "agent": "Mila", "to": "Mila",
                    "what": MILA_GATES[6]["what"], "reason": reason, "findings": []}
        if n == 7 and files_with_ext(steps / STEP_DIRS[7], IMAGE_EXTS) \
                and st not in ("INVALID", "BLOCKED"):
            return {"kind": "mila", "step": 7, "agent": "Mila", "to": "Mila",
                    "what": MILA_GATES[7]["what"], "reason": reason, "findings": []}
        if n == 10:
            kv = parse_kv(steps / STEP_DIRS[10] / "mila-verdict.md")
            if st == "INVALID" and kv.get("verdict", "").upper() != "PASS":
                return {"kind": "agent", "step": 9, "agent": agent_name(9),
                        "to": agent_name(9), "reason": reason,
                        "what": "rebuild — Mila sent the build back",
                        "findings": [reason]}
            return {"kind": "mila", "step": 10, "agent": agent_name(10),
                    "to": agent_name(10), "reason": reason,
                    "what": "QC check of every build in the handoff folder",
                    "findings": [reason] if st == "INVALID" else []}
        if n == 9:
            redo = parse_kv(steps / STEP_DIRS[9] / "glam-redo-notes.md")
            if redo.get("notes"):
                return {"kind": "agent", "step": 9, "agent": agent_name(9),
                        "to": agent_name(9), "reason": reason,
                        "what": "rebuild — Glam asked for a redo",
                        "findings": [f"Glam asked for a redo (#{redo.get('redo', '?')}): "
                                     f"{redo['notes']}"]}
        sent_back = (st == "INVALID"
                     or (n == 2 and nonempty_file(steps / STEP_DIRS[2] / "scout.md")))
        return {"kind": "agent", "step": n, "agent": agent_name(n),
                "to": agent_name(n), "reason": reason,
                "what": AGENTS.get(n, {}).get("output", ""),
                "findings": step_findings(run, n, reason) if sent_back else []}
    return {"kind": "done", "step": None, "agent": "", "to": "Glam",
            "what": "final review — Ready for Glam, freeze on",
            "reason": "complete through Step 10", "findings": []}


def time_cap_line():
    """Glam, Nov 25: every agent job gets a 5-minute cap."""
    from datetime import timedelta
    due = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
    return (f"⏱ Time cap: 5 minutes (until {due}). At the cap, hand in what "
            "you have, or run report-blocked with the reason.\n")


def locked_rule_line():
    """Glam's locked rule (Nov 25), printed at the top of EVERY job."""
    law = next((l for l in RULES.get("laws", []) if l.get("id") == "own-step-handoff"), None)
    if not law:
        return ""
    return f"## 🔒 LOCKED: {fill(law['title'])}\n{fill(law['text'])}\n"


def mila_gate_job_md(run, info):
    n = info["step"]
    g = MILA_GATES[n]
    cfg = load_config(run)
    out = [f"# JOB — Step {n}: Mila (approval gate)",
           f"Run: {cfg['run_id']} · rules version {RULES.get('version')} · "
           f"opened {now_stamp()} · posting freeze ON\n",
           locked_rule_line(),
           time_cap_line(),
           "## Your job", g["job"].replace("<run>", cfg["run_id"]) + "\n",
           f"Can't do it? Stop, and put it on the board at once: runner.py "
           f"report-blocked {cfg['run_id']} --step {n} --by Mila --reason "
           "\"what blocked you and why\"\n",
           "## Check these (exact files)"]
    out += [f"- {f.relative_to(run)}  (sha256 {sha256_file(f)[:16]}…)"
            for f in g["files"](run)]
    out.append("\n## Farm laws (from farm-rules.json)")
    out += [f"- {fill(l['title'])}: {fill(l['text'])}" for l in RULES.get("laws", [])]
    return "\n".join(out) + "\n"


def job_md(run, info):
    n = info["step"]
    if info.get("kind") == "mila" and n in MILA_GATES:
        return mila_gate_job_md(run, info)
    a = AGENTS.get(n, {})
    cfg = load_config(run)
    laws = {l["id"]: l for l in RULES.get("laws", [])}
    out = []
    if info.get("findings"):
        out.append("## ⚠ SENT BACK — fix these, then submit again\n")
        out += [f"- {f}" for f in info["findings"]]
        out.append("")
    out.append(f"# JOB — Step {n}: {a.get('agent', '')}")
    out.append(f"Run: {cfg['run_id']} · rules version {RULES.get('version')} · "
               f"opened {now_stamp()} · posting freeze ON\n")
    out.append(locked_rule_line())
    out.append(time_cap_line())
    out.append("## Your job")
    out.append(fill(a.get("job", "")) + "\n")
    out.append("## Read these (exact files)")
    ins = chain_input_files(run, n)
    out += ([f"- {i['file']}  (sha256 {i['sha256'][:16]}…)" for i in ins]
            or ["- " + "; ".join(a.get("inputs", []))])
    out.append("\n## Farm laws you follow (from farm-rules.json)")
    for lid in a.get("laws", []):
        if lid in laws:
            out.append(f"- {fill(laws[lid]['title'])}: {fill(laws[lid]['text'])}")
    out.append("\n## Hand in")
    out.append(f"- Output: {a.get('output', '')} → {a.get('output_file', '')}")
    if n == 10:
        out.append("- Hand in ONLY by running the Mila sign workflow "
                   f"(mila-sign.yml) with run {cfg['run_id']}, step 10, verdict "
                   "PASS or FAIL, notes, and your own session id. It signs "
                   "with the key only it holds and submits for you.")
    elif n == 5:
        out.append("- Submit with: runner.py record-match "
                   f"{cfg['run_id']} --checker <you> --grabber <grabber> "
                   "--verdict MATCH|NO-MATCH --session <your id>")
    else:
        out.append(f"- Submit with: runner.py submit {cfg['run_id']} --step {n} "
                   f"--by \"{a.get('agent', '').split(' + ')[0]}\" --file <your file> "
                   "--session <your id>")
    if n != 10:
        out.append("- <your id> is muse_ followed by YOUR OWN Muse scheduled "
                   "job's id (a Claude agent uses its session_... id). One id "
                   "acts as one role per run; the proof lists it for this step.")
    out.append(f"- Can't do it? Stop, and put it on the board at once: "
               f"runner.py report-blocked {cfg['run_id']} --step {n} --by "
               f"\"{a.get('agent', '').split(' + ')[0]}\" --reason \"what blocked you "
               "and why\" --session <your id>")
    out.append(f"- Hands to: {a.get('hands_to', '')}")
    out.append("\n## What this job needs that the runner can't do by itself")
    out += [f"- {x}" for x in a.get("needs", [])]
    if n == 10:
        out.append(f"\nBuilds are in ~/workspace/farm-qc-handoff/{cfg['run_id']}/ "
                   "(HANDOFF.md there carries your full scorecard).")
    return "\n".join(out) + "\n"


def sync_chain(run, actor=None, submitted=None):
    """Open the next job (or gate) if it changed, and log the handoff."""
    info = open_job_info(run)
    sub_sig = sha256_file(submitted) if submitted and Path(submitted).is_file() else ""
    sig = json.dumps([info["kind"], info["step"], info["agent"],
                      info["findings"], sub_sig], ensure_ascii=False)
    st = chain_state(run)
    if st.get("sig") == sig:
        return info
    cfg = load_config(run)
    if info["kind"] in ("agent", "mila"):
        if info["kind"] == "mila" and info["step"] == 10:
            builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
            dest = handoff_dir_for(cfg["run_id"])
            handed = bool(builds) and dest.is_dir() and all(
                (dest / b.name).exists()
                and sha256_file(dest / b.name) == sha256_file(b) for b in builds)
            if builds and not handed:
                import contextlib, io
                with contextlib.redirect_stdout(io.StringIO()):
                    cmd_handoff(argparse.Namespace(run=str(run)))
        jd = run / "steps" / STEP_DIRS[info["step"]]
        jd.mkdir(parents=True, exist_ok=True)
        (jd / "JOB.md").write_text(job_md(run, info), encoding="utf-8")
    if info["kind"] == "agent":
        result = "sent back" if info["findings"] else "handed off"
    elif info["kind"] == "mila":
        result = "waiting on Mila"
    else:
        result = "waiting on Glam"
    frm = actor or st.get("last_actor") or "Start a Run"
    if info["findings"] and info["kind"] == "agent":
        what = (f"{actor} submitted; " if actor else "") + \
               f"SENT BACK to {info['agent']}: {info['findings'][0]}"
    elif info["kind"] in ("agent", "mila"):
        what = f"job opened for {info['agent']}: {info['what']}"
    else:
        what = info["what"]
    if info["kind"] == "mila" and info["step"] in MILA_GATES:
        inputs = [{"file": str(f.relative_to(run)), "sha256": sha256_file(f)}
                  for f in MILA_GATES[info["step"]]["files"](run)]
    elif info["kind"] in ("agent", "mila"):
        inputs = chain_input_files(run, info["step"])
    elif info["kind"] == "glam":
        inputs = [{"file": str(f.relative_to(run)), "sha256": sha256_file(f)}
                  for f in (files_with_ext(run / "steps" / STEP_DIRS[7], IMAGE_EXTS)
                            if info["step"] == 7
                            else [run / "steps" / STEP_DIRS[6] / "script.md"])]
    else:
        inputs = [{"file": str(f.relative_to(run)), "sha256": sha256_file(f)}
                  for f in files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)]
    output = ""
    if submitted:
        sp = Path(submitted)
        output = (f"{sp.relative_to(run)} (sha256 {sha256_file(sp)[:16]}…)"
                  if sp.is_file() and run in sp.parents else str(sp))
    elif info["kind"] == "mila" and info["step"] in MILA_GATES:
        output = "expected: Mila's approval or send-back"
    elif info["kind"] in ("agent", "mila"):
        output = "expected: " + AGENTS.get(info["step"], {}).get("output_file", "")
    rec = {"at": now_stamp(), "from": frm, "to": info["to"],
           "step": info["step"], "what": what, "inputs": inputs,
           "output": output, "result": result}
    append_handoff(run, rec)
    sheet_log(run, f"CHAIN: {frm} → {info['to']} (Step {info['step']}) — {result}")
    save_chain_state(run, {"sig": sig, "opened_at": now_stamp(),
                           "last_actor": actor or st.get("last_actor", ""),
                           "open": {k: info[k] for k in ("kind", "step", "agent", "to")}})
    return info


def open_job_entry(run, info=None):
    info = info or open_job_info(run)
    if info["kind"] not in ("agent", "mila"):
        return None
    a = AGENTS.get(info["step"], {})
    if info["kind"] == "mila" and info["step"] in MILA_GATES:
        a = MILA_GATES[info["step"]]
    return {"step": info["step"], "agent": info["agent"],
            "job_file": f"steps/{STEP_DIRS[info['step']]}/JOB.md",
            "job": fill(a.get("job", "")), "needs": a.get("needs", []),
            "since": chain_state(run).get("opened_at", ""),
            "sent_back": info["findings"]}


def cmd_submit(args):
    if refuse_if_old_rules("SUBMIT"):
        return 2
    run = resolve_run(args.run)
    n = args.step
    info = open_job_info(run)
    if n == 5:
        print("SUBMIT REFUSED — Step 5 is recorded with record-match "
              "(the checker must not be the grabber).")
        return 2
    if info["kind"] not in ("agent", "mila") or info["step"] != n:
        now = (f"Step {info['step']} — {info['to']}" if info["step"]
               else "Glam's final review")
        print(f"SUBMIT REFUSED — Step {n} isn't the open job. The chain is at "
              f"{now}. Agents hand off in order.")
        return 2
    if not by_allowed(n, args.by):
        a = AGENTS.get(n, {})
        print(f"SUBMIT REFUSED — Step {n} belongs to {a.get('agent')} "
              f"(accepted: {', '.join(a.get('by', []))}); '{args.by}' can't "
              "submit it.")
        return 2
    src = Path(args.file).expanduser()
    if not src.is_file():
        print(f"SUBMIT REFUSED — file not found: {src}")
        return 2
    if not session_guard(run, "Mila" if n == 10 else args.by, n, args,
                         "SUBMIT"):
        return 2
    folder = run / "steps" / STEP_DIRS[n]
    if n == 10:
        cfg = load_config(run)
        dest_dir = handoff_dir_for(cfg["run_id"])
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / "verdict.md")
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_collect_verdict(argparse.Namespace(run=str(run)))
        dest = folder / "mila-verdict.md"
    else:
        exts = {4: IMAGE_EXTS, 7: IMAGE_EXTS, 9: VIDEO_EXTS}.get(n)
        if exts and src.suffix.lower() not in exts:
            print(f"SUBMIT REFUSED — Step {n} takes "
                  f"{'an image' if exts is IMAGE_EXTS else 'a video'} file "
                  f"({', '.join(sorted(exts))}); got {src.suffix}.")
            return 2
        out_file = AGENTS.get(n, {}).get("output_file", "")
        dest = (folder / src.name) if out_file.endswith("/") \
            else run / out_file
        shutil.copy2(src, dest)
        if n == 4:
            (folder / "GRABBED-BY.txt").write_text(args.by + "\n", encoding="utf-8")
    sheet_log(run, f"SUBMIT: Step {n} by {args.by} — {dest.name}")
    after = sync_chain(run, actor=args.by, submitted=dest)
    write_status_file()
    if after["kind"] == "agent" and after["step"] == n and after["findings"]:
        print(f"SENT BACK to {after['agent']} — the Step {n} checks failed:")
        for f in after["findings"]:
            print(f"  - {f}")
        print(f"The findings are at the top of steps/{STEP_DIRS[n]}/JOB.md.")
        return 2
    print(f"Submitted Step {n} ({dest.name}) by {args.by} — checks passed. "
          f"Handed to {after['to']}"
          + (f" (Step {after['step']})" if after["step"] else "")
          + (f": {after['what']}" if after["kind"] in ("glam", "done") else "")
          + ".")
    return 0


def jobs_out_path():
    import os
    if os.environ.get("FARM_JOBS_OUT"):
        return Path(os.environ["FARM_JOBS_OUT"]).expanduser()
    return status_out_path().with_name("farm-jobs.json")


def collect_jobs():
    jobs = []
    if RUNS_DIR.is_dir():
        for run in sorted(d for d in RUNS_DIR.iterdir()
                          if d.is_dir() and (d / "config.json").exists()):
            e = open_job_entry(run)
            if e:
                e = dict(e)
                e["run_id"] = load_config(run)["run_id"]
                jobs.append(e)
    return jobs


def write_jobs_file(jobs=None):
    import os
    jobs = collect_jobs() if jobs is None else jobs
    out = jobs_out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps({"generated_at": now_stamp(),
                               "rules_version": RULES.get("version"),
                               "jobs": jobs}, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, out)
    return out, jobs


def cmd_jobs(args):
    if RUNS_DIR.is_dir():
        for run in sorted(d for d in RUNS_DIR.iterdir()
                          if d.is_dir() and (d / "config.json").exists()):
            sync_chain(run)
    out, jobs = write_jobs_file()
    print(f"farm-jobs.json written: {out} ({len(jobs)} open job(s))")
    for j in jobs:
        print(f"  {j['agent']} — {j['run_id']} Step {j['step']} — since "
              f"{j['since']} — needs: {'; '.join(j['needs'])}"
              + (f" — SENT BACK: {j['sent_back'][0]}" if j['sent_back'] else ""))
    if not jobs:
        print("  (no open agent jobs)")
    return 0


def status_out_path():
    import os
    if os.environ.get("FARM_STATUS_OUT"):
        return Path(os.environ["FARM_STATUS_OUT"]).expanduser()
    repo = Path(__file__).resolve().parent.parent
    if (repo / "index.html").exists():
        return repo / "farm-status.json"
    return WORKSPACE / "farm-status.json"


def step_owner(run, n, state):
    if n == 6:
        script = run / "steps" / STEP_DIRS[6] / "script.md"
        if state == "INVALID" or not nonempty_file(script):
            return "Story Agent (writes or fixes the script)"
        return "Mila (script approval)"
    return {
        1: "Indigo (creates the run)",
        2: "TikTok Scout",
        3: "TikTok Shop Agent",
        4: "TikTok Shop Agent (grabs the listing photo)",
        5: "A checker who did not grab the photo",
        7: "Casting agent (Glam's uploaded model), then Mila approves",
        8: "Story Agent + Video Agent (package)",
        9: "Indigo (build)",
        10: "Mila (QC)",
        11: "Glam (lifts the freeze)",
    }.get(n, "")


def run_status_entry(run):
    cfg, results = derive(run)
    head = headline(results)
    open_n, open_name, needs, state = None, "", "", "READY"
    for n, name, st, reason in results:
        if n == 11:
            break
        if st != "CLEARED":
            open_n, open_name, needs = n, name, reason
            state = "STOPPED" if st == "INVALID" else "BLOCKED"
            break
    pick = pick_from_record(run, cfg) or ""
    review = review_entry(run)
    links = watch_links(run)
    builds = files_with_ext(run / "steps" / STEP_DIRS[9], VIDEO_EXTS)
    info = open_job_info(run)
    if open_n is None:
        owner = "Glam (final review; she lifts the freeze)"
        needs = ("Glam's final review — " + (review["review_status"]
                 if review else "waiting for Glam") + ". Freeze on.")
    else:
        owner = step_owner(run, open_n, results[open_n - 1][2])
        if info["kind"] in ("agent", "mila"):
            a = AGENTS.get(info["step"], {})
            owner = info["agent"]
            if info["findings"]:
                state = "STOPPED"
                needs = f"sent back to {info['agent']}: {info['findings'][0]}"
            else:
                state = "BLOCKED"
                needs = f"{info['agent']} — needs: " + "; ".join(a.get("needs", []))
        elif info["kind"] == "glam":
            owner = "Glam"
            needs = f"Glam — {info['what']}"
        br = blocked_report(run, info.get("step")) \
            if info["kind"] in ("agent", "mila") else None
        if br:
            state = "STOPPED"
            needs = (f"{br.get('by', info['agent'])} reported BLOCKED: "
                     f"{br['reason']}")
            head = (f"BLOCKED at Step {info['step']} — {needs} "
                    f"({br.get('at', '')})")
    return {
        "run_id": cfg["run_id"],
        "pick": pick,
        "model": cfg.get("cast_model", ""),
        "mode": cfg.get("mode", ""),
        "account": cfg.get("account", ""),
        "headline": head,
        "state": state,
        "open_step": open_n,
        "open_step_name": open_name,
        "needs": needs,
        "owner": owner,
        "steps": [{"n": n, "name": name, "state": st, "reason": reason,
                   "agent": step_owner(run, n, st)}
                  for n, name, st, reason in results],
        "review_status": review["review_status"] if review else "No build yet",
        "watch_links": [{"file": b.name, "url": links.get(b.name, "")}
                        for b in builds],
        "is_test": bool(re.search(r"TEST|MOCK", pick.upper())),
        "handoffs": read_handoffs(run),
        "open_job": open_job_entry(run, info),
    }


def write_status_file():
    import os
    runs = []
    if RUNS_DIR.is_dir():
        for run in sorted(d for d in RUNS_DIR.iterdir()
                          if d.is_dir() and (d / "config.json").exists()):
            runs.append(run_status_entry(run))
    data = {"generated_at": now_stamp(), "rules_version": RULES["version"],
            "freeze": "ON", "runs": runs}
    out = status_out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, out)
    write_jobs_file([dict(r["open_job"], run_id=r["run_id"])
                     for r in runs if r.get("open_job")])
    publish_status(out)
    return out, data


def cmd_status_export(args):
    out, data = write_status_file()
    print(f"farm-status.json written: {out} ({len(data['runs'])} run(s), "
          f"generated {data['generated_at']})")
    for r in data["runs"]:
        print(f"  {r['run_id']} — {r['state']} — step {r['open_step']} "
              f"{r['open_step_name']} — needs: {r['needs'][:80]} — "
              f"owner: {r['owner']}")
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
    p.add_argument("--pick", default="",
                   help="optional — the Shop Agent picks at Step 3 (pick.md)")
    p.add_argument("--pick-id", default="")
    p.add_argument("--model", default="",
                   help="optional — Glam's uploaded model is picked at Step 7")
    p.add_argument("--mode", default="")
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
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_attach_photo)

    p = sub.add_parser("record-match", help="record the Step 5 Photo Match verdict")
    p.add_argument("run")
    p.add_argument("--checker", required=True)
    p.add_argument("--grabber", required=True)
    p.add_argument("--verdict", required=True, choices=["MATCH", "NO-MATCH"])
    p.add_argument("--notes", default="")
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_record_match)

    p = sub.add_parser("approve-script", help="Mila's Step 6 gate: approve the exact script (or --send-back \"notes\")")
    p.add_argument("run")
    p.add_argument("--by", default="", help="must be Mila")
    p.add_argument("--send-back", default="", help="send the script back to the Story Agent with these notes")
    p.add_argument("--verdict-file", default="", help="Mila's signed verdict file (runner.py mila-sign)")
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_approve_script)

    p = sub.add_parser("mila-sign", help="Mila signs a verdict (only where her key lives)")
    p.add_argument("--run", required=True)
    p.add_argument("--step", type=int, required=True, choices=[6, 7, 10])
    p.add_argument("--verdict", required=True, choices=["APPROVE", "SENDBACK", "PASS", "FAIL", "approve", "sendback", "pass", "fail"])
    p.add_argument("--file", action="append", required=True, help="the exact file(s) checked")
    p.add_argument("--notes", default="")
    p.add_argument("--out", default="")
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_mila_sign)

    p = sub.add_parser("approve-image", help="Mila's Step 7 gate: approve the exact model photo (or --send-back \"notes\")")
    p.add_argument("run")
    p.add_argument("--by", default="", help="must be Mila")
    p.add_argument("--send-back", default="", help="send the photo back to Casting with these notes")
    p.add_argument("--verdict-file", default="", help="Mila's signed verdict file (runner.py mila-sign)")
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_approve_image)

    p = sub.add_parser("submit", help="an agent hands in its step's work; the step's checks run at once and the chain hands off or sends it back")
    p.add_argument("run")
    p.add_argument("--step", type=int, required=True)
    p.add_argument("--by", required=True, help="the agent handing it in (must be that step's agent)")
    p.add_argument("--file", required=True)
    p.add_argument("--session", default=None, help="this agent's own session id (session_...)")
    p.set_defaults(fn=cmd_submit)

    p = sub.add_parser("jobs", help="list every open agent job across runs and write farm-jobs.json")
    p.set_defaults(fn=cmd_jobs)

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
    p.add_argument("--decision", required=True, choices=["approved", "redo", "sent-back"])
    p.add_argument("--notes", default="", help="Glam's notes (required for redo)")
    p.add_argument("--recorded-by", default="Indigo")
    p.set_defaults(fn=cmd_review_decision)

    p = sub.add_parser("review-feed", help="write review-feed.json: the rows for the Farm Video Review page")
    p.set_defaults(fn=cmd_review_feed)

    p = sub.add_parser("review-apply", help="apply Glam's Approve/Redo taps exported from the Farm Video Review page (JSON)")
    p.add_argument("--file", required=True)
    p.set_defaults(fn=cmd_review_apply)

    p = sub.add_parser("sync-rules", help="(retired) the old books are archived; rules live only in farm-rules.json")
    p.set_defaults(fn=cmd_sync_rules)

    p = sub.add_parser("check-rules", help="prove farm-rules.json is complete, placeholders resolve, the page reads it, and nothing reads an archived book")
    p.add_argument("--runner", default=None)
    p.add_argument("--page", default=None)
    p.set_defaults(fn=cmd_check_rules)

    p = sub.add_parser("mila-keygen", help="Mila's own session makes her key pair (private key stays in that session)")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(fn=cmd_mila_keygen)

    p = sub.add_parser("proof", help="show the session id behind every hand-in on a run")
    p.add_argument("run")
    p.set_defaults(fn=cmd_proof)

    p = sub.add_parser("status-export", help="write farm-status.json (every run's live status) for the farm page")
    p.set_defaults(fn=cmd_status_export)

    p = sub.add_parser("report-blocked", help="an agent that can't do its step reports BLOCKED to the board at once (--clear once fixed)")
    p.add_argument("run")
    p.add_argument("--step", type=int, required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--reason", default="")
    p.add_argument("--session", default="")
    p.add_argument("--clear", action="store_true")
    p.set_defaults(fn=cmd_report_blocked)

    p = sub.add_parser("start-request", help="open a run from a farm-requests/*.json file (what a push from Muse runs)")
    p.add_argument("file")
    p.set_defaults(fn=cmd_start_request)

    args = ap.parse_args()
    if args.cmd not in ("check-rules", "mila-sign", "mila-keygen"):
        sync_runs()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
