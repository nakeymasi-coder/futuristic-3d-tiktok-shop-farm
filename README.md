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
