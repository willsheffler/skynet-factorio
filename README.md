# skynet-factorio

AI bot infrastructure for Factorio multiplayer co-play. Will + kids host games; bot
joins as a third player.

**Status:** Phase 0 scaffolding (2026-05-21). Not yet runnable.

## Borrow-and-fork posture

Per Will's directive (2026-05-21), this project leans on existing work
aggressively rather than reinventing. Phase 0 survey is captured in
[`notes/survey_2026_05_21.md`](notes/survey_2026_05_21.md). Top candidates:

- **[JackHopkins/factorio-learning-environment](https://github.com/JackHopkins/factorio-learning-environment)** (FLE) — MIT, NeurIPS 2025, Python + Docker observation/action REPL for LLM agents. Mature. Single-player evaluation focused; multiplayer co-play is our adaptation.
- **[mark9064/factorio-rcon-py](https://github.com/mark9064/factorio-rcon-py)** — standard Python RCON client. PyPI.
- **[Windfisch/factorio-bot](https://github.com/Windfisch/factorio-bot)** — early POC, C++/Lua, fair-info principle. Reference for multiplayer mechanics.

## Architecture (Phase 0 draft, subject to revision)

```
+----------------------+         +-----------------------+
| Will's Steam Factorio|         | Jonah's Steam Factorio|
| (GUI client)         |         | (GUI client)          |
+----------+-----------+         +----------+------------+
           |  multiplayer LAN/loopback        |
           v                                  v
        +-----------------------------------------+
        | Factorio headless server (this repo)    |
        |   + skynet_observer Lua mod             |  <-- state emission + cmd intake
        |   + RCON enabled                        |
        +---------------------+-------------------+
                              |  RCON commands / state pipe
                              v
                  +-------------------------+
                  | Python harness          |
                  |   factorio-rcon client  |
                  |   FLE-derived brain     |  <-- decision layer (LLM or scripted)
                  +-------------------------+
```

Topology rationale: headless hosts, GUI clients connect. Cleaner than
"bot joins external game" — bot's mod is in-process with the simulation,
no LAN protocol layer between bot and game state.

## Layout

- `mod/skynet_observer/` — Factorio Lua mod for state emission + command exec
- `harness/` — Python harness (RCON client + decision logic; will pull from FLE)
- `notes/` — research, survey, primer for Will
- `scripts/` — install/launch helpers

## Status checklist (Phase 0)

- [x] Survey existing work
- [x] Decide topology (headless-hosts)
- [x] Repo scaffolded
- [ ] Headless Factorio installed on cake
- [ ] factorio-rcon Python lib installed + tested
- [ ] Minimal Lua mod that emits one tick of state
- [ ] Smoke test: Will + bot in one game
