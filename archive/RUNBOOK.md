# FARM RUNNER — RUNBOOK
*How Indigo operates the TikTok Shop farm runner. Plain language, step by step.*
*Built Nov 24, 2026 (audit F2/F3 fix). The runner lives at `~/workspace/farm-runner/runner.py`.*


## The rules live in ONE file: `farm-rules.json`

Every farm rule — the laws, the 11-step run order, Mila's scorecard, the form options, and every word list and pattern the runner checks — lives in `farm-rules.json` (repo root, or next to runner.py). The runner, Mila's QC handoff, the farm page and the playbook all read it. Nothing keeps its own copy; if the file is missing or broken the runner stops (exit 4).

**How a rule changes now:** Glam approves the change → edit `farm-rules.json` once → run `python3 ~/workspace/farm-runner/runner.py sync-rules` (refreshes the generated rules block in this runbook and in the playbook, plus the playbook's skill prompt) → run `python3 ~/workspace/farm-runner/runner.py check-rules` (proves nothing drifted; non-zero on drift) → the page and the runner already read the file live, and Mila's HANDOFF.md carries the new scorecard and laws on the next run.

=== FARM RULES — generated from farm-rules.json (version 2026-11-25). Do not edit here; edit farm-rules.json and run sync-rules ===
## Farm laws (farm-rules.json, version 2026-11-25)
- Exact products only: Every scene uses the listing's real product photo as the reference. Prompts never describe the product in words or carry label wording. If the render doesn't match the real product, it fails.
- Max 12 spoken words a line: Every clip is 8 seconds flat with max 12 spoken words. Four clips make the video, ending with a 1 to 2 second clean close-up of the REAL listing photo — about 34 seconds.
- Hook in the first 3 seconds: The first spoken line is a person-first hook built from the story sentence, spoken to the viewer's moment, never the model's, and also shown as on-screen text.
- One spoken CTA, at the end: Soft CTA up top: on screen, the product linked below, and the caption's first line. One short spoken CTA in the closing line only, like "tap the orange cart". Never "tap the link".
- No "I used it" claims: The model is AI and never used the product. No use claims, no results, no health or beauty claims, nothing the listing doesn't say.
- No prices, no sold counts: No prices, discounts, sold counts or invented urgency in any video or caption. The product link shows the live price.
- Glam's uploaded models only: Pick the best fit for the product and its buyer: a woman for women's products, a man for men's clothing, either for unisex, and the best-fitting uploaded model for every other category. The photo is used as-is, never generated.
- Product stays put: The product stays stationary with no hands on it. A pour, hand-off, or held or lifted product fails always. Exactly ONE show-it shot is allowed, only after a test build proved it: skincare = Texture shot (on skin, bottle stays on the counter); clothes = fabric moving; shoes = on feet walking; gadget = in use.
- 3 to 5 hashtags, required: Every caption carries 3 to 5 hashtags tied to the product and its niche. Never generic tags like #fyp or #viral.
- Caption keywords: The caption's first line names the product in words buyers search, plus 3 to 5 search words. Add a visible on-screen keyword at posting if the editor allows. Missing keywords = fail.
- Repeats yes, copies no: A product that's selling can repeat any day. Never an identical or near-identical video. Skip sold-out products.
- Disclosures on: AI-generated label ON and Disclose post content (branded content) ON for every Shop video. Commercially cleared music only on Shop videos.
- Mila checks every step: Mila is in charge of quality control; the maker never checks her own work. A fail goes back to the agent who did it with what's wrong written down.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it.
- Can't use it? Stop: If any agent can't use something a step needs, STOP and report BLOCKED: [what] - [why] to Glam. No substitute tools, no workarounds.
## Run order (11 steps)
1. Start a Run — Opens empty; the product is picked at Step 3.
2. TikTok Scout — Real, named findings plus the one story sentence in Glam's voice: who this is for and why they'd care. No sentence, no handoff.
3. TikTok Shop Agent — Picks the product from what's actually selling. A selling product may repeat any day; sold-out products are skipped.
4. Product Photo — The ACTUAL listing photo, the only product description for every later step.
5. Photo Match Check — The grabbed photo matches the pick's name and the listing's own image, checked by someone who did not grab it. A mismatch blocks the run.
6. Story Agent script — Real-UGC pain-point script built from the story sentence; passes the script check; Glam approves the exact script.
7. Model photo — Glam's uploaded model — The best-fitting uploaded model, photo used as-is, never generated. Glam approves.
8. "Next" package — Video Express clip prompts + hook + caption; the model photo and the real listing photo are the references; no product described in words.
9. Video Agent build — Built in Video Express, Realistic Consistent Character workflow. Every build goes to Mila.
10. Checks — Mila's frame-by-frame check and scorecard, then Glam. Mila's PASS covers only the exact builds she was handed.
11. Caption & Post — Only after Glam lifts the @glamorousgrammyglowup posting freeze.
## Mila's scorecard (farm-rules.json, version 2026-11-25)
CRITICAL — automatic fail. Anything that could give Glam a violation is an automatic fail. No exceptions. The critical tier IS the GG skill's compliance rules: if the GG skill bans it, it is critical here. Any one of these and the video is dead; no score saves it:
- Wrong product — what is on screen is not the product in the real listing photo: wrong shape, wrong cap, wrong label, or it morphs mid-clip. The product on screen must match the listing photos exactly in size, shape, color, logo, packaging and details in every frame. If it morphs or drifts at any point, that is an automatic fail.
- Banned health or beauty claims — clears acne, anti-aging, heals, treats, cures, FDA approved, or any medical or weight loss claim, spoken, on screen, or in the caption, even if the listing says it.
- Before-and-after — shown or implied, for skincare, body products, or hair products, or anything comparing weight or body shape in any category.
- A price or a sold count, spoken or on screen.
- Missing AI label or missing disclosure.
- A fake "I used it" claim — the model claiming she used it, wears it, or lives with it when she didn't.
MAJOR — must fix. Any one of these and the video goes back before it can pass:
- Face drifting from the anchor — the model stops looking like the approved model.
- Bad hands.
- Lip sync off.
- No hook in the first three seconds.
- No CTA up top.
- Wrong framing for the category — the shot does not follow the framing rule for that product's category.
- A clip over 12 spoken words, or a clip that is not 8 seconds flat.
- No on-screen hook text in the first three seconds.
- A failed sound-off check — the video would not stop the scroll on mute.
- Hashtags that do not match the product — generic tags like #fyp or #viral, or tags for the wrong product, type, color, or style.
- Caption keywords — the first line of every caption names the product in words people actually search. Indigo also adds a short visible text overlay with that keyword near the top at posting if the editor allows it. If the caption keyword is missing, the post fails and gets fixed before it goes up.
MINOR — scored 1 to 5 each: Pacing. Lighting. Music fit.
PASS BAR: zero criticals, zero majors, and the minor scores average 4 or higher.
SIGN-OFF: Mila signs every video with her score and her notes — what she checked, what she found, and the exact scene and second of anything she failed, with a screenshot attached of anything she fails. Nothing reaches Glam without Mila's sign-off.
## How the product is shown (the only allowed options)
- Let the Story Agent pick
- None — no product on camera
- Worn on her body (clothes, shoes, bags, accessories)
- Sitting on the vanity in front of her
- On the bathroom counter, by the sink
- On the shelf behind her
- On the nightstand
- In the shower / tub setup
- Flat lay on the table
- Beside her — she points and talks, never touches it
- Mirror shot — product on the counter in front of her
- On screen only — the listing photo, nothing in her hands
- One show-it shot (needs a proven test build first)
## Product types
Women's clothing, Men's clothing, Unisex clothing, Shoes, Bag, Accessory, Skincare & beauty, Body care, Hair, Home, Gadget, Other
## Video modes (16)
Problem → Solution, Get Ready With Me, Unboxing Reveal, Nighttime Routine, Bathroom Vanity Demo, Before You Buy, My Honest Take, Restock Day, Comment Reply Video, Side-by-Side Test, Morning Routine, What I Actually Use, Quick Tip, Shelf Tour, First Impression, The Closer Look
=== END FARM RULES ===

## The two laws on the face of this book

1. **THE FREEZE IS ON.** Step 11 (Caption & Post) is freeze-locked in the runner's code. The runner has no posting action of any kind and never will. A finished run ends at **"Ready for Glam — freeze on."** Only Glam lifts the freeze, and she does it outside the runner.
2. **NO AUTO-START, NO PRODUCT PLAN.** The driver runs on demand (`drive` / `drive-all`) or from the scheduled driver job (`tiktok-shop-farm-runner-driver`, every 2 hours — Job Board row 151). Neither the runner nor the job body names a product, a pick, a script, or a schedule of videos. The driver works whatever run folders exist in `~/workspace/farm-runs/`. The tombstoned 4 AM archive is the warning: never hard-code a plan into a job body, never resurrect the old daily-run jobs (Job Board rows 137/138, SCRAPPED Nov 23).

## What the runner is

- A run is a **folder**: `~/workspace/farm-runs/run-<date>-<n>/`. Everything about the run — photo, verdicts, script, package, builds — lives in that folder. The farm page is the checklist and the display; the run folder is the record.
- **Status is derived, never set.** There is no status field and no set-status command. `status` reads the evidence files and computes the truth every time. If a step's evidence isn't in the folder, the step has not happened — no matter what anyone says in a chat.
- **The driver advances automatically** through every step whose evidence is in place, and does the mechanical connective work itself (lint, QC handoff, verdict collection, review manifest). It stops cold at the human gates:
  - **Step 6 — Glam's script approval.** The driver cannot approve a script.
  - **Step 10 — Mila's QC verdict.** Mila is QC owner. The driver hands her every build and cannot check its own work.
  - **Review — Glam's final review.** Finished videos land on the farm's Review section for her verdict.
- Steps whose evidence is produced by agents (scout findings, the pick, the script, the styled image, the package, the VideoExpress build) are placed in the folder by whoever did the work. The driver never fabricates evidence.

## Operating it, step by step

### 1. Create the run
```
python3 ~/workspace/farm-runner/runner.py create
python3 ~/workspace/farm-runner/runner.py create --mode "Get Ready With Me"   # mode optional
```
A run starts **empty**: no product and no model are needed to open it (audit fix, Nov 24). The Scout scouts at Step 2, the Shop Agent picks at Step 3, and the uploaded model is picked at Step 7. `--pick` / `--model` still exist as optional notes, but nothing clears from them. Account defaults to @glamorousgrammyglowup. The sheet it writes starts empty — statuses are earned, never pre-written.

### 2. Feed the early steps
- Scout findings → `steps/step2-scout/scout.md` (real, named, dated findings) — **and the story sentence, or Step 2 does not clear.** The file must carry a line starting `Story:` — ONE real sentence in Glam's own voice about who this is for and why they'd care. No story line, no handoff: the run waits at Step 2. The runner's SMART STORY CHECK: at least 5 words, no spec/label word or number (list: farm-rules.json → checks.spec_words), and about a person (list: farm-rules.json → checks.person_words). A failing sentence leaves the run WAITING at Step 2 with the exact reason.
- Pick record → `steps/step3-pick/pick.md` (a `product:` line with the product name, then listing ID/URL and where it was picked). **This file is the pick** — Step 3 clears from it, and the run sheet, handoff and Review read the product name from it.

### 3. Attach the product photo (Step 4)
```
python3 ~/workspace/farm-runner/runner.py attach-photo <run> <photo-file> --by <who grabbed it>
```
The photo must be the actual listing photo, pulled from the listing itself. No photo in hand = full stop: no scene, no script. The grabber's name is recorded — it matters at the next step.

### 4. Record the Photo Match verdict (Step 5)
The grabbed photo is compared against **the listing's own product image** and the picked product's name, by a checker who did **NOT** grab the photo.
```
python3 ~/workspace/farm-runner/runner.py record-match <run> \
  --checker <name> --grabber <name> --verdict MATCH
```
A verdict signed by the grabber does not count — the derivation refuses it and the run stays stopped at Step 5. A NO-MATCH blocks the run right there.

### 5. Script + Glam's approval (Step 6)
- Script → `steps/step6-script/script.md`, spoken lines on `LINE n:` rows (a `Hook:` row is checked too) and a `CTA:` line pointing below. The rules a script must meet — word cap, hook, one spoken CTA at the end, no use claims, no prices or sold counts, staging — are the farm laws (rule: farm-rules.json → laws). The runner's **Step 6 SCRIPT CHECK** enforces the mechanical bars from farm-rules.json (numbers.max_spoken_words_per_line and the checks.* lists: spec words, use-claim patterns, spoken CTA patterns, banned phrases, mode names, person words) before Glam ever sees it. A failing script shows INVALID at Step 6 with its findings, and `approve-script` REFUSES to record Glam's approval on one — she judges voice, never specs.
- Show the script to Glam. **Only after she approves it:**
```
python3 ~/workspace/farm-runner/runner.py approve-script <run>
```
Her approval is tied to the **exact script she saw** — the runner stores the script's fingerprint (sha256) with her approval. If anyone edits `script.md` afterward, Step 6 goes back to WAITING ("script changed after Glam's approval — needs her approval again") and the driver stops for her again.

### 6. Model photo (Step 7)
Pick from Glam's uploaded models (rule: farm-rules.json → casting). The picked photo lands in `steps/step7-styled/`. The product enters every later step as the **listing photo reference** — never described in words.

### 7. Package + lint (Step 8)
Package (VideoExpress prompts, hook, caption) → `steps/step8-package/package.md`. It must carry a `References:` line naming the approved model photo **and** the real listing photo. Clip rule (rule: farm-rules.json → words); the closing close-up of the REAL listing photo is what protects the label.
```
python3 ~/workspace/farm-runner/runner.py lint <run>
```
The lint fails the package for: label wording, product description in words, the retired guard sentence, and handling/motion staging (rule: farm-rules.json → staging) — the patterns are in farm-rules.json → checks (label_wording_patterns, product_description_*, guard_patterns, staging_patterns, handling_nouns/verbs). It also enforces the clip rule from farm-rules.json → numbers (words per clip, seconds per clip, clips per video). The one declared `Texture shot:` / `Show-it shot:` line is judged by the show-it rules: exactly one, stating the action, with `steps/step8-package/staging-proof.md` (a test build that proved that exact shot) on file first.

### 8. Build (Step 9)
Build in VideoExpress per the canonical workflow skill, full checklist, Glam's approval gates as usual. Finished build files → `steps/step9-builds/`. **Every** build goes there, good and bad.

### 9. Hand off to QC (Step 10)
```
python3 ~/workspace/farm-runner/runner.py handoff <run>
```
Copies **every** build + the approved script + the listing photo into `~/workspace/farm-qc-handoff/<run-id>/` with a manifest. If a verdict is already waiting in that folder, the runner collects it first, so it can only ever count for the builds Mila was actually handed. The builder selects nothing — Mila pulls everything. (The driver also does this automatically when it finds unhanded builds.) Mila checks per the handoff README — frame by frame through the motion, bottle first, ASR diff against the script — and writes `verdict.md` in that folder.

### 10. Collect the verdict
```
python3 ~/workspace/farm-runner/runner.py collect-verdict <run>
```
Copies Mila's verdict into `steps/step10-qc/mila-verdict.md`, records **exactly which build files it covers** (name + fingerprint, in `steps/step10-qc/verdict-covers.json`), and moves her `verdict.md` to `verdict-collected-<time>.md` so it is **collected once and never again**. Only a PASS signed by Mila, covering exactly the builds now in `steps/step9-builds/`, clears Step 10. A FAIL stops the run — the build goes back, the run does not advance. **A new or changed build after her verdict — PASS or FAIL — puts Step 10 back to WAITING** ("new build since Mila's verdict — waiting on her check"); the driver hands the new build to her and nothing shows as finished until she rules on it.

### 11. Review — Glam's landing page
```
python3 ~/workspace/farm-runner/runner.py review-manifest
```
Rebuilds `~/workspace/farm-runner/review-manifest.json` and `review-section.html` from the run folders. Every run with build files appears; a run without Mila's PASS shows **"Not ready — waiting on Mila's check"** and can never show as finished. The farm page's Review section is refreshed from the generated HTML by an artifact edit (Indigo runs it after the manifest changes — see the sync note in `review-section.html`'s companion manifest). Glam's verdict on a finished video:
```
python3 ~/workspace/farm-runner/runner.py review-decision <run> --decision approved
python3 ~/workspace/farm-runner/runner.py review-decision <run> --decision sent-back
```
The runner refuses a decision on any run that hasn't cleared Mila's check. Approval is a review verdict only — **it never posts anything.**

**Watch links (so Glam can actually watch a finished video):** the builds live in the run folder, which a web page can't play. Put each video's Google Drive link in `steps/step9-builds/links.md`, one line per file:
```
build-1.mp4: https://drive.google.com/file/d/…/view
```
`review-manifest` puts a **▶ Watch** link on that video's Review card (and in `review-manifest.json`). A video with no line shows "No watch link yet — add it to links.md." `links.md` is never handed to Mila as a build.

## Anytime commands
```
python3 ~/workspace/farm-runner/runner.py status <run>     # the run's true status, derived
python3 ~/workspace/farm-runner/runner.py check <run> --to <step>   # verify all prior gates; fails loudly
python3 ~/workspace/farm-runner/runner.py drive <run>      # advance one run to its next human gate
python3 ~/workspace/farm-runner/runner.py drive-all        # advance every run (what the scheduler calls)
```
`check --to 11` always refuses: Step 11 is freeze-locked. `--to` takes 2 through 11.

## What the driver will never do
- Post, schedule a post, or touch TikTok. (No code path exists.)
- Approve a script, pass a QC check, or record a review decision on its own.
- Create a run, invent evidence, or describe the product in words.
- Run a product plan. If a run folder doesn't exist, the driver has nothing to do and says so.

## Verification
The cheat tests (a)–(g) — trying to skip the photo gate, self-sign a match, sneak a word-described pour package past the lint, reach Step 11, fake a finished video without Mila's PASS, and drive past Glam's script approval — are recorded with their results in `~/workspace/farm-runner/VERIFICATION.md`. The mock run they used is `run-2026-11-24-1`, clearly a TEST product, left in place as the worked example.
