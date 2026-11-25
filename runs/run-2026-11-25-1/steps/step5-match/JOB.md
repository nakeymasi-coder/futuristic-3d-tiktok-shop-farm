# JOB — Step 5: Photo Match checker
Run: run-2026-11-25-1 · rules version 2026-11-25f · opened 2026-11-25 14:42 · posting freeze ON

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

## Your job
Compare the grabbed photo against the listing's own product image and the picked product's name. Record MATCH or NO-MATCH with record-match. You must not be the person who grabbed the photo. A mismatch blocks the run.

## Read these (exact files)
- steps/step4-photo/bask-lather-scalp-stimulator-listing-1729385609961706380.png  (sha256 f4560cb38c7d133a…)
- steps/step3-pick/pick.md  (sha256 08917f41a00e4a34…)

## Farm laws you follow (from farm-rules.json)
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- Mila checks every step: Mila is in charge of quality control; the maker never checks her own work. A fail goes back to the agent who did it with what's wrong written down.

## Hand in
- Output: match-verdict.md (written by record-match) → steps/step5-match/match-verdict.md
- Submit with: runner.py record-match run-2026-11-25-1 --checker <you> --grabber <grabber> --verdict MATCH|NO-MATCH
- Hands to: Story Agent

## What this job needs that the runner can't do by itself
- someone other than the grabber who can open the live listing to compare
