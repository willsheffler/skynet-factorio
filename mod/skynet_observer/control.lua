-- skynet_observer / control.lua
-- Phase 0 + chat-pipe scaffold.

local CHAT_BUFFER_MAX = 100
local chat_buffer = {}

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

local function record_chat(player_index, message)
  local name = "<server>"
  if player_index and game.players[player_index] then
    name = game.players[player_index].name
  end
  table.insert(chat_buffer, {
    tick = game.tick,
    player_index = player_index,
    player_name = name,
    message = message,
  })
  while #chat_buffer > CHAT_BUFFER_MAX do
    table.remove(chat_buffer, 1)
  end
end

script.on_event(defines.events.on_console_chat, function(event)
  record_chat(event.player_index, event.message)
end)

commands.add_command(
  "skynet_state",
  "Emit a JSON snapshot of current game state.",
  function(event)
    game.print(helpers.table_to_json(snapshot()))
  end
)

commands.add_command(
  "skynet_say",
  "Make the skynet bot say something in chat.",
  function(event)
    local msg = event.parameter or "(no message)"
    game.print("[skynet] " .. msg)
  end
)

remote.add_interface("skynet", {
  ping = function()
    return { ok = true, tick = game.tick }
  end,
  state_snapshot = function()
    return snapshot()
  end,
  -- Return all chat-buffer entries with tick > since_tick.
  -- Pass 0 (or omit) for full buffer. Buffer is in-memory only, max 100 entries.
  chat_since = function(since_tick)
    since_tick = since_tick or 0
    local result = {}
    for _, entry in ipairs(chat_buffer) do
      if entry.tick > since_tick then
        table.insert(result, entry)
      end
    end
    return { tick = game.tick, entries = result }
  end,
  -- Clear the in-memory chat buffer.
  chat_clear = function()
    chat_buffer = {}
    return { ok = true, tick = game.tick }
  end,
})

script.on_init(function()
  game.print("[skynet_observer] initialized at tick " .. game.tick)
end)

script.on_load(function()
  -- chat_buffer is intentionally transient (not stored in `global`); resets on load.
end)
