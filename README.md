# Futuristic 3D TikTok Shop Farm

Glam's TikTok Shop agent farm. **Live page:** https://nakeymasi-coder.github.io/futuristic-3d-tiktok-shop-farm/

The live page only changes after Glam approves the change.

## The farm is three things, and everything is in plain view

1. **`farm-rules.json` — the master rules file.** Every farm rule lives here and only here: the laws, the 11-step run order, Mila's scorecard, the form options and modes, the numbers (words a line, clip seconds, hashtags), and every word list and pattern the runner checks. The farm page shows the whole file, readable, so everyone sees the same rules.
2. **`farm-runner/runner.py` — the farm code.** It runs the farm from evidence in each run's folder, checks every gate, and never posts.
3. **`index.html` — the farm page.** It reads `farm-rules.json` live and shows every run's live status on the **Live Run Board** (from `farm-status.json`), step by step, including what is BLOCKED, what it needs and who acts next.

Also kept: this README (the operator guide), `manifest.webmanifest` and the icons (`icon-512.png`, `icon-192.png`, `apple-touch-icon.png`, `favicon-32.png`), and `farm-runner/fixcheck.sh` (the full test run).

**Archive (read-only):** the old playbook, runbook and test log are kept, never deleted, at https://github.com/nakeymasi-coder/futuristic-3d-tiktok-shop-farm/tree/main/archive. Nothing reads its rules from there.

## How a rule changes now

Glam approves → edit `farm-rules.json` once → run `python3 farm-runner/runner.py check-rules` → the page and the runner read it live, and Mila's handoff carries it on the next run.

Numbers live once, in `"numbers"`. A law that says `{max_spoken_words_per_line}` is filled from there, so changing a number changes every sentence that uses it. `check-rules` fails if a `{placeholder}` has no number, if the page stops reading the rules or status file, or if anything reads an archived book.

## Deploy note

`farm-rules.json` must sit next to `runner.py`, in the folder above it, or in `~/workspace/` (or set `FARM_RULES` to its path). Without it, the runner stops with exit 4 and a plain message. It never falls back to an old copy. Copy `farm-rules.json` together with `runner.py` whenever the runner is updated.

## The 9 agents

1. TikTok Scout
2. TikTok Shop Agent
3. Story Agent
4. Casting / Image Agent
5. Video Agent (Video Express)
6. Indigo (Builder & Handoff)
7. Caption & Post Agent
8. Mila (Quality Control)
9. TikTok Live Game Agent (A-09, LIVE ONLY): builds live games only from the real people engaging on Glam's live.

## How the chain runs

One agent does its step and hands it to the next, in Glam's order. Nobody passes work along by chat.

TikTok Scout → TikTok Shop Agent (pick, then the real listing photo) → Photo Match checker (not the grabber) → Story Agent (script) → **Mila approves the script** → Casting / Image Agent (her uploaded model photo) → **Mila approves the photo** → Story Agent + Video Agent ("Next" package with caption) → Video Agent / Indigo (build) → Mila (QC) → **Glam's final review: Approve or Redo with notes**. Step 11 stays frozen; nothing posts.

Glam, Nov 25: "Don't wait for my approval to make the video." Nothing before the video waits on Glam. She rules once, on the finished video, on the [Farm Video Review page](https://claude.ai/artifact/9oFBb5aLg1rrm23B96Rt3w).

- **Jobs:** when a step clears, the runner opens the next agent's job as `steps/<step>/JOB.md`. The job text, the laws that agent follows and what it needs all come from `farm-rules.json → agents`. JOB.md also lists the exact input files with their sha256.
- **Finding your work:** `python3 farm-runner/runner.py jobs` lists every open job and writes `farm-jobs.json` next to `farm-status.json`.
- **Starting a run:** Muse pushes a new file into `farm-requests/` on main, and the run opens (see `farm-requests/README.md`). The Start Run button still works.
- **Handing in:** `python3 farm-runner/runner.py submit <run> --step N --by "<agent>" --file <your file> --session <your id>`. Step 5 uses `record-match` instead. The step's checks run at once (story check, script check, lint and caption).
  - **Your id:** a Muse job passes `muse_` followed by its own Muse scheduled job's id; a Claude agent passes its `session_...` id. One id plays one role per run, and `runner.py proof <run>` lists the id behind every step. Mila's gates take only her signed verdict from the Mila sign workflow.
  - **Stuck?** `runner.py report-blocked <run> --step N --by "<agent>" --reason "..." --session <your id>` puts BLOCKED on the board at once.
  - If they pass, the next agent's job opens, or Glam's or Mila's gate.
  - If they fail, the work is **sent back** to the same agent with the findings at the top of its JOB.md.
  - `--by` must be that step's agent, and a step out of order is refused.
- **Mila's gates before the video:** `approve-script <run> --by Mila` and `approve-image <run> --by Mila` (add `--send-back "notes"` to send it back). Each approval is tied to the exact file she saw. Anyone else is refused.
- **Glam's one gate, the finished video:** `review-decision <run> --decision approved` or `--decision redo --notes "..."`. A redo keeps the old build and Mila's verdict in `redo/redo-N/` and reopens the Video Agent's job with her notes at the top; Mila checks the rebuild.
- **The review page:** `review-feed` writes `review-feed.json`, the rows the Farm Video Review page shows (copy them into its `videos` list). Her taps are saved on the page; export them as JSON and run `review-apply --file <taps.json>` (each tap applies once).
- **Every hop is logged** in the run folder's `handoffs.jsonl` (who, when, what, the inputs used with sha256, the output, and the result). It also appears in `farm-status.json`, so the page's Live Run Board shows every handoff and the open job.
- **Who does each job.** The runner opens each job and checks the work; the agents do it. A run shows the agent as up next until it hands in its work:
  - **TikTok Scout:** the farm's TikTok browser (Glam keeps it signed in) for the Shop showcase, best sellers and trends, plus an AI agent to write.
  - **TikTok Shop Agent:** the farm's TikTok Shop seller view, to see what's selling and what's sold out, and to save the real listing photo.
  - **Photo Match checker:** someone who did not grab the photo, comparing it to the live listing.
  - **Story Agent and the package:** an AI agent to write. The runner never writes.
  - **Casting / Image Agent:** Glam's uploaded model photos.
  - **Video Agent:** Video Express in the farm's browser.
  - **Mila:** watches the video frame by frame and hears the audio.
- **Safety net:** if a sign-in screen ever appears, the agent stops and reports BLOCKED: sign-in needed. It never works around it.

The runner never writes an agent's work, never calls an AI or a website, and never posts.

## Operating the runner, step by step

The two laws: **the posting freeze is ON** (Step 11 is locked in code; the runner has no posting action, and only Glam lifts the freeze, outside the runner), and **no product plan** (the runner and the 2-hourly driver job never name a product; they only work the run folders that exist).

A run is a folder: `~/workspace/farm-runs/run-<date>-<n>/`. Status is **derived from the evidence in that folder, never set by hand**. If a step's evidence isn't there, the step hasn't happened.

Commands below are shown as `runner.py`; the live copy is `python3 ~/workspace/farm-runner/runner.py`.

1. **Create the run:** `runner.py create` (optional `--mode "Get Ready With Me"`). A run starts empty; the product is picked at Step 3 and the model at Step 7.
2. **Scout (Step 2):** put real, named findings in `steps/step2-scout/scout.md` with a `Story:` line, one real sentence in Glam's voice about who this is for and why they'd care. No passing story sentence, no handoff.
3. **Pick (Step 3):** `steps/step3-pick/pick.md` with a `product:` line. This file is the pick.
4. **Listing photo (Step 4):** `runner.py attach-photo <run> <photo-file> --by <who grabbed it>`. It must be the real listing photo.
5. **Photo match (Step 5):** `runner.py record-match <run> --checker <name> --grabber <name> --verdict MATCH` (or `NO-MATCH`). The checker can't be the person who grabbed the photo.
6. **Script (Step 6):** `steps/step6-script/script.md` with spoken lines on `LINE n:` rows (a `Hook:` row is checked too) and a `CTA:` line pointing below. The script check runs the laws from `farm-rules.json`. Mila approves it with `runner.py approve-script <run> --by Mila` (or sends it back with `--send-back "notes"`). Her approval is tied to the exact script; any edit after that needs her approval again.
7. **Model photo (Step 7):** Glam's best-fitting uploaded model photo, used as-is, goes in `steps/step7-styled/`.
8. **Package (Step 8):** `steps/step8-package/package.md` with a `References:` line naming the approved model photo and the real listing photo. Check it with `runner.py lint <run>`.
9. **Build (Step 9):** every Video Express build goes in `steps/step9-builds/`, good and bad. Put each video's Google Drive link in `steps/step9-builds/links.md` (`build-1.mp4: https://drive.google.com/...`) so it can be watched from the page.
10. **Hand off to Mila (Step 10):** `runner.py handoff <run>` copies every build, the approved script and the listing photo to `~/workspace/farm-qc-handoff/<run-id>/`, with a `HANDOFF.md` that carries Mila's full scorecard and the farm laws from `farm-rules.json`. Mila writes `verdict.md` there.
11. **Collect the verdict:** `runner.py collect-verdict <run>` collects it once, records exactly which builds it covers, and moves it to `verdict-collected-<time>.md`. A new or changed build waits on Mila again.
12. **Review:** `runner.py review-manifest` rebuilds the review list. Glam's verdict is recorded with `runner.py review-decision <run> --decision approved` or `--decision redo --notes "..."`, or from her taps on the review page with `review-apply`. Approval never posts.

Anytime:

- `runner.py status <run>`: the run's true status, derived.
- `runner.py check <run> --to <step>`: verifies every earlier gate (2 through 11; 11 always refuses, freeze).
- `runner.py drive <run>` / `runner.py drive-all`: advance runs to their next human gate (`drive-all` is what the scheduler calls).
- `runner.py status-export`: writes `farm-status.json` for the page's Live Run Board.
- `runner.py check-rules`: proves the rules file is complete and nothing reads an archived book.

`status`, `drive`, `drive-all`, `review-manifest` and `review-decision` also rewrite `farm-status.json`. It goes next to the page when the runner sits in this repo, otherwise to `~/workspace/farm-status.json` (or wherever `FARM_STATUS_OUT` points).

What the driver never does: post or touch TikTok, approve a script, pass a QC check, record Glam's decision, create a run, invent evidence, or run a product plan.

## Testing

`bash farm-runner/fixcheck.sh` runs every check in a scratch folder (never your real run folders) and prints a pass/fail summary.

By Glam Hustle Hub.

## Farm brain changelog

### 2026-11-25 (rules version 2026-11-25h), approved by Glam on the call
1. **Time cap:** every agent job gets a 5-minute cap (the Scout's is now 10, see item 13). At the cap, it hands in what it has, or runs report-blocked with the reason.
2. **Scout:** a trends-only quick check, capped at 5 minutes, at Step 2. It does not page the showcase.
3. **Saved product list:** a saved showcase product list in the repo (name, sold count, in stock), refreshed once a day, not every run. No job pages all 264 products per run. File: `farm-data/showcase-products.json`.
4. **Weekly lineup:** once a week, pick that week's products to promote from the saved list (in-stock best sellers). Glam's turmeric products are ALWAYS included every week and can run daily. File: `farm-data/weekly-lineup.json`.
5. **Photos ahead:** each lineup product's real listing photos are pulled once and saved with the lineup (`farm-data/products/<listing id>/`). If a photo won't download, that product is BLOCKED with the reason. Never use a drawn or substituted photo.
6. **Shop job:** Steps 3-4 pick the day's product from the weekly lineup and use its saved photos.
7. **Selling points:** approved, claim-safe selling points for each product are saved next to its photos (`selling-points.md`), with no health or growth claims. Story uses them.
8. **Stock and price check** at the start of each run. A sold-out product gets skipped and the next one is picked.
9. **Angle log:** record the angle and hook each video used per product, so videos don't repeat. File: `farm-data/angle-log.json`.
10. **Scorecard:** track which videos worked and which didn't (views, watch time, sales where visible) and each one's formula (hook, angle, format), so winners get repeated. It starts from existing @glamorousgrammyglowup stats, read only. The posting freeze stays ON. File: `farm-data/scorecard.json`.
11. **Agents are the Muse jobs** (`muse_farm-agent-*`). Mila stays out of Muse and is started by the coordinator when a gate opens (the free stopgap). No Mila automation.

12. **HARD RULE, products only from Streamer Desktop** (rules version 2026-11-25i): anything about Glam's products (the showcase, best sellers, stock, listing photos and product sales) comes ONLY from TikTok Shop Streamer Desktop / LIVE Manager, because her regular TikTok can't show those. Her regular TikTok is allowed for trends and general video views. If Streamer Desktop needs a sign-in, the job reports BLOCKED and Glam signs in herself. It's the first law in `farm-rules.json`, at the top of every JOB.md and at the top of every agent prompt.

13. **Time cap update** (rules version 2026-11-25j): the Scout gets 10 minutes, and all other jobs stay at 5.
14. **Photo finisher job:** it works through the lineup's blocked photos a few at a time, turmeric staples first, and skips any already saved. It stays inside 5 minutes per run and saves real listing photos only. A photo that won't download stays BLOCKED with the reason. Prompt: `farm-agents/prompts/photo-finisher.md`, listed in `farm-agents/routines.json` under `support_jobs`.
15. **Facts Indigo found:** the showcase page shows no sold counts. Best-seller ranking uses scorecard sales first, then past farm runs, then Scout trends.
16. **Repo first:** a farm change lives in the repo first, and Muse jobs only follow what's on main.

17. **Muse job ids:** the six agents are `muse_farm-agent-scout`, `-shop`, `-photo-match`, `-story`, `-casting` and `-video`, recorded per agent in `farm-agents/routines.json` (`muse_job`). Mila has none; she stays out of Muse.
18. **Muse support jobs:** the showcase list refresh (once a day) and the weekly lineup (every Monday), which Indigo created in Muse, plus the photo finisher. They're recorded in `farm-agents/routines.json` under `support_jobs`.
19. **Farm data home:** Indigo's files from the top folder (angle-log.json, scorecard.json, showcase-products.json, weekly-lineup.json) moved into `farm-data/`. From now on every job writes them only in `farm-data/`.
20. **Posting freeze and sign-ins:** the posting freeze stays ON and no farm job ever posts to TikTok. Glam types her own secrets and does her own sign-ins.

21. **Time caps are enforced by the farm** (rules version 2026-11-25k): Muse can't hard-stop a job, so each job now claims its step first (`runner.py claim <run> --step N --by "<role>" --session <id>`) and the clock starts then. A hand-in past the cap (Scout 10 minutes, every other job 5) is refused and BLOCKED "time cap reached" goes on the board. Every status export also files that BLOCKED for a claim past its cap with nothing handed in. Claiming again starts a fresh try. Mila's gates aren't Muse jobs and keep the written cap only.
22. **The pick must be a real showcase product:** the runner checks the pick (listing ID or name) against `farm-data/showcase-products.json`. A pick that isn't there stops Step 3 with BLOCKED and the reason. Nothing is swapped or replaced automatically. A preset pick that isn't in the list shows that note on the board too.
23. **No duplicate run names:** a run name exists only once. A copy made on one computer that was never on the shared farm is moved aside to `workspace/farm-runs-retired/` (kept, not deleted) and the shared run is used. A new run can't start when the shared farm can't be read. While a run is in conflict, the board shows the shared copy, not the local one.
24. **The old local copy of run-2026-11-25-2:** it was archived on Indigo's machine (not on the farm) and its angle-log entry was removed (commit b1b6d7f). Its "Step 6 passed" does not count.
25. **Runs 2026-11-25-2 and 2026-11-25-3** are both at Step 2 waiting on the Scout. Nothing in the code blocks a Scout refire on either: a new claim starts a fresh try and clears an old time-cap BLOCKED.
26. **Weekly lineup and photo finisher get 10 minutes** (rules version 2026-11-25l): Glam raised both Muse support jobs to a 10-minute cap. The Scout stays at 10 and every other job stays at 5. At the cap, each saves what it has and stops.

Where it lives: each rule is a law in `farm-rules.json`, so every JOB.md prints it. The Scout, Shop and Story job texts, the agent prompts and `farm-data/README.md` all carry it too.
