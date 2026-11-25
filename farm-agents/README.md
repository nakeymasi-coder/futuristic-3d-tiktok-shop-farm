# Farm agents: each one runs itself (Glam, Nov 25)

Every farm agent is its own Routine. A firing starts a fresh session that does only that agent's step, hands in with its own session id, and fires the next agent. Mila is her own routine too, but she never holds a key: she reviews, then runs the "Mila sign" workflow, which signs with the repo secret MILA_SIGNING_SEED. Nobody plays another agent.

- routines.json: every agent, its step(s), the next agent, and its Routine id once created.
- prompts/: the exact standalone instructions each agent's Routine runs.
- Proof a run was done by the agents themselves: `python3 farm-runner/runner.py proof <run>` lists the session id behind every hand-in. Each id must match that agent's own Routine run record (list_triggers → last_run.session_id). The runner refuses a hand-in with no session, and refuses a session that already played another role on the run.
- Switched OFF: the dispatcher's hourly check stays disabled until Glam says yes. Agent Routines have no schedule and cost nothing until fired.
