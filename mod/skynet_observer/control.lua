-- skynet_observer / control.lua
-- Phase 0 scaffold. Two surfaces:
--   1. /skynet_state   — chat command; emits structured JSON snapshot of game state
--   2. RCON commands   — via remote-callable interface "skynet" with functions:
--         remote.call("skynet", "state_snapshot")
--         remote.call("skynet", "ping")
-- Outputs are placed in game.print so RCON callers see them in the response.

local function snapshot()
  local snap = {
    tick = game.tick,
    players = {},
    surfaces = {},
  }
  for _, player in pairs(game.players) do
    local pdata = {
      index = player.index,
      name = player.name,
      online = player.connected,
      surface = player.surface and player.surface.name or nil,
    }
    if player.character then
      pdata.position = { x = player.character.position.x, y = player.character.position.y }
      pdata.health = player.character.health
    end
    table.insert(snap.players, pdata)
  end
  for _, surface in pairs(game.surfaces) do
    table.insert(snap.surfaces, { name = surface.name, index = surface.index })
  end
  return snap
end

commands.add_command(
  "skynet_state",
  "Emit a JSON snapshot of current game state (skynet bot phase 0).",
  function(event)
    local snap = snapshot()
    game.print(helpers.table_to_json(snap))
  end
)

commands.add_command(
  "skynet_say",
  "Make the skynet bot say something in chat (phase 0 round-trip check).",
  function(event)
    local msg = event.parameter or "(no message)"
    game.print("[skynet] " .. msg)
  end
)

-- Remote interface for RCON / programmatic use.
remote.add_interface("skynet", {
  ping = function()
    return { ok = true, tick = game.tick }
  end,
  state_snapshot = function()
    return snapshot()
  end,
})

script.on_init(function()
  game.print("[skynet_observer] initialized at tick " .. game.tick)
end)

script.on_load(function()
  -- Nothing persistent yet; on_load reserved for Phase 1+.
end)
