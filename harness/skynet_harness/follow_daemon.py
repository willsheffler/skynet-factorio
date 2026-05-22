"""follow_daemon — Python-side reliable follow-logic. Polls storage.standing_orders
and advances autopilot for bots with kind = 'follow:<player>' orders.

Runs alongside chat_pump. Updates every 2 seconds. Doesn't rely on eval-haiku
for the follow behavior — Haiku is for command interpretation; this is the
deterministic execution layer.

Run with: uv run python -m skynet_harness.follow_daemon
"""

from __future__ import annotations

import time

from .client import SkynetClient


def main() -> int:
    print("follow_daemon starting (2s tick)")
    with SkynetClient() as c:
        while True:
            try:
                # Single Lua block: for each standing order with kind='follow:<player>',
                # set autopilot_destination to within radius tiles of that player.
                lua = """
local orders = storage.standing_orders or {}
local moved = 0
for bot_name, order in pairs(orders) do
  if type(order) == 'table' and order.kind then
    local kind = order.kind
    if string.sub(kind, 1, 7) == 'follow:' then
      local target = string.sub(kind, 8)
      local p = game.get_player(target)
      local radius = order.radius or 3
      local bot_entity = nil
      if bot_name == 'Facet' then bot_entity = storage.facet_char end
      if bot_name == 'Vellum' then bot_entity = storage.vellum_char end
      if bot_name == 'Skynet' and storage.bots and storage.bots.skynet then bot_entity = storage.bots.skynet.entity end
      if bot_entity and bot_entity.valid and p and p.character and p.character.valid then
        local bp = bot_entity.position
        local tp = p.character.position
        local dx = tp.x - bp.x
        local dy = tp.y - bp.y
        local dist = math.sqrt(dx*dx + dy*dy)
        if dist > radius + 1 then
          bot_entity.autopilot_destination = { tp.x - 2, tp.y }
          moved = moved + 1
        end
      end
    end
  end
end
rcon.print('moved=' .. moved)
"""
                r = c.raw_cmd("/sc " + lua.replace("\n", " "))
                # We don't log every tick to avoid spam; only log when something moved
                if r and "moved=0" not in r:
                    print(f"  tick: {r}")
            except Exception as exc:
                print(f"  tick error: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("follow_daemon stopped")
        raise SystemExit(0)
