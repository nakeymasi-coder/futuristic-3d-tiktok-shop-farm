# JOB — Step 9: Video Agent
Run: run-2026-11-25-3 · rules version 2026-11-25n · opened 2026-11-26 14:44 · posting freeze ON

## 🔒 HARD RULE: Products only from TikTok Shop Streamer Desktop
Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

⏱ Time cap: 5 minutes, counted from when you claim the step. At the cap, hand in what you have, or run report-blocked with the reason.

▶ Start by claiming the step (the clock starts then): runner.py claim run-2026-11-25-3 --step 9 --by "Video Agent" --session <your id>. A hand-in past the cap is refused and BLOCKED goes on the board. Claim again to start a fresh try.

## Your job
Build the video in Video Express with the Realistic Consistent Character workflow from the package and the approved model photo. The AI clips never show the product; the real listing photo goes in only as the 1-2 second clean close-up. Every clip is 8 seconds flat; the runner measures each build before Mila sees it. Submit EVERY build, good or bad; the builder never checks her own work.

## Read these (exact files)
- steps/step8-package/package.md  (sha256 5e45f48d99d38954…)
- steps/step7-styled/casting-pick-run-2026-11-25-3.jpg  (sha256 26baf9a35a9b4033…)
- steps/step7-styled/model-thursday-pink-blonde.jpg  (sha256 26baf9a35a9b4033…)
- steps/step4-photo/00.jpg  (sha256 470dccbf175a57f5…)

## Farm laws you follow (from farm-rules.json)
- Products only from TikTok Shop Streamer Desktop: Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.
- Bot check means BLOCKED at once: Any bot or security check on any page (a CAPTCHA, a "Security Check" page, a slider puzzle): never try to solve it and never wait on it. Report BLOCKED at once with the site and the page, and stop that item.
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- No health or beauty claims: Glam's rule (Nov 25), for every product: no health, beauty or results claim in words, anywhere the farm writes: spoken lines, on-screen text, the CTA, the caption or the hashtags. That covers acne, anti-aging, heals, treats, cures, FDA approved, hair growth or regrowth, stops hair loss, any medical or weight-loss claim, and any promised result, even if the listing or the label says it. A claim printed on the real product label, seen in the real listing photo, is not a fail by itself; the farm just never repeats it. The script and caption checks fail a claim before any video is made, and Mila fails any video that says or writes one.
- No before-and-after: Glam's rule (Nov 25), for every product: no before-and-after, shown or implied. No split screens, no 'day 1 vs day 7', no 'after' reveal or hair flip following a use shot, nothing comparing weight or body shape. The script and package checks fail the words; Mila fails the shots.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- Max 12 spoken words a line: Every clip is 8 seconds flat with max 12 spoken words. 4 clips make the video, ending with a 1 to 2 second clean close-up of the REAL listing photo — about 34 seconds.
- She can use it, the product stays off frame: Glam's rule (Nov 25), for every product: she can be shown using the product on camera, as many use shots as the video needs, with no proof build: her hands, skin or hair, with the product itself kept out of frame (the oil on her fingers, never the bottle). A bottle, jar, tube, box or any product drawn in an AI clip fails always. No reveal, hair flip or 'after' shot following a use shot: that's a before-and-after.
- It has to feel human: Conversational delivery, natural gestures and head movement, normal blinking. If it looks like a robot, it goes back for a rebuild.
- No dead air: Edits are tightened so there are no long pauses — natural breath beats only. The video moves the way a real person talks.
- Disclosures on: AI-generated label ON and Disclose post content (branded content) ON for every Shop video. Commercially cleared music only on Shop videos.
- Time cap: Scout, weekly lineup and photo finisher 10 minutes, every other job 5: The Scout, the weekly lineup job and the photo finisher job each get a 10-minute cap; every other agent job gets a 5-minute cap. At the cap, a run step hands in what it has, or runs report-blocked with the reason; the weekly lineup and the photo finisher save what they have and stop.
- Agents are the Muse jobs: The agents are the Muse jobs (muse_farm-agent-*). Mila stays out of Muse and is started by the coordinator when a gate opens. No Mila automation.
- Farm changes live in the repo first: A farm change lives in the repo first, and Muse jobs only follow what's on main.
- Glam does her own secrets and sign-ins: Glam types her own secrets and does her own sign-ins. No job ever asks for, types or stores a password, code or key.
- Farm data lives in farm-data/: The saved product list, weekly lineup, product photos, selling points, angle log and scorecard live in farm-data/ on main. No job writes them anywhere else.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it. No farm job ever posts to TikTok.

## Hand in
- Output: the build video file(s) → steps/step9-builds/
- Submit with: runner.py submit run-2026-11-25-3 --step 9 --by "Video Agent" --file <your file> --session <your id>
- <your id> is muse_ followed by YOUR OWN Muse scheduled job's id (a Claude agent uses its session_... id). One id acts as one role per run; the proof lists it for this step.
- Can't do it? Stop, and put it on the board at once: runner.py report-blocked run-2026-11-25-3 --step 9 --by "Video Agent" --reason "what blocked you and why" --session <your id>
- Hands to: Mila

## What this job needs that the runner can't do by itself
- Video Express in the farm's browser (kept signed in) to build the video
