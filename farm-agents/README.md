# Farm agents: each one runs itself (Glam, Nov 25)

**Muse runs the farm (Glam, Nov 25: "This is Muse job").** Muse (Indigo) runs each agent as its own scheduled job: TikTok Scout, TikTok Shop Agent, Photo Match checker, Story Agent, Casting / Image Agent and Video Agent.
- Start a run: push a new file into `farm-requests/` on main (see farm-requests/README.md).
- Each job reads farm-jobs.json (after `runner.py status-export`), does only its own step, and hands in with the command in that step's JOB.md, adding `--session muse_<its own Muse job id>`.
- One id acts as one role per run. `runner.py proof <run>` lists the id behind every step, to check against that job's Muse history.
- Stuck? `runner.py report-blocked <run> --step <n> --by "<role>" --reason "..." --session muse_<job id>`. The board shows BLOCKED at once.
- Mila's gates (Steps 6, 7, 10) are not Muse's. Her verdicts count only from the Mila sign workflow with her own Claude session; Muse never holds her key.

The Claude routines below are kept as a backup.

Every farm agent is its own Routine. A firing starts a fresh session that does only that agent's step, hands in with its own session id, and fires the next agent. Mila is her own routine too, but she never holds a key: she reviews, then runs the "Mila sign" workflow, which signs with the repo secret MILA_SIGNING_SEED. Nobody plays another agent.

- routines.json: every agent, its step(s), the next agent, and its Routine id once created.
- prompts/: the exact standalone instructions each agent's Routine runs.
- Proof a run was done by the agents themselves: `python3 farm-runner/runner.py proof <run>` lists the session id behind every hand-in. Each id must match that agent's own Routine run record (list_triggers → last_run.session_id). The runner refuses a hand-in with no session, and refuses a session that already played another role on the run.
- Switched OFF: the dispatcher's hourly check stays disabled until Glam says yes. Agent Routines have no schedule and cost nothing until fired.
