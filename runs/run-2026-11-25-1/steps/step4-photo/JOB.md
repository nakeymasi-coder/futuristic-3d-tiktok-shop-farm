# JOB — Step 4: TikTok Shop Agent
Run: run-2026-11-25-1 · rules version 2026-11-25f · opened 2026-11-25 14:40 · posting freeze ON

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

## Your job
Pull the ACTUAL listing photo for the picked product from the listing itself and submit it. It becomes the only product description for every later step. No photo in hand = full stop.

## Read these (exact files)
- steps/step3-pick/pick.md  (sha256 08917f41a00e4a34…)

## Farm laws you follow (from farm-rules.json)
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- Can't use it? Stop: If any agent can't use something a step needs, STOP and report BLOCKED: [what] - [why] to Glam. No substitute tools, no workarounds.

## Hand in
- Output: the real listing photo (an image file) → steps/step4-photo/
- Submit with: runner.py submit run-2026-11-25-1 --step 4 --by "TikTok Shop Agent" --file <your file>
- Hands to: Photo Match checker

## What this job needs that the runner can't do by itself
- the farm's TikTok Shop view of the listing (kept signed in) to save its real product photo
