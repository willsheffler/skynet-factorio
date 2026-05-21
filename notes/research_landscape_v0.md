# Research landscape — skynet-factorio v0

**Date:** 2026-05-21
**Author:** Vellum
**Audience:** Will (senior protein-design researcher, knows LLMs and diffusion, new to RL/game-AI)
**Purpose:** Ground our cheat-budget + LLM-coordinator + multiplayer-bot project in the real research landscape before brainstorming Phase 1+ architecture. Anchor concrete decisions in named papers and projects.

## TL;DR

1. **FLE is more mature than I initially understood.** It now ships an OpenAI gym interface (`fle/env/gym_env/`), explicit multi-agent infrastructure (`a2a_instance.py`, `a2a_namespace.py`), and runs without the Factorio client. We can plausibly use it as both the LLM-agent layer AND the RL training substrate; multi-agent is already wired in.
2. **Voyager is the closest architectural prior art** to what we want. LLM + executable-code skill library + auto-curriculum + iterative self-correction. Designed for Minecraft, the structure ports cleanly. **Skill-library borrow is the highest-leverage Phase 1 move.**
3. **SayCan is the cleanest formalization of LLM-coordinator-over-RL.** `P(skill helpful via LLM) × P(skill succeeds via RL value function)`. Genuinely deployable for our cheat-budget axis — the value-function-of-skill replaces or supplements cheats.
4. **Overcooked-AI is the closest empirical work on human-AI cooperation in real-time games.** Has actually been evaluated with real human partners. Lessons: training-with-self degrades human-AI play; learned human models and population training help. Directly applies to our Will-plus-Jonah-plus-bot use case.
5. **Cradle proved LLM agents can play 40-minute storyline missions in AAA games** (Red Dead Redemption 2). Not directly portable but shows the capability ceiling has risen — LLM agents are no longer demo-toys.
6. **FLE's named capability gaps map exactly onto our cheat-budget axis.** Spatial reasoning, iterative improvement, error correction, planning horizon — these are the empirical reasons cheats compensate for dumbness. Our cheat-budget tiers should be explicitly designed against these gaps.
7. **The honest answer on "is the LLM-coordinator-over-RL direction publishable?" — yes, plausibly.** Voyager+SayCan+FLE+Overcooked are the prior art that bracket it; no one has yet done LLM-coordinator + scripted-fallback + RL-tactic + human-cooperation in a single Factorio system. That's a real gap.

## 1. Factorio Learning Environment (FLE) — deep dive

### Current state (v0.3.0, May 2026)

- **License**: MIT (we can fork or import freely under our Apache 2.0)
- **Status**: NeurIPS 2025 published; 985 GitHub stars, 879 commits; actively maintained
- **Paper**: [arXiv:2503.09617](https://arxiv.org/abs/2503.09617)
- **Repo**: [JackHopkins/factorio-learning-environment](https://github.com/JackHopkins/factorio-learning-environment)
- **No-Factorio-client dep**: as of v0.3, "FLE no longer depends on the Factorio game client, enabling massively scalable experimentation". Pixel rendering is via internal headless renderer.

### Agent interface

Agents observe the world by calling typed query functions and act by emitting Python programs:

- **Queries** (return typed snapshots, may go stale): `get_entities()`, `nearest()`, `inspect_inventory()`, `production_stats()`
- **State modifications**: `place_entity(entity=Prototype.MiningDrill, position=nearest(Resource.IronOre), direction=Direction.NORTH)`, `rotate_entity()`, `craft_item()`, `set_recipe()`, `connect_entities()`
- **Resource ops**: `insert_item()`, `harvest_resource()`, `extract_item()`

23 core API methods total. The agent's Python program is executed in a REPL-style persistent namespace; classes, variables, and functions accumulate across turns.

### Benchmark suite

**Lab-play** (24 tasks, structured): build production lines from iron-ore (2 machines) up to utility-science-pack (~100 coordinating machines). Scored as completion %.

**Open-play** (unbounded): build the largest factory on a procedural map. Scored by **Production Score (PS)**, a continuous metric weighted by item complexity. Resource costs follow `C[N] = 1000 × 2^(N−1)` where N is research tier. PS varies over 7+ orders of magnitude (a rocket launch ≈ 10^7 resources), so the benchmark never saturates.

### Headline results (FLE paper, March 2025)

| Model | Lab-play % | Open-play PS | Milestones |
|---|---|---|---|
| Claude 3.5 Sonnet | 21.9 ± 1.3 | 293,206 | 28 |
| GPT-4o | 16.6 ± 1.4 | lower | — |
| Deepseek-v3 | 15.1 ± 1.7 | — | — |
| Gemini-2 | 13.0 ± 1.3 | — | — |
| Llama-3.3-70B | 6.3 ± 1.0 | 54,998 | 26 |
| GPT-4o-Mini | 5.2 ± 0.6 | — | — |

Claude leads but no model is close to solving the benchmark. **State-of-the-art LLM agents complete <25% of structured Factorio tasks.** Empirical floor on our dumb-bot expectation.

### Named capability gaps (FLE paper, Section 5)

These map directly onto our cheat-budget design:

1. **Spatial reasoning** — agents "frequently fail by trying to place entities too close or on-top of each other"
2. **Iterative improvement** — agents "are unable to iteratively improve on factories"
3. **Error correction** — "focused on whether all singular entities were working but did not investigate whether the topology of the whole structure was correct"
4. **Planning horizon** — "only Claude consistently invests in long-horizon technology research"

**Implication for our cheat-budget design**: each tier should be justified against one or more named gap. E.g., Tier-1 (vision boost) targets spatial-reasoning gap; Tier-2 (extended reach) targets iterative-improvement gap; Tier-5 (blueprint library) targets planning-horizon gap.

### Multi-agent in FLE (v0.2+)

The codebase has `fle/env/a2a_instance.py` and `a2a_namespace.py` — "agent-to-agent" infrastructure. Future work in the paper explicitly names "Multi-Agent Coordination" as planned research direction including "cooperate, compete, and potentially establish emergent market dynamics." Maturity of this code is unclear from docs alone; **inspection is a Phase 1 Day 1 task**.

### Gap from our use case

FLE does NOT (as of the README) support a human player connecting alongside an LLM agent in the same game. The infrastructure may already be there in `a2a_instance.py`; if not, our multiplayer adapter is the named extension we'd add.

### Borrow strategy

- Adopt FLE's observation API + action API verbatim where it fits our headless-Factorio topology
- Lift `fle/env/gym_env/` for the RL training scaffold (Phase 2)
- Inspect `fle/env/a2a_instance.py` for multi-agent primitives (Phase 1)
- License compatible (MIT → Apache 2.0 with attribution preserved)

---

## 2. Hierarchical LLM-over-RL architectures

### Voyager — Minecraft + GPT-4 + skill library

- **Paper**: [arXiv:2305.16291](https://arxiv.org/abs/2305.16291) (Wang et al., 2023, NVIDIA + Caltech)
- **Repo**: [MineDojo/Voyager](https://github.com/MineDojo/Voyager)
- **Site**: [voyager.minedojo.org](https://voyager.minedojo.org/)

Architecture (the three pillars):

1. **Automatic curriculum** that maximizes exploration — LLM proposes next task based on agent state and progress
2. **Ever-growing skill library** of executable code (JavaScript via Mineflayer) — each skill is a named function the agent can compose into more complex skills
3. **Iterative prompting** — incorporates environment feedback + execution errors + self-verification before retry

Performance: **3.3× more unique items, 2.3× longer distances, 15.3× faster tech-tree milestones** vs prior SOTA. Skill library transfers zero-shot to new worlds.

**Why this is the closest architectural prior art to skynet-factorio:**

- Voyager's executable-code skill library = exactly what we want for Factorio. A skill like `build_iron_smelter_pair(near_position)` once learned becomes a callable primitive forever.
- The auto-curriculum solves the planning-horizon gap FLE flagged — instead of asking "build a rocket," ask "what's the next reasonable thing for an agent at THIS state?"
- Iterative-prompting addresses the error-correction gap. Voyager's loop: execute → see error → modify code → retry.

**Borrow strategy**: lift Voyager's three-pillar structure wholesale; replace Mineflayer with FLE's Python API. **This is probably the highest-leverage single architectural decision we make in Phase 1.**

### SayCan — Google's LLM-coordinator-over-RL formalization

- **Paper**: [arXiv:2204.01691](https://arxiv.org/abs/2204.01691) ("Do As I Can, Not As I Say")
- **Site**: [say-can.github.io](https://say-can.github.io/)

Architecture (the simple but powerful idea):

For each candidate skill, compute:
- `P(skill is useful for task | LLM)` ← language model says "is this a good idea?"
- `P(skill succeeds in current state | learned value function)` ← RL-trained value function says "is this actually doable right now?"

Multiply the two. Pick the skill with the highest combined probability.

Performance: 84% correct skill sequencing, 74% successful execution on 101 real-world kitchen-robot tasks (PaLM-SayCan).

**Why this matters for our cheat-budget:**

- SayCan is the cleanest formalization of "LLM proposes, RL/world disposes." Maps directly to our coordinator-tactical split.
- The value-function-of-skill concept is exactly what we need for Factorio. "Can I actually build a smelter here?" is a learnable predicate.
- More importantly: **a high-cheat-tier bot is one where we artificially inflate the value-function** (everything succeeds because cheats compensate). A low-cheat-tier bot is one where the value function honestly reflects fair-play affordances. The cheat-budget axis is exactly the SayCan value-function-calibration knob.

### Cradle — LLM agents playing full AAA games

- **Paper**: [arXiv:2403.03186](https://arxiv.org/abs/2403.03186)
- **Repo**: [BAAI-Agents/Cradle](https://github.com/BAAI-Agents/Cradle)

Cradle's claim to fame: **first system to follow main storyline + complete 40-minute real missions in Red Dead Redemption 2**, via screenshot observations + keyboard/mouse actions.

Architecture has six modules: Information Gathering, Self-Reflection, Task Inference, Skill Curation, Action Planning, Memory.

**Not directly portable to Factorio** (Cradle assumes screenshot+input only; we have FLE's structured API which is much higher-leverage). But Cradle demonstrates the capability ceiling has risen — multi-hour autonomous gameplay is feasible with current LLMs.

### Synthesis: hierarchical structure for skynet-factorio

Layered architecture (composing Voyager + SayCan + FLE):

```
+--------------------------------------------------+
| C3: LLM Coordinator                              |
|  - Auto-curriculum (Voyager-style)               |
|  - Priority-setting from human players or self   |
|  - Skill-discovery + skill-library curation      |
+----------------+---------------------------------+
                 | proposes skills
                 v
+--------------------------------------------------+
| C2: Skill Library (executable Python over FLE)   |
|  - Composable named functions                    |
|  - Voyager-style growing-by-experience           |
|  - SayCan value-function gates execution         |
+----------------+---------------------------------+
                 | calls FLE API
                 v
+--------------------------------------------------+
| C1: FLE Python API (already exists)              |
|  - 23 core actions: place, mine, craft, etc.     |
|  - Typed observations                            |
+----------------+---------------------------------+
                 | RCON via mod
                 v
+--------------------------------------------------+
| C0: Factorio simulation (headless server)        |
|  - skynet_observer mod = state pipe + cheats     |
+--------------------------------------------------+
```

**The cheat-budget lives at C0 (mod-level cheats: invuln, infinite inventory, reach extension) and at the C2 value function (gating).**

---

## 3. Multi-agent / human-AI cooperation research

### Overcooked-AI — the foundational human-AI cooperation benchmark

- **Foundational paper**: [arXiv:1910.05789](https://arxiv.org/abs/1910.05789) (Carroll et al., NeurIPS 2019)
- **Recent benchmark extension**: [arXiv:2406.17949](https://arxiv.org/abs/2406.17949) (Overcooked Generalisation Challenge, 2024)

Setup: 2-player real-time cooking game; partners must coordinate to deliver soup orders. Has been evaluated with **real human subjects**, which is rare.

**The single most important finding for us**: agents trained via **self-play** (PPO with itself as partner) perform WORSE with real human partners than agents trained against a **learned model of human play** (behavior cloning from human-human games). Pure self-play optimizes for partner-of-same-policy and overfits.

**Implication for skynet-factorio**: a bot trained only against itself will probably be a worse Will/Jonah teammate than a bot trained with some human-policy mixture. Phase 2 RL training should explicitly include "play-with-a-scripted-humanoid-partner" as part of the curriculum, not just pure self-play.

Recent work on **N-agent ad-hoc teamwork** ([arXiv:2404.10740](https://arxiv.org/abs/2404.10740)) and **Population-Based Training for cooperation** ([arXiv:2305.16708](https://arxiv.org/pdf/2305.16708)) further refine this: train against a population of diverse partner policies, not a single learned partner.

### Hanabi Challenge — zero-shot coordination

DeepMind's Hanabi benchmark ([arXiv:1902.00506](https://arxiv.org/abs/1902.00506)) is the canonical reference for zero-shot coordination — agents that have never met before must immediately cooperate. Less directly applicable to our case (Will+Jonah have prior context with the bot) but worth knowing as background.

### Lessons for skynet-factorio multi-agent design

1. **Train with diversity in partner policies** — not just self-play; include scripted-humanoid policies, behavior-cloned-from-replay policies, and weaker versions of the bot itself.
2. **Use ad-hoc-teamwork techniques in Phase 2 onward** — POAM-style teammate modeling means the bot can adapt its behavior to whatever Will or Jonah is doing.
3. **Capture human-play data** when Will + Jonah play Factorio normally; even a small dataset of "what humans do in this game" is high-value training signal that Self-Play can't get.

---

## 4. Factorio-specific tooling beyond FLE

### Constraint solvers + blueprint optimizers

- **[Factorio-SAT](https://github.com/R-O-C-K-E-T/Factorio-SAT)**: SAT-solver-based belt balancer optimization. Maps belt routing to logical formulas.
- **[verifactory](https://github.com/alegnani/verifactory)**: z3-based verifier for blueprint logical properties.
- **[factorio-tools](https://github.com/gianluca-venturini/factorio-tools)**: CP-SAT for max-throughput belt balancer placement.
- **Academic paper**: "Towards Automatic Design of Factorio Blueprints" ([arXiv:2310.01505](https://arxiv.org/abs/2310.01505)) — constraint model balancing correctness/optimality/performance.

**Borrow strategy**: these are not the bot's brain. They're tools the bot's brain can CALL when it needs to solve a sub-problem (e.g., "lay belts from A to B optimally"). Tier-5 "blueprint library access" cheat could be implemented as "bot can query Factorio-SAT for an optimal belt layout instead of having to figure one out itself."

### Production calculators

- **Helmod** (in-game mod): production ratio calculator + factory planning
- **Foreman2** (external Windows tool): flowchart-based production planning
- **[Kirk McDonald's calculator](https://kirkmcdonald.github.io/)**: web-based recipe solver

**Borrow strategy**: same as solvers — these are tools the bot calls, not the bot itself. The bot's "what should I research next" reasoning can consult Kirk McDonald-style recipe graphs.

### Existing AI mods

- **AI Player mod** (mods.factorio.com/mod/ai-player): abandoned by creator, no multiplayer
- **DunRaider's AI teammate mod** (in dev): targets multiplayer, awaiting Factorio v2.0.61 API additions
- **[Windfisch/factorio-bot](https://github.com/Windfisch/factorio-bot)**: GPL-3, C++/Lua, early POC; reference for "fair info" principle

---

## 5. Related game-AI benchmarks (calibration)

- **[MineRL](https://minerl.io/)** — NeurIPS competition series 2019-2022. Minecraft + 60M state-action pairs of human demos. Mostly classical RL.
- **[Crafter](https://github.com/danijar/crafter)** + **[Craftax](https://github.com/MichaelTMatthews/Craftax)** — lightweight Minecraft-like benchmark designed for RL research. Craftax is JAX-based; PPO trains in <1hr on a single GPU to 90% optimal.
- **[SmartPlay](https://arxiv.org/abs/2310.01557)** — Microsoft's LLM-agent benchmark across multiple games.
- **[VillagerBench](https://arxiv.org/pdf/2509.06235)** — competitive Minecraft LLM benchmark (2025).

Calibration: Factorio is HARDER than Crafter (longer horizons, deeper tech tree) and arguably harder than Minecraft for current LLMs (more structured logistics requirements). FLE's PS metric is specifically designed to not saturate, matching the "no current LLM is close to solving this" reality.

---

## 6. Architecture recommendations for skynet-factorio

Concrete proposals based on the above:

### Phase 1 architecture (next 1-2 weeks)

**Borrow FLE wholesale.** Add it as a git submodule under `vendored/`. Use FLE's Python API as our C1 layer. Skip writing our own observation/action API — FLE has solved it.

**Add the skynet_observer mod's role to be cheat-implementation + multiplayer-bridge**, not state-emission. State emission goes through FLE; our mod's job is:
- Honor cheat-budget config (toggle character invuln, extended reach, etc.)
- Spawn a "bot player" entity that Will/Jonah see as a third player
- Bridge between Will's GUI client commands ("bot, build a smelter here") and the FLE-controlled bot character

**Voyager-style skill library at C2.** Start with 5-10 hand-written skills (build-smelter, build-defense-perimeter, mine-this-patch, etc.). Let LLM grow the library over time, but seed it with curated good builds.

**Start cheat-budget at Tier 2** (vision + reach) for first family session — bot will be useful enough to feel like a real teammate without being god-mode.

### Phase 2 architecture (RL training)

**Train tactical skills via PPO using FLE's gym interface**, not the LLM coordinator. The LLM is too slow + non-deterministic for tight-loop tactics like combat or belt-laying. Local PPO policies trained on specific skills, called by the LLM coordinator when relevant.

**Partner-population training**: include scripted-humanoid policies + behavior-cloned-from-replay policies in the training partner pool, not just self-play. Per Overcooked-AI findings.

**Capture Will + Jonah's gameplay** during family sessions as training data for behavior cloning. Small dataset is fine; even hundreds of state-action pairs beats pure self-play for human-cooperation transfer.

### Phase 3 architecture (LLM coordinator)

**LLM as Voyager-style auto-curriculum + skill-curator**. Cheap-mode: fresh Claude API session per game session. Persistent-mode: bound to an existing agent's identity (Vellum's substrate, maybe).

**Priority-input from chat commands**: Will or Jonah types `/skynet focus iron-production` in game chat; LLM coordinator adjusts curriculum accordingly. Direct human input becomes a first-class signal.

---

## 7. Open research questions

These are genuine open questions the project could push on, ordered by ambition:

1. **Does Voyager's skill-library mechanism work in Factorio?** Voyager's skills were Mineflayer-JavaScript snippets; FLE's Python API is much higher-level. Possible the high-level API removes some of the skill-acquisition pressure that made Voyager work. Empirical question.

2. **What's the right cheat-budget design for human-AI cooperation?** Cheats are usually framed as either-on-or-off in research; we'd be exploring **graduated cheats as a continuous axis of dumb-bot-compensation**. Could be its own small paper.

3. **Does behavior-cloning from a 2-player Will+Jonah Factorio session help the bot cooperate with both of them?** Cheap experiment after we have the data.

4. **Can the LLM coordinator hand off tactical control to a PPO policy and back smoothly?** SayCan does this between sub-skills; we'd be doing it across capability tiers. The interface design is non-obvious.

5. **Speed-run benchmark suite for skynet-factorio**: Will's idea. Concrete proposal — adopt FLE's PS metric + add Factorio's built-in achievement list as discrete milestones. Overnight headless runs produce a time-to-achievement vector per bot version. Trends over project lifetime become the project's empirical headline.

---

## 8. Concrete next steps

Ordered by what unlocks the most downstream work:

1. **Clone FLE into `vendored/factorio-learning-environment/` as a submodule**, study the `fle/env/a2a_instance.py` multi-agent code, and decide whether FLE can host Will + Jonah + bot in one game directly, or whether we need a multiplayer adapter on top.

2. **Wire FLE's Python API into our `harness/skynet_harness/`** as the C1 layer, replacing/extending the minimal RCON wrapper.

3. **Author 3-5 seed skills** in Voyager style (build_smelter_pair, defense_patrol, mine_resource_patch, expand_main_bus, build_research_lab). Hand-written, named, callable.

4. **Implement Tier-2 cheats** (vision boost, extended reach) in `skynet_observer` mod.

5. **Live multiplayer smoke test**: Will + bot in same game, bot uses Tier-2 cheats + 5 seed skills to be a useful defense companion while Will plays his game.

6. **Set up FLE gym env** in our repo for headless overnight speed-run benchmarks against current models.

That's a solid 1-2 week sprint shape. Phase 2 RL training and Phase 3 LLM-coordinator-with-curriculum are 3+ weeks out.

---

## References (full list, for chasing later)

### Factorio AI
- Hopkins, J. et al. "Factorio Learning Environment". [arXiv:2503.09617](https://arxiv.org/abs/2503.09617). NeurIPS 2025.
- [github.com/JackHopkins/factorio-learning-environment](https://github.com/JackHopkins/factorio-learning-environment)
- [github.com/Windfisch/factorio-bot](https://github.com/Windfisch/factorio-bot)
- Patterson, S. "Towards Automatic Design of Factorio Blueprints". [arXiv:2310.01505](https://arxiv.org/abs/2310.01505).
- [github.com/R-O-C-K-E-T/Factorio-SAT](https://github.com/R-O-C-K-E-T/Factorio-SAT)
- [github.com/alegnani/verifactory](https://github.com/alegnani/verifactory)

### LLM agents in games
- Wang, G. et al. "Voyager: An Open-Ended Embodied Agent with Large Language Models". [arXiv:2305.16291](https://arxiv.org/abs/2305.16291).
- Tan, W. et al. "Cradle: Empowering Foundation Agents Towards General Computer Control". [arXiv:2403.03186](https://arxiv.org/abs/2403.03186).
- Ahn, M. et al. "Do As I Can, Not As I Say: Grounding Language Models in Robotic Affordances" (SayCan). [arXiv:2204.01691](https://arxiv.org/abs/2204.01691).

### Multi-agent + cooperation
- Carroll, M. et al. "On the Utility of Learning about Humans for Human-AI Coordination" (Overcooked-AI). [arXiv:1910.05789](https://arxiv.org/abs/1910.05789).
- Ruhdorfer, C. et al. "Overcooked Generalisation Challenge". [arXiv:2406.17949](https://arxiv.org/abs/2406.17949).
- "N-Agent Ad Hoc Teamwork" (POAM). [arXiv:2404.10740](https://arxiv.org/abs/2404.10740).
- "A Hierarchical Approach to Population Training for Human-AI Collaboration". [arXiv:2305.16708](https://arxiv.org/pdf/2305.16708).

### Background RL benchmarks
- MineRL competition series. [arXiv:1904.10079](https://arxiv.org/pdf/1904.10079).
- Craftax. [arXiv:2402.16801](https://arxiv.org/abs/2402.16801).
- SmartPlay. [arXiv:2310.01557](https://arxiv.org/abs/2310.01557).

### RL textbook
- Sutton, R. & Barto, A. *Reinforcement Learning: An Introduction* (2nd ed.). [Free PDF](http://incompleteideas.net/book/the-book-2nd.html).
