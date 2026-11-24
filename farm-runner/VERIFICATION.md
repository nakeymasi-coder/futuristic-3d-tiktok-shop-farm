# FARM RUNNER — VERIFICATION (cheat tests)
**Date:** Tuesday, November 24, 2026 · **Runner:** `~/workspace/farm-runner/runner.py`
**Test subject:** mock run `run-2026-11-24-1` — product "MOCK — TEST Product (Test Brand)", model "Mock Model (TEST)". Paper/mock records only: no VideoExpress build, no farm run against TikTok, nothing posted, and the only schedule created is the bookkeeping driver (see Scheduling, below).
**Method:** try to cheat the runner at every gate, in order, and record what it does. A test passes only if the runner refuses or reports the truth.

---

## (a) Status with no photo → must show blocked at Step 4 — ✅ PASS
Mock run created; scout + pick evidence placed; **no photo attached.**
```
HEADLINE: BLOCKED at Step 4 (Product Photo) — no product photo attached — no photo in hand, no scene, no script, full stop
```
Steps 1–3 CLEARED from their evidence; Step 4 WAITING; everything downstream waiting; Step 11 FROZEN. Status came from the files — the run sheet has no status field to edit, and the CLI has no set-status command.

## (b) Advance to Step 6 with a photo but no match verdict → must refuse — ✅ PASS
Photo attached (grabber of record: Indigo). Then:
```
$ runner.py check run-2026-11-24-1 --to 6
CHECK to Step 6: REFUSED — prior gate(s) do not hold:
  Step 5 (Photo Match Check): WAITING — no match verdict recorded — the grabbed photo has not been checked against the listing's own image
exit code: 2
```
The refusal was also written onto the run sheet's GATE LOG.

## (c) Match verdict signed by the grabber → must refuse (checker ≠ grabber) — ✅ PASS
```
$ runner.py record-match run-2026-11-24-1 --checker Indigo --grabber Indigo --verdict MATCH
WARNING: checker == grabber. The derivation will REFUSE to count this verdict — a self-check is not a check.
$ runner.py check run-2026-11-24-1 --to 6
CHECK to Step 6: REFUSED — prior gate(s) do not hold:
  Step 5 (Photo Match Check): INVALID — match verdict was signed by the grabber (Indigo) — the checker must NOT be the person who grabbed the photo; a self-check does not count
exit code: 2
```
Status headline: "STOPPED at Step 5". The cheat verdict stayed on file but counts for nothing. A proper verdict (checker: Mila, grabber: Indigo, compared against the listing's own image) then cleared Step 5 and `check --to 6` returned OK.

## (d) Package with product word-description + pour staging → lint must fail both — ✅ PASS
Fed the Step 8 package the Nov 24 failure recipe verbatim in substance: the retired guard sentence, a BOTTLE block describing the product in words ("the exact product: a tall rectangular clear bottle… the label reads Amococo, TURMERIC… 200ml"), and a pour shot ("she tips the bottle over her open palm and golden oil pools in it; she holds the bottle…").
```
LINT: 6 finding(s):
  [RETIRED GUARD TEXT] line 3
  [LABEL WORDING] line 4
  [PRODUCT DESCRIPTION] line 4
  [PRODUCT DESCRIPTION] line 5
  [STAGING] line 5
  [REFERENCES] package: references do not name the listing photo
LINT RESULT: FAIL — 6 blocking finding(s). Step 8 cannot clear.   exit code: 2
$ runner.py check run-2026-11-24-1 --to 9
CHECK to Step 9: REFUSED — Step 8 (Package): INVALID — package FAILS lint (…)
```
Both required categories — product description in words **and** pour/handling staging — were caught, plus label wording, the retired guard text, and the missing listing-photo reference. A clean package (references-only line naming the styled image + listing photo, bottle on the counter untouched, fragments-only direction) then passed lint with exit 0 and cleared Step 8.

## (e) Try to reach Step 11 → must end at the freeze — ✅ PASS
With every gate 1–10 cleared:
```
$ runner.py check run-2026-11-24-1 --to 11
CHECK to Step 11 REFUSED — Step 11 (Caption & Post) is FREEZE-LOCKED. The posting freeze is ON and the runner has no posting action. A finished run ends at 'Ready for Glam — freeze on.' Only Glam lifts the freeze, outside the runner.
exit code: 3
```
And the run's derived headline is exactly: **"Ready for Glam — freeze on."** There is no post command in the CLI at all — Step 11 cannot be reached because the action does not exist.

## (f) All evidence present but NO Mila PASS → review must show NOT ready — ✅ PASS
Two mock build files placed; driver auto-handed off **every** build (2 files) + approved script + listing photo to `~/workspace/farm-qc-handoff/run-2026-11-24-1/` and stopped at Step 10. With no verdict collected:
```
manifest entry -> run-2026-11-24-1 | Mila: NONE | status: Not ready — waiting on Mila's check | ready_for_review: False
$ runner.py review-decision run-2026-11-24-1 --decision approved
REVIEW DECISION REFUSED — this run has not cleared Mila's check (Step 10)…   exit code: 2
```
The run appears in the review manifest (it has finished build files) but **cannot show as finished** and cannot be approved or sent back before QC. After a mock Mila PASS was placed in the handoff folder, the driver collected it, Step 10 cleared, and the manifest flipped to "Waiting for Glam" (Mila: PASS, ready_for_review: true).

## (g) Automatic driver vs. unapproved script → must stop at the Step 6 gate — ✅ PASS
Script written to the run folder, Glam's approval **not** recorded:
```
$ runner.py drive run-2026-11-24-1
DRIVING run-2026-11-24-1 …
  STOP at Step 6 — human gate: Glam's script approval. The script is written; the driver cannot approve it.
```
The driver stopped cold and logged the stop on the run sheet. (Same behavior verified at Step 10 — "STOP at Step 10 — human gate: Mila's QC verdict" — and at Review — "STOP — human gate: Glam's final review. Freeze on; nothing posts.")

## Full lifecycle, end to end (same mock run) — ✅
create → scout/pick evidence → photo attached → match (independent checker) → script → Glam approval recorded → styled image → clean package (lint pass) → 2 mock builds → drive: auto-handoff → Mila PASS collected → status headline **"Ready for Glam — freeze on."** → review-decision mechanism tested (flips manifest to "Approved") and the test marker then **deleted** — the run stands at "Waiting for Glam", with a correction line in its GATE LOG so no fake approval survives in the record. `drive-all` smoke-tested clean.

## Review landing wiring (manifest → farm Review section)
- `runner.py review-manifest` derives `~/workspace/farm-runner/review-manifest.json` + `review-section.html` from the run folders. The mock entry renders: run id, product, cast model, mode, both video file references, "Mila's verdict: PASS", status "Waiting for Glam", and a TEST badge.
- Farm page edit (artifact `futuristic-3d-tiktok-shop-farm`): ✅ DONE and source-verified by the edit builder — the runner sentence ("Runs are executed by the farm runner from the run folder — status is derived from the evidence in the folder, never set by hand.") appears exactly 2× (both honest-label locations); the "Review — Finished Videos" section sits after the Run Board with the verbatim freeze intro, the `<!-- REVIEW-ENTRIES:BEGIN/END -->` markers, and the exact mock TEST card markup between them; CSS for all nine review classes added in the page's existing style. The builder confirms the previously verified fixes (evidence-derived statuses, staging bar, Mila QC ownership, Run Board rendering) were not touched. Note: the edit is in Glam's Muse copy of the farm; the public share link still serves the previously approved version until a new share is approved.
- **Mock disposition: LEFT IN PLACE, clearly marked TEST** (TEST badge on the card, MOCK product name) so Glam can see the wiring working on the farm. It comes out the first time a real finished video lands, or whenever she says.

## Scheduling (Job Board rule followed)
- **Board checked first** (GLAM HQ Job Board, Sheet `1FpJWpD-i0aMlAqpK7ckf2sthLt5HrGTZONfdxA5qqhs`): row 137 (MUSE-tiktok-shop-ugc-farm-daily-run) SCRAPPED Nov 23, row 138 (Director QC) SCRAPPED Nov 23, row 150 (ChatGPT farm run) CANCELLED Nov 23. Scheduler inventory (137 jobs) holds no TikTok Shop farm runner/driver job — no duplication.
- **Job created:** `tiktok-shop-farm-runner-driver` — every 2 hours, America/New_York, enabled; first run Tue Nov 24, 2026 ~2:50 PM EST. Body is bookkeeping-only: run drive-all + review-manifest and report stops. It names **no product, pick, or plan**, and it forbids creating runs, recording verdicts/approvals, inventing evidence, and posting.
- **Board updated:** new row 151 (MUSE-tiktok-shop-farm-runner-driver … ON), written and read back verified.
- Paste line: TikTok Shop farm runner — automatic driver | Muse (Indigo) | Indigo | every 2 hours | ON

## Honest limits
- The driver automates the connective tissue — derivation, lint, handoff, verdict collection, manifest. It does not scout TikTok, pick products, write scripts, or build videos in VideoExpress; those remain agent steps whose outputs land in the run folder as evidence. Human gates (Glam ×2, Mila ×1) stop it by design.
- Timestamps the runner writes use the VM clock (UTC); dates on run ids use the same clock.

## Cheat test (h) — the story-sentence gate (Nov 24, ~3:13 PM, Emma's fix, Glam: "Okay fix it")
- **Rule added:** Step 2 no longer clears on findings alone. `scout.md` must carry a `Story:` line — one real sentence in Glam's voice, who this is for and why they'd care (≥5 words after the colon). Runner: `story_sentence_on_file()` + new Step 2 derivation; RUNBOOK updated.
- **Test A** (copy of mock run in /tmp, findings only): Step 2 = WAITING — "scout findings on file but NO STORY SENTENCE…"; Steps 3–5 show BLOCKED behind it even though their evidence exists. ✅ Refused.
- **Test B** (same copy + a Story: line added): Step 2 = CLEARED — "scout findings + story sentence on file"; Steps 3–5 clear. ✅
- **Live consequence, stated plainly:** the real run `run-2026-11-24-2` (Turmeric) now derives WAITING at Step 2 — its scout.md never had a story sentence, which is exactly why its Step 6 script came out as label copy and was rejected. The run cannot move until a real story sentence is on its scout file.
- Farm page half of the same fix dispatched the same hour (artifact edit: Scout role text, Start Run prompt opening — person first, Scout QC lines, Story Agent send-back, farm laws).

(i) SMART STORY CHECK (Nov 24, Glam-approved, first version): on a /tmp copy
    of the mock run — a label-copy Story line ("Plant based massage oil made
    with turmeric and honey, two hundred milliliters.") leaves Step 2 WAITING
    with the reason naming the spec word 'milliliters' ("it names a spec,
    not a person"); a real person sentence ("My skin has been dry and tight
    all winter, and I just want to feel soft again.") CLEARS Step 2 with
    "smart story check passed". The old 5-word count alone would have passed
    the label line (9 words); the new check fails it on the spec screen.

(j) STEP 6 SCRIPT CHECK (Nov 24, Glam-approved + Claude's three additions):
    the REAL rejected turmeric script (run-2026-11-24-2, copied to /tmp)
    derives Step 6 INVALID — line-length x3 (18/15/15 spoken words vs the
    8-word bar), spec 'milliliters' on LINE 3, no-cta — and approve-script
    REFUSES to record an approval on it (no glam-approval.md written).
    Probe script: LINE 1 "Get ready with me." alone fails mode-name-hook;
    "I used it every single morning." fails use-claim. A clean 3-line
    script (8/7/6 words, person-first hook, CTA: line pointing below)
    passes the check and takes Glam's approval normally.

(k) SCRIPT CHECK TIGHTENED (Nov 24, Claude's catch): the mode-name bar
    first failed only a first line that was JUST the mode name — but the
    rejected turmeric script OPENS with "Get ready with me — ..." and
    slipped that bar. Bar now fails any first line that OPENS with a mode
    name. "Has been living on my counter all week" added as an applied
    use claim ("living on my" / "has been living"). Retest on the exact
    rejected script: SEVEN findings — line-length x3, use-claim (LINE 1),
    spec 'milliliters', mode-name-hook, no-cta — approval refused. The
    clean test script still passes unchanged.
