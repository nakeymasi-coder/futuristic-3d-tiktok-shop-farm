# JOB — Step 10: Mila
Run: run-2026-11-25-3 · rules version 2026-11-26a · opened 2026-11-26 15:29 · posting freeze ON

## 🔒 HARD RULE: Products only from TikTok Shop Streamer Desktop
Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

⏱ Time cap: 5 minutes, counted from when you claim the step. At the cap, hand in what you have, or run report-blocked with the reason.

▶ Start by claiming the step (the clock starts then): runner.py claim run-2026-11-25-3 --step 10 --by "Mila" --session <your id>. A hand-in past the cap is refused and BLOCKED goes on the board. Claim again to start a fresh try.

## Your job
Check every build in the QC handoff folder frame by frame, bottle first, then the lines word for word against the approved script, using your scorecard. Sign your verdict with runner.py mila-sign (PASS or FAIL, covering the exact build files) and drop it in the Glam Claude Handoff folder; only a signed verdict counts. Your PASS covers only the exact builds you were handed.

## Read these (exact files)
- steps/step9-builds/C01.mp4  (sha256 cf336c3231934dd9…)
- steps/step9-builds/C02.mp4  (sha256 3914e1b45e0b210b…)
- steps/step9-builds/C03.mp4  (sha256 7b4264a40fc0e7d0…)
- steps/step9-builds/C04.mp4  (sha256 1c5b81ae803a8b77…)
- steps/step6-script/script.md  (sha256 600867d52cb3edd6…)
- steps/step4-photo/00.jpg  (sha256 470dccbf175a57f5…)

## Farm laws you follow (from farm-rules.json)
- Products only from TikTok Shop Streamer Desktop: Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. The one exception is a product's listing photos, which may also come from the product's public TikTok Shop listing page (the shop.tiktok.com product page for that listing ID, no sign-in needed). Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.
- Bot check means BLOCKED at once: Any bot or security check on any page (a CAPTCHA, a "Security Check" page, a slider puzzle): never try to solve it and never wait on it. Report BLOCKED at once with the site and the page, and stop that item.
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- No health or beauty claims: Glam's rule (Nov 25), for every product: no health, beauty or results claim in words, anywhere the farm writes: spoken lines, on-screen text, the CTA, the caption or the hashtags. That covers acne, anti-aging, heals, treats, cures, FDA approved, hair growth or regrowth, stops hair loss, any medical or weight-loss claim, and any promised result, even if the listing or the label says it. A claim printed on the real product label, seen in the real listing photo, is not a fail by itself; the farm just never repeats it. The script and caption checks fail a claim before any video is made, and Mila fails any video that says or writes one.
- No before-and-after: Glam's rule (Nov 25), for every product: no before-and-after, shown or implied. No split screens, no 'day 1 vs day 7', no 'after' reveal or hair flip following a use shot, nothing comparing weight or body shape. The script and package checks fail the words; Mila fails the shots.
- Mila checks every step: Mila is in charge of quality control; the maker never checks her own work. A fail goes back to the agent who did it with what's wrong written down.
- Real product only: the AI never draws it: Glam's rule (Nov 25), for every product: the product appears ONLY as its real listing photo, label and all, exactly as the listing shows it, in the clean close-up. The video tool never draws or regenerates a product: no AI clip puts the product in frame, not on a counter, not in a hand, not worn. Prompts never describe the product in words or carry label wording. Any AI clip that shows a drawn product fails.
- Disclosures on: AI-generated label ON and Disclose post content (branded content) ON for every Shop video. Commercially cleared music only on Shop videos.
- Time cap: Scout, weekly lineup, photo finisher and the Video build 10 minutes, every other job 5: The Scout, the weekly lineup job, the photo finisher job and the Video Agent's Step 9 build each get a 10-minute cap; every other agent job gets a 5-minute cap. At the cap, a run step hands in what it has, or runs report-blocked with the reason; the weekly lineup and the photo finisher save what they have and stop.
- Farm changes live in the repo first: A farm change lives in the repo first, and Muse jobs only follow what's on main.
- Glam does her own secrets and sign-ins: Glam types her own secrets and does her own sign-ins. No job ever asks for, types or stores a password, code or key.
- Farm data lives in farm-data/: The saved product list, weekly lineup, product photos, selling points, angle log and scorecard live in farm-data/ on main. No job writes them anywhere else.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it. No farm job ever posts to TikTok.

## Hand in
- Output: verdict.md → steps/step10-qc/mila-verdict.md
- Hand in ONLY by running the Mila sign workflow (mila-sign.yml) with run run-2026-11-25-3, step 10, verdict PASS or FAIL, notes, and your own session id. It signs with the key only it holds and submits for you.
- Can't do it? Stop, and put it on the board at once: runner.py report-blocked run-2026-11-25-3 --step 10 --by "Mila" --reason "what blocked you and why" --session <your id>
- Hands to: Glam (final review on the Farm Video Review page: Approve or Redo with notes; freeze stays on)

## What this job needs that the runner can't do by itself
- Mila (an AI agent that can watch the video frame by frame and hear the audio)

Builds are in ~/workspace/farm-qc-handoff/run-2026-11-25-3/ (HANDOFF.md there carries your full scorecard).
