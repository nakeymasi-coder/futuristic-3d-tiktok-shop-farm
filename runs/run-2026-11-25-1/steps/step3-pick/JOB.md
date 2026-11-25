# JOB — Step 3: TikTok Shop Agent
Run: run-2026-11-25-1 · rules version 2026-11-25f · opened 2026-11-25 14:13 · posting freeze ON

## 🔒 LOCKED: Locked to your own step, then hand off
Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.

## Your job
Read the Scout's findings and pick the product from what's actually selling in the showcase. A selling product may repeat any day; skip sold-out products. Write the pick record with a 'product:' line (exact listing name) and the listing ID or link.

## Read these (exact files)
- steps/step2-scout/scout.md  (sha256 6432c62f850e75ae…)

## Farm laws you follow (from farm-rules.json)
- Locked to your own step, then hand off: Glam's rule, in her words: "they should hand off automatically to the next agent" and "Nobody should be off trying to do somebody else's job and then get stuck." Each agent does only its own step. The moment its step's output is complete, it hands it in with submit, and the next agent's job opens automatically. No side trips into another step's work: anything a later step needs is that step's job. If you can't finish your own step, stop right away and report BLOCKED: [what] - [why]. Don't search other routes, watch tutorials or stall.
- Repeats yes, copies no: A product that's selling can repeat any day. Never an identical or near-identical video. Skip sold-out products.
- Right listing, checked live: Attach the actual correct product listing — the real one for this product. Before posting, verify in the live listing: title, size chart and availability.
- Can't use it? Stop: If any agent can't use something a step needs, STOP and report BLOCKED: [what] - [why] to Glam. No substitute tools, no workarounds.

## Hand in
- Output: pick.md with a product: line and the listing ID/link → steps/step3-pick/pick.md
- Submit with: runner.py submit run-2026-11-25-1 --step 3 --by "TikTok Shop Agent" --file <your file>
- Hands to: TikTok Shop Agent

## What this job needs that the runner can't do by itself
- the farm's TikTok Shop seller view (kept signed in) to see the showcase, what's selling and what's sold out
