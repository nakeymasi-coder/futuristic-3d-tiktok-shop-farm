# JOB — Step 3: TikTok Shop Agent
Run: run-2026-11-25-3 · rules version 2026-11-25k · opened 2026-11-25 17:32 · posting freeze ON

## 🔒 HARD RULE: Products only from TikTok Shop Streamer Desktop
Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

⏱ Time cap: 5 minutes, counted from when you claim the step. At the cap, hand in what you have, or run report-blocked with the reason.

▶ Start by claiming the step (the clock starts then): runner.py claim run-2026-11-25-3 --step 3 --by "TikTok Shop Agent" --session <your id>. A hand-in past the cap is refused and BLOCKED goes on the board. Claim again to start a fresh try.

## Your job
Pick the day's product from this week's lineup (farm-data/weekly-lineup.json). Start with the stock and price check: a sold-out product gets skipped and the next one is picked. Write the pick record with a 'product:' line (exact listing name) and the listing ID or link.

## Read these (exact files)
- steps/step2-scout/scout.md  (sha256 593331334a96b5b0…)

## Farm laws you follow (from farm-rules.json)
- Products only from TikTok Shop Streamer Desktop: Anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself.
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Repeats yes, copies no: A product that's selling can repeat any day. Never an identical or near-identical video. Skip sold-out products.
- Right listing, checked live: Attach the actual correct product listing — the real one for this product. Before posting, verify in the live listing: title, size chart and availability.
- Can't use it? Stop: If any agent can't use something a step needs, STOP and report BLOCKED: [what] - [why] to Glam. No substitute tools, no workarounds.
- Time cap: Scout 10 minutes, every other job 5: The Scout gets a 10-minute cap; every other agent job gets a 5-minute cap. At the cap, it hands in what it has, or runs report-blocked with the reason.
- Agents are the Muse jobs: The agents are the Muse jobs (muse_farm-agent-*). Mila stays out of Muse and is started by the coordinator when a gate opens. No Mila automation.
- Shop job picks from the lineup: The Shop job (Steps 3-4) picks the day's product from the weekly lineup and uses its saved photos.
- Weekly lineup: Once a week, pick that week's products to promote from the saved list (in-stock best sellers). Glam's turmeric products are ALWAYS included every week and can run daily. Save it in the repo (farm-data/weekly-lineup.json).
- Stock and price check first: A stock and price check runs at the start of each run. A sold-out product gets skipped and the next one is picked.
- Farm changes live in the repo first: A farm change lives in the repo first, and Muse jobs only follow what's on main.
- How best sellers are ranked: Best-seller ranking uses scorecard sales first, then past farm runs, then Scout trends.
- Glam does her own secrets and sign-ins: Glam types her own secrets and does her own sign-ins. No job ever asks for, types or stores a password, code or key.
- Farm data lives in farm-data/: The saved product list, weekly lineup, product photos, selling points, angle log and scorecard live in farm-data/ on main. No job writes them anywhere else.
- Posting freeze ON: Nothing posts while the @glamorousgrammyglowup freeze is on. Only Glam lifts it. No farm job ever posts to TikTok.

## Hand in
- Output: pick.md with a product: line and the listing ID/link → steps/step3-pick/pick.md
- Submit with: runner.py submit run-2026-11-25-3 --step 3 --by "TikTok Shop Agent" --file <your file> --session <your id>
- <your id> is muse_ followed by YOUR OWN Muse scheduled job's id (a Claude agent uses its session_... id). One id acts as one role per run; the proof lists it for this step.
- Can't do it? Stop, and put it on the board at once: runner.py report-blocked run-2026-11-25-3 --step 3 --by "TikTok Shop Agent" --reason "what blocked you and why" --session <your id>
- Hands to: TikTok Shop Agent

## What this job needs that the runner can't do by itself
- TikTok Shop Streamer Desktop / LIVE Manager (Glam signs it in herself) for the stock and price check on the picked product
