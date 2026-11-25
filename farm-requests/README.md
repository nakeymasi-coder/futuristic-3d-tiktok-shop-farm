# Farm requests — how Muse starts a run

Push ONE new file into this folder on `main`, and the "Start a farm run" workflow opens a real run right away. No button press is needed.

- Name it so it's new every time, for example `2026-11-25-bask-lather.json`.
- What goes inside (all three fields are optional):

```json
{"mode": "", "product": "Bask and Lather Scalp Stimulator Oil, Rosemary & Mint", "account": "@glamorousgrammyglowup"}
```

- One new file opens one run. Changing or deleting a file starts nothing, and the same file never opens a second run.
- The run then shows on the Live Run Board, and the first job opens for the TikTok Scout.
- The posting freeze stays on. Opening a run never posts anything.

The red Start Run button (Run workflow on GitHub) still works as a backup.
