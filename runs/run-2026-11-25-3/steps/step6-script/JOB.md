# JOB — Step 6: Story Agent
Run: run-2026-11-25-3 · rules version 2026-11-25n · opened 2026-11-25 21:05 · posting freeze ON

## 🔒 HARD RULE: Products only from TikTok Shop Streamer Desktop
Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

⏱ Time cap: 5 minutes, counted from when you claim the step. At the cap, hand in what you have, or run report-blocked with the reason.

▶ Start by claiming the step (the clock starts then): runner.py claim run-2026-11-25-3 --step 6 --by "Story Agent" --session <your id>. A hand-in past the cap is refused and BLOCKED goes on the board. Claim again to start a fresh try.

## Your job
Write the real-UGC pain-point script INSIDE the farm, built from the Scout's story sentence and the product's approved selling points (farm-data/products/<listing id>/selling-points.md). Check the angle log (farm-data/angle-log.json) so this product's angle and hook don't repeat, and record this video's angle and hook there. Spoken lines go on LINE rows in quotes; add the 'CTA:' line for the soft CTA up top. The script check runs the moment you submit; a failing script comes straight back to you. Then Mila approves with her signed verdict file the exact script (or sends it back with notes).

## Read these (exact files)
- steps/step2-scout/scout.md  (sha256 593331334a96b5b0…)
- steps/step3-pick/pick.md  (sha256 1fee3b43216d6cf7…)
- steps/step4-photo/00.jpg  (sha256 470dccbf175a57f5…)

## Farm laws you follow (from farm-rules.json)
- Products only from TikTok Shop Streamer Desktop: Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.
- Bot check means BLOCKED at once: Any bot or security check on any page (a CAPTCHA, a "Security Check" page, a slider puzzle): never try to solve it and never wait on it. Report BLOCKED at once with the site and the page, and stop that item.
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- No health or beauty claims: Glam's rule (Nov 25), for every product: no health, beauty or results claim in words, anywhere the farm writes: spoken lines, on-screen text, the CTA, the caption or the hashtags. That covers acne, anti-aging, heals, treats, cures, FDA approved, hair growth or regrowth, stops hair loss, any medical or weight-loss claim, and any promised result, even if the listing or the label says it. A claim printed on the real product label, seen in the real listing photo, is not a fail by itself; the farm just never repeats it. The script and caption checks fail a claim before any video is made, and Mila fails any video that says or writes one.
- No before-and-after: Glam's rule (Nov 25), for every product: no before-and-after, shown or implied. No split screens, no 'day 1 vs day 7', no 'after' reveal or hair flip following a use shot, nothing comparing weight or body shape. The script and package checks fail the words; Mila fails the shots.
- Max 12 spoken words a line: Every clip is 8 seconds flat with max 12 spoken words. 4 clips make the video, ending with a 1 to 2 second clean close-up of the REAL listing photo — about 34 seconds.
- Hook in the first 3 seconds: The first spoken line is a person-first hook built from the story sentence, spoken to the viewer's moment, never the model's, and also shown as on-screen text.
- One spoken CTA, at the end: Soft CTA up top: on screen, the product linked below, and the caption's first line. One short spoken CTA in the closing line only, like "tap the orange cart". Never "tap the link".
- No "I used it" claims: The model is AI and never used the product. She can be shown using it, but she never says she used it, for how long, or what it did for her. No results, nothing the listing doesn't say.
- No prices, no sold counts: No prices, discounts, sold counts or invented urgency in any video or caption. The product link shows the live price.
- She can use it, the product stays off frame: Glam's rule (Nov 25), for every product: she can be shown using the product on camera, as many use shots as the video needs, with no proof build: her hands, skin or hair, with the product itself kept out of frame (the oil on her fingers, never the bottle). A bottle, jar, tube, box or any product drawn in an AI clip fails always. No reveal, hair flip or 'after' shot following a use shot: that's a before-and-after.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- It has to feel human: Conversational delivery, natural gestures and head movement, normal blinking. If it looks like a robot, it goes back for a rebuild.
- No dead air: Edits are tightened so there are no long pauses — natural breath beats only. The video moves the way a real person talks.
- Time cap: Scout, weekly lineup and photo finisher 10 minutes, every other job 5: The Scout, the weekly lineup job and the photo finisher job each get a 10-minute cap; every other agent job gets a 5-minute cap. At the cap, a run step hands in what it has, or runs report-blocked with the reason; the weekly lineup and the photo finisher save what they have and stop.
- Agents are the Muse jobs: The agents are the Muse jobs (muse_farm-agent-*). Mila stays out of Muse and is started by the coordinator when a gate opens. No Mila automation.
- Approved selling points: Approved, claim-safe selling points for each product are saved next to its photos (farm-data/products/<listing id>/selling-points.md), with no health or growth claims. Story uses them.
- Angle log: Record the angle and hook each video used per product (farm-data/angle-log.json), so videos don't repeat.
- Farm changes live in the repo first: A farm change lives in the repo first, and Muse jobs only follow what's on main.
- Glam does her own secrets and sign-ins: Glam types her own secrets and does her own sign-ins. No job ever asks for, types or stores a password, code or key.
- Farm data lives in farm-data/: The saved product list, weekly lineup, product photos, selling points, angle log and scorecard live in farm-data/ on main. No job writes them anywhere else.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it. No farm job ever posts to TikTok.

## Hand in
- Output: script.md → steps/step6-script/script.md
- Submit with: runner.py submit run-2026-11-25-3 --step 6 --by "Story Agent" --file <your file> --session <your id>
- <your id> is muse_ followed by YOUR OWN Muse scheduled job's id (a Claude agent uses its session_... id). One id acts as one role per run; the proof lists it for this step.
- Can't do it? Stop, and put it on the board at once: runner.py report-blocked run-2026-11-25-3 --step 6 --by "Story Agent" --reason "what blocked you and why" --session <your id>
- Hands to: Mila (script approval), then Casting / Image Agent

## What this job needs that the runner can't do by itself
- an AI model (Claude, Muse/Indigo or another assigned agent) to do the writing — the runner itself never writes
