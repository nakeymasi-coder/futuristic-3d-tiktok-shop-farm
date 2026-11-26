# JOB — Step 7: Casting / Image Agent
Run: run-2026-11-25-3 · rules version 2026-11-25n · opened 2026-11-26 14:27 · posting freeze ON

## 🔒 HARD RULE: Products only from TikTok Shop Streamer Desktop
Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

⏱ Time cap: 5 minutes, counted from when you claim the step. At the cap, hand in what you have, or run report-blocked with the reason.

▶ Start by claiming the step (the clock starts then): runner.py claim run-2026-11-25-3 --step 7 --by "Casting / Image Agent" --session <your id>. A hand-in past the cap is refused and BLOCKED goes on the board. Claim again to start a fresh try.

## Your job
Pick the best-fitting model from Glam's uploaded models for this product and its buyer and submit that photo as-is. Never generate a model. Then Mila approves with her signed verdict file it (or sends it back with notes).

## Read these (exact files)
- steps/step6-script/script.md  (sha256 600867d52cb3edd6…)
- steps/step3-pick/pick.md  (sha256 1fee3b43216d6cf7…)
- steps/step4-photo/00.jpg  (sha256 470dccbf175a57f5…)

## Farm laws you follow (from farm-rules.json)
- Products only from TikTok Shop Streamer Desktop: Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.
- Bot check means BLOCKED at once: Any bot or security check on any page (a CAPTCHA, a "Security Check" page, a slider puzzle): never try to solve it and never wait on it. Report BLOCKED at once with the site and the page, and stop that item.
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Glam's uploaded models only: Pick the best fit for the product and its buyer: a woman for women's products, a man for men's clothing, either for unisex, and the best-fitting uploaded model for every other category. The photo is used as-is, never generated.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- Time cap: Scout, weekly lineup and photo finisher 10 minutes, every other job 5: The Scout, the weekly lineup job and the photo finisher job each get a 10-minute cap; every other agent job gets a 5-minute cap. At the cap, a run step hands in what it has, or runs report-blocked with the reason; the weekly lineup and the photo finisher save what they have and stop.
- Agents are the Muse jobs: The agents are the Muse jobs (muse_farm-agent-*). Mila stays out of Muse and is started by the coordinator when a gate opens. No Mila automation.
- Farm changes live in the repo first: A farm change lives in the repo first, and Muse jobs only follow what's on main.
- Glam does her own secrets and sign-ins: Glam types her own secrets and does her own sign-ins. No job ever asks for, types or stores a password, code or key.
- Farm data lives in farm-data/: The saved product list, weekly lineup, product photos, selling points, angle log and scorecard live in farm-data/ on main. No job writes them anywhere else.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it. No farm job ever posts to TikTok.

## Hand in
- Output: the uploaded model photo (an image file) → steps/step7-styled/
- Submit with: runner.py submit run-2026-11-25-3 --step 7 --by "Casting / Image Agent" --file <your file> --session <your id>
- <your id> is muse_ followed by YOUR OWN Muse scheduled job's id (a Claude agent uses its session_... id). One id acts as one role per run; the proof lists it for this step.
- Can't do it? Stop, and put it on the board at once: runner.py report-blocked run-2026-11-25-3 --step 7 --by "Casting / Image Agent" --reason "what blocked you and why" --session <your id>
- Hands to: Mila (model photo approval), then Story Agent + Video Agent

## What this job needs that the runner can't do by itself
- access to Glam's uploaded model photos
