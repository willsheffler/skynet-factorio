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
- [x] Headless Factorio configured on cake (Steam binary + separate runtime dir)
- [x] factorio-rcon Python lib installed + tested
- [x] Minimal Lua mod loaded successfully + remote interface verified
- [x] Smoke test end-to-end: ping + state_snapshot + say round-trip via RCON
- [ ] Live multiplayer smoke: Will joins bot-hosted game (deferred until Will has time at cake)

## Phase 0 quickstart

```bash
# 1. Initialize headless runtime (one-time)
./scripts/init_headless.sh

# 2. Set up the Python harness venv (one-time)
cd harness && uv venv && uv pip install -e . && cd ..

# 3. Launch the headless server (in one terminal)
./scripts/run_headless.sh skynet_smoke

# 4. In another terminal, run the smoke test
cd harness && .venv/bin/python -m skynet_harness.smoke
```

The headless server listens on LAN port 34197. Steam Factorio clients can find
it via Play → Multiplayer → Play on LAN.
