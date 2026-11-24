# FARM RUNNER — RUNBOOK
*How Indigo operates the TikTok Shop farm runner. Plain language, step by step.*
*Built Nov 24, 2026 (audit F2/F3 fix). The runner lives at `~/workspace/farm-runner/runner.py`.*

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
python3 ~/workspace/farm-runner/runner.py create \
  --pick "Turmeric + Honey Body Oil (Elowen Lab)" --pick-id 1731203941857530625 \
  --model "Tuesday Blue Bob" --mode "Get Ready With Me"
```
Account defaults to @glamorousgrammyglowup. The sheet it writes starts empty — statuses are earned, never pre-written.

### 2. Feed the early steps
- Scout findings → `steps/step2-scout/scout.md` (real, named, dated findings) — **and the story sentence, or Step 2 does not clear.** The file must carry a line starting `Story:` — ONE real sentence in Glam's own voice about who this is for and why they'd care (the way she'd say it to a friend, not how a brand talks). No story line, no handoff: the run waits at Step 2, and the Story Agent sends the handoff back naming what's missing instead of writing a script from listing facts. If the sentence reads like a product label, it doesn't leave the Scout. The runner enforces this with the **SMART STORY CHECK (Glam, Nov 24 — first version, person words spelled out so the check has something concrete to look for)**: (1) a real sentence, at least 5 words; (2) it FAILS on any spec or label word — ml, oz, grams, percent, plant-based, made with, formula, ingredients, or any number at all; (3) it only PASSES if it's about a person — you, her, I, my, she, a mom, a grandma, a friend — and her real moment. A failing sentence leaves the run WAITING at Step 2 with the exact reason on the run ("story sentence failed the check — it names a spec, not a person").
- Pick record → `steps/step3-pick/pick.md` (product name, listing ID/URL, where it was picked).

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
- Script → `steps/step6-script/script.md`. Lines follow the farm's bars: short, camera-only, no claims, and the **hook + soft CTA bar (Glam, Nov 24 — this REPLACES the old blanket "no tap the link")**: every script OPENS with a person-first hook that is SPOKEN OUT LOUD in the video's first 3 seconds — it is the script's first spoken line, built from the Scout's story sentence: a person and her moment, never a product fact. The hook speaks to the VIEWER's moment, never the model's — it never claims "I used it," because the model is AI and never used it; a use claim in the hook is a claim the listing didn't make. The story sentence sitting on file in scout.md does NOT count — if the hook isn't spoken in the first 3 seconds of the video, it isn't there — and carries a soft CTA up top in three places: on screen, the product linked below, and the caption's first line. The soft CTA points down ("it's linked below for you"); the spoken script still never says the words "tap the link," and the closing line still lands on the benefit, never on the CTA. No hook in the first 3 seconds, or no soft CTA up top = send-back. **The runner's Step 6 SCRIPT CHECK enforces the mechanical bars before Glam ever sees the script (Glam + Claude, Nov 24)**: every spoken line ≤8 words; no "tap the link"; no spec/measure words or numbers in spoken lines — the spec list is WIDENED past beauty (Nov 24): fabric percentages and materials, true to size, sizes, stretchy, waterproof, liters, watts, and measures of every kind, so the bars hold for a dress or a bottle, not just the oil; no price, no sold counts; no "I used it" use claims (the model is AI) — including APPLIED ones said sideways, like "has been living on my counter all week," which claims the product lives with her, and the pattern forms: been using / been wearing / reaching for, "my go-to," and "all week / all month" in the model's own voice (in the viewer's moment — "your feet hurt all week" — it's a hook and it passes); the first spoken line must be a person-first hook — a first line that OPENS with the mode name ("Get ready with me — ...") fails as a label, not a hook, no matter what comes after it; and the soft CTA up top must be on file as a `CTA:` line on the script pointing below. A failing script shows INVALID at Step 6 with its findings, and `approve-script` REFUSES to record Glam's approval on one — she judges voice, never specs. Plus the **staging bar** — product stationary (on the counter, no hands on it, clean close-up at the end); a pour or hand-held motion shot is a send-back.
- Show the script to Glam. **Only after she approves it:**
```
python3 ~/workspace/farm-runner/runner.py approve-script <run>
```

### 6. Styled image (Step 7)
Cast photo used as-is → image lands in `steps/step7-styled/`. The product enters every later step as the **listing photo reference** — never described in words.

### 7. Package + lint (Step 8)
Package (VideoExpress prompts, hook, caption) → `steps/step8-package/package.md`. It must carry a `References:` line naming the approved styled image **and** the real listing photo. **CLIP RULE (Glam + Claude, Nov 24): every clip is 8 seconds flat, max 8 spoken words in a clip — four clips make the video. The old 10-second clip shape (and its 18–27 words of dialogue) is RETIRED. The video ends with a 1–2 second clean close-up of the REAL listing photo — kept on purpose: it is what protects the label from being rendered wrong.**
```
python3 ~/workspace/farm-runner/runner.py lint <run>
```
The lint fails the package for: label wording, product description in words (the Nov 24 rule — word prompts make the model invent the product), the retired guard sentence (the new dialogue method is fragments-only direction + isolated quoted lines, per the VideoExpress workflow skill), and handling/motion staging (pour, hand-off, held bottle, raised bottle…) unless `steps/step8-package/staging-proof.md` records a test build that proved that exact staging.

### 8. Build (Step 9)
Build in VideoExpress per the canonical workflow skill, full checklist, Glam's approval gates as usual. Finished build files → `steps/step9-builds/`. **Every** build goes there, good and bad.

### 9. Hand off to QC (Step 10)
```
python3 ~/workspace/farm-runner/runner.py handoff <run>
```
Copies **every** build + the approved script + the listing photo into `~/workspace/farm-qc-handoff/<run-id>/` with a manifest. The builder selects nothing — Mila pulls everything. (The driver also does this automatically when it finds unhanded builds.) Mila checks per the handoff README — frame by frame through the motion, bottle first, ASR diff against the script — and writes `verdict.md` in that folder.

### 10. Collect the verdict
```
python3 ~/workspace/farm-runner/runner.py collect-verdict <run>
```
Copies Mila's verdict into `steps/step10-qc/mila-verdict.md`. Only a PASS signed by Mila clears Step 10. A FAIL stops the run — the build goes back, the run does not advance.

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

## Anytime commands
```
python3 ~/workspace/farm-runner/runner.py status <run>     # the run's true status, derived
python3 ~/workspace/farm-runner/runner.py check <run> --to <step>   # verify all prior gates; fails loudly
python3 ~/workspace/farm-runner/runner.py drive <run>      # advance one run to its next human gate
python3 ~/workspace/farm-runner/runner.py drive-all        # advance every run (what the scheduler calls)
```
`check --to 11` always refuses: Step 11 is freeze-locked.

## What the driver will never do
- Post, schedule a post, or touch TikTok. (No code path exists.)
- Approve a script, pass a QC check, or record a review decision on its own.
- Create a run, invent evidence, or describe the product in words.
- Run a product plan. If a run folder doesn't exist, the driver has nothing to do and says so.

## Verification
The cheat tests (a)–(g) — trying to skip the photo gate, self-sign a match, sneak a word-described pour package past the lint, reach Step 11, fake a finished video without Mila's PASS, and drive past Glam's script approval — are recorded with their results in `~/workspace/farm-runner/VERIFICATION.md`. The mock run they used is `run-2026-11-24-1`, clearly a TEST product, left in place as the worked example.
