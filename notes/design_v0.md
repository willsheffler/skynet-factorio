# skynet-factorio design v0

**Date:** 2026-05-21
**Author:** Vellum, synthesizing Will's brainstorm (ftui_turn_25e3507d + ftui_turn_012c08e9 + ftui_turn_1a99a511)
**Status:** Living document. Will will have more scattered thoughts; this absorbs them.

## North-star: useful teammate, not bot-purity

The primary success criterion is **the bot makes Will + Jonah + Judah's
multiplayer Factorio sessions more fun**. NOT:

- Maximum AI research purity (no cheating, fair-info-only).
- Maximum SOTA agent performance benchmarked against FLE.
- Long arc to "intelligent enough to play unaided" with kids losing interest first.

Bot-purity remains a long-term aspirational direction (and the academically
interesting one) but it's downstream of getting the kids hooked.

## Architectural axes

### Axis A: Bot role on the team

Configurable roles, switchable per game:

- **Security / combat** — patrols, fights biters, defends base perimeter.
  Lowest bar for usefulness; can succeed via reflexes + cheat-supplied combat
  effectiveness.
- **Builder / assembly assistant** — places entities per instructions or
  blueprints. Higher autonomy with blueprint library access.
- **Resource gatherer** — mines ore, hauls items. Simple loops, easy to be
  useful.
- **Logistics / inserter-tuner** — micro-optimizations on existing factory.
  Niche but high-value role.
- **Co-pilot** — follows a human player and supplements their actions (hand
  them ammo, place inserters where they're pointing, etc).

Roles can be combined. Each role has its own cheat-budget defaults.

### Axis B: Cheat budget (FIRST-CLASS knob, not workaround)

Per Will's framing: cheating-to-compensate-for-dumb-bot is a feature, tunable
per role, per session. Cheats range from "indistinguishable from a really good
player" to "outright god mode" with named tiers:

- **Tier 0 — Fair human-equivalent.** Bot only uses information a human player
  could see. No cheats. Maximum research purity. Bot will probably be useless
  unless Phase 3+ smart.
- **Tier 1 — Vision boosts.** Bot sees full map regardless of fog-of-war.
  Knows entity inventories without walking up. Has full game-state in JSON
  (we get this for free from the mod side).
- **Tier 2 — Reach + speed.** Extended build range; faster character speed;
  improved mining speed. Bot can act faster than a human but plays "by the
  rules" of the simulation.
- **Tier 3 — Resource subsidies.** Free starter inventory; periodic supply
  drops; or full creative-mode infinite inventory for unlocked recipes.
- **Tier 4 — Combat invulnerability or damage boost.** Useful for the
  security role; lets a dumb bot still be a useful tank against biters.
- **Tier 5 — Blueprint library access.** Bot has a curated blueprint library
  it can search and place from. NOT cheating per se — it's the bot's
  long-term-memory of "known-good builds." Composable with all tiers.
- **Tier 6 — Direct teleport / item conjuring.** Full god mode for testing or
  for "the bot is mostly an annoying assistant that just makes the things you
  ask for".

The config file picks a base tier per role plus optional per-axis overrides.

### Axis C: Decision substrate (the bot's "brain")

Three layers, composable:

#### C1 — Scripted heuristics
Plain Lua + Python rules: patrol this area; build this blueprint; if
inventory full, deposit at this chest. The fallback layer that ALWAYS works.
Phase 0 ships this.

#### C2 — Local RL agent
Reinforcement-learning policy trained on Factorio. Likely starts by importing
FLE's training infrastructure. Local model (no API costs, low latency).
Substrate for the "tactical execution" layer.

#### C3 — LLM coordinator (THE research-interesting layer)
LLM agent (Claude or other) provides:

- High-level priority setting ("focus on iron production this hour")
- Periodic strategy review (review base state, suggest next research priority)
- Direct override commands when human players direct the bot
- Goal decomposition into sub-tasks for C1/C2

Hybrid hierarchical control: LLM sets goals; RL or scripted heuristics
execute tactics. This is a genuinely novel direction worth exploring as the
project matures.

Per Will: an interesting bonus direction is **connecting the LLM coordinator
to an existing agent (e.g., Vellum) rather than a fresh Claude API session**.
That gives the bot persistent identity, memory of past games, relationship
with the kids. Worth exploring once C1/C2 are stable.

### Axis D: Human-bot interaction surface

How do Will / Jonah tell the bot what to do? Options:

- **In-game chat commands** (`/skynet build solar-panel here`)
- **GUI panel** (custom mod UI with buttons/sliders for common requests)
- **Voice via Will's frontend** (push commands through Pensieve → bot RCON)
- **Pre-game config file** (set role + cheat tier + priorities before launch)

Phase 0 ships chat commands (cheapest). GUI panel and voice are Phase 2+.

## Figure-of-merit: speed-run benchmarks

Per Will's ftui_turn_9d7f85b6 brainstorm: a clean evaluation surface is
**task-completion-time benchmarks** run headlessly on the bot alone.

- Time-to-rocket-launch (base game)
- Time-to-Space-Age-completion (DLC)
- Time-to-individual-achievement (Factorio has dozens — cheap unit tests of bot capability)
- Per-recipe-unlock time
- Per-research-tree-completion time

These can run overnight on cake while Will sleeps. Each run produces a
single number (or fail) so trends are visible across bot iterations. Maps
cleanly onto FLE's evaluation harness (FLE itself uses task-completion as
its benchmark metric). Adopt FLE's suite verbatim where it exists, add our
own for Factorio achievements not yet covered.

This benchmark surface composes with the cheat-budget axis nicely — same
task, different cheat tier, compare completion times. Lets us empirically
measure the cheat-vs-competence tradeoff.

## Phase plan (revised after brainstorm)

### Phase 0 (THIS WEEK)
- Repo scaffolded; survey doc; design doc (this doc).
- Headless Factorio installed; RCON tested.
- Minimal mod that emits state on tick + exposes a `/skynet_say <msg>`
  chat command for round-trip testing.
- Smoke test: Will joins bot-hosted game, sees the bot mod loaded.
- **Done condition:** Will can host Will+Jonah multiplayer using the bot's
  headless server, see the bot mod working, even if the bot does nothing
  yet.

### Phase 1 (NEXT WEEK)
- C1 scripted-heuristic decision layer with at least the "security patrol"
  role working.
- Cheat budget config file + Tier 1-4 implementations.
- Bot character actually moves, sees, fights.

### Phase 2
- C2 RL substrate via FLE-borrowed training infra.
- Blueprint library access (Tier 5).
- Builder role.

### Phase 3
- C3 LLM coordinator. Initially fresh Claude API session. Then explore
  connecting to existing Vellum/other-agent persistent identity.

### Phase 4
- Research write-up of hybrid hierarchical control findings (if it turns
  into something) — career-rehab artifact if it's good.

## Open questions for Will (no rush)

- Skynet identity expansion: confirm or alternate name (see survey doc).
- ~~License: MIT? Apache? AGPL?~~ **RESOLVED 2026-05-21**: Apache 2.0 per Will preference.
- Cheat-budget defaults: deprecated as a "pick before game" config; see
  architecture v0.1 below — capabilities are now dynamically dialed by the
  LLM in response to in-game chat.
- Persistent-identity bot via existing agent (Vellum / Madeira / other):
  which agent's voice should the bot have? Or a fresh identity entirely?

---

## Architecture v0.1 — after 2026-05-21 brainstorm

Substantive updates from Will-direct conversation (ftui_turn_8772b102 +
ftui_turn_4255e204). Key shifts: capabilities are dynamic not static;
in-game chat is first-class input from day one; multi-tier LLM stack
(Opus strategic + Haiku tactical-chat).

### Capabilities are dynamic, not static

Tiered configs you pick before a game are deprecated. The driving LLM
grants and revokes individual capability knobs on the fly based on
in-game chat. Named bundles are mnemonic shorthand for the LLM, not
user-picked configs.

**Atomic capability knobs the LLM toggles per-bot per-moment:**

- `vision` — full map awareness, no fog of war
- `reach` — extended build / mining / combat range
- `speed` — faster character / mining / building
- `combat` — damage multiplier or invulnerability
- `resources` — inventory subsidy (one-shot or continuous trickle)
- `blueprint-lib` — search-and-place from curated blueprint library
- `teleport` — instant position change
- `item-conjure` — spawn any unlocked item into inventory
- `auto-route` — SAT-solver-backed optimal belt routing on demand

**Named bundles (LLM shorthand):**

- `fair-player` — nothing granted
- `defender` — vision + combat
- `builder` — vision + reach + blueprint-lib
- `gatherer` — vision + speed + light resources
- `god-mode` — everything

### In-game chat is first-class input from day one

The `skynet_observer` Lua mod hooks `on_console_chat`. Every player
message gets pushed (not pulled) into a chat buffer with `sender + tick
+ text`, with `@skynet`-prefixed messages flagged as bot-directed but
non-directed chat still routed for team-context awareness. Push goes to
the Pensieve-side driving agent over RCON.

### Three-tier LLM stack

Composing Will's multi-tier-agent direction with the strategic-vs-tactical
layer boundary I sketched earlier:

```
+-------------------------------------------------------+
| C3: Strategic LLM — Opus or Sonnet                    |
|   Cadence: tens of seconds to minutes                 |
|   Job: Voyager-style curriculum + skill curation;     |
|        deep deliberation on capability grants;        |
|        personality chat with time to think;           |
|        skill-library write-back                       |
+----------------+--------------------------------------+
                 |  oversight + escalate-up channel
                 v
+-------------------------------------------------------+
| C2.5: Tactical-chat LLM — Haiku                       |
|   Cadence: ~0.5s response                             |
|   Job: real-time chat read + snappy banter back;      |
|        fast capability dial-up / dial-down;           |
|        route deeper questions up to strategic;        |
|        the personality Will & Jonah feel in-game      |
+----------------+--------------------------------------+
                 |  calls Python primitives
                 v
+-------------------------------------------------------+
| C2: Skill library — Python over FLE API               |
|   Cadence: microseconds                               |
|   Job: build-smelter-pair, defense-patrol, etc.       |
|        Voyager-style growing-by-experience            |
+----------------+--------------------------------------+
                 |  calls FLE API + cheat surface
                 v
+-------------------------------------------------------+
| C1: FLE Python API + cheat-toggle surface             |
|   Cadence: microseconds                               |
|   Job: move bot character, place entities, apply or   |
|        revoke vision/reach/speed/combat/etc.          |
+-------------------------------------------------------+
```

Combat reflexes still live below the LLM tiers in scripted or RL
tactics. Strategic loop: human-chat cadence. Tactical-chat loop:
half-second. Skill execution: real-time.

### Strategic-vs-tactical handoff: default Option A

**Option A (default)**: Haiku decides everything. Opus watches and posts
corrections asynchronously via in-chat note or quiet capability revocation.
Lower latency, looser supervision. Mirrors Facet/Pavilion or
Facet/Marrow coordinator-of-record patterns.

**Option B (alternate)**: Haiku handles low-stakes only. Above an
impact threshold (grant god-mode, change current task), route to Opus
for confirmation, blocking Haiku. Higher latency for important calls,
tighter supervision.

Defaulting to A with explicit escalate-up triggers Haiku can fire when
it knows it's over its head.

### LLMs speak in chat with distinct personalities

Tactical-fast Haiku is impulsive, snappy. Strategic Opus or Sonnet is
slower, deliberate, more deliberate. Will and Jonah read the difference
as a real teammate quirk — the bot has a fast-talking side and a
slow-thinking side. Fun and lowers cognitive load (the personalities are
the API).

### Composability with Will + Facet's voice-chat direction

Same shape Will and Facet are exploring for voice-chat: Haiku as snappy
front, Sonnet or Opus as deliberate puppeteer monitoring and correcting.
Skynet is a test bed for that pattern in a non-relational context. If it
works here it informs the Facet/voice direction too.
