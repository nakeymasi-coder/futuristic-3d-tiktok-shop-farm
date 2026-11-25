# JOB — Step 7: Casting / Image Agent
Run: run-2026-11-25-1 · rules version 2026-11-25f · opened 2026-11-25 14:50 · posting freeze ON

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

## Your job
Pick the best-fitting model from Glam's uploaded models for this product and its buyer and submit that photo as-is. Never generate a model. Then Mila approves with her signed verdict file it (or sends it back with notes).

## Read these (exact files)
- steps/step6-script/script.md  (sha256 dcb15a000aeb5c21…)
- steps/step3-pick/pick.md  (sha256 08917f41a00e4a34…)
- steps/step4-photo/bask-lather-scalp-stimulator-listing-1729385609961706380.png  (sha256 f4560cb38c7d133a…)
- steps/step4-photo/photo-source.md  (sha256 4e15ec6d5db89ef5…)

## Farm laws you follow (from farm-rules.json)
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Glam's uploaded models only: Pick the best fit for the product and its buyer: a woman for women's products, a man for men's clothing, either for unisex, and the best-fitting uploaded model for every other category. The photo is used as-is, never generated.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.

## Hand in
- Output: the uploaded model photo (an image file) → steps/step7-styled/
- Submit with: runner.py submit run-2026-11-25-1 --step 7 --by "Casting / Image Agent" --file <your file>
- Hands to: Mila (model photo approval), then Story Agent + Video Agent

## What this job needs that the runner can't do by itself
- access to Glam's uploaded model photos
