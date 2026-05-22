"""RCON client wrapper for skynet_observer mod.

Thin wrapper around factorio_rcon.RCONClient that knows the conventions of
our mod's remote interface. Phase 0 surface: ping, state_snapshot, raw_cmd.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import factorio_rcon


class SkynetClient:
    """Phase 0 RCON client for the skynet_observer mod.

    Parameters
    ----------
    host : str
        IP/hostname of the headless Factorio server. Default 127.0.0.1.
    port : int
        RCON port. Default matches scripts/run_headless.sh (27015).
    password : str
        RCON password (read from runtime/factorio-headless/rcon-password if
        omitted).
    """

    DEFAULT_RCON_PASSWORD_FILE = (
        pathlib.Path(__file__).resolve().parents[2]
        / "runtime"
        / "factorio-headless"
        / "rcon-password"
    )

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27015,
        password: str | None = None,
    ) -> None:
        if password is None:
            password = self.DEFAULT_RCON_PASSWORD_FILE.read_text().strip()
        self._client = factorio_rcon.RCONClient(host, port, password)

    def __enter__(self) -> "SkynetClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def raw_cmd(self, cmd: str) -> str:
        """Send a raw Factorio chat/console command. Returns the server's response text."""
        return self._client.send_command(cmd)

    def ping(self) -> dict[str, Any]:
        """Call remote.skynet.ping(). Returns {ok: bool, tick: int}."""
        raw = self._client.send_command(
            "/sc rcon.print(helpers.table_to_json(remote.call('skynet', 'ping')))"
        )
        return json.loads(raw)

    def state_snapshot(self) -> dict[str, Any]:
        """Call remote.skynet.state_snapshot(). Returns the snapshot dict."""
        raw = self._client.send_command(
            "/sc rcon.print(helpers.table_to_json(remote.call('skynet', 'state_snapshot')))"
        )
        return json.loads(raw)

    def say(self, message: str) -> str:
        """Make the bot post a chat message via the mod's /skynet_say command."""
        return self._client.send_command(f"/skynet_say {message}")

    def chat_since(self, since_tick: int = 0) -> dict[str, Any]:
        """Pull chat-buffer entries with tick > since_tick. Returns {tick, entries: [...]}.

        Each entry: {tick, player_index, player_name, message}.
        """
        raw = self._client.send_command(
            f"/sc rcon.print(helpers.table_to_json(remote.call('skynet', 'chat_since', {since_tick})))"
        )
        return json.loads(raw)

    def chat_clear(self) -> dict[str, Any]:
        """Clear the in-memory chat buffer."""
        raw = self._client.send_command(
            "/sc rcon.print(helpers.table_to_json(remote.call('skynet', 'chat_clear')))"
        )
        return json.loads(raw)

    def chat_as(self, speaker: str, message: str) -> str | None:
        """Inject a synthetic chat message via on_console_chat. The mod's record_chat
        will store it in the buffer; the chat_pump daemon will relay it to the
        driving agent same as any real player chat.

        Use this for Vellum-side test commands. The speaker label is embedded in
        the message itself (e.g. "VELLUM: skynet follow me") because synthetic
        events have no real player_index.
        """
        # Lua-escape single quotes by doubling
        safe = message.replace("\\", "\\\\").replace("'", "\\'")
        # on_console_chat requires player_index; use Will's slot (1) as the channel,
        # speaker label embedded in message for downstream parsing.
        lua = (
            f"script.raise_event(defines.events.on_console_chat, "
            f"{{ player_index = 1, message = '{speaker}: {safe}' }})"
        )
        return self._client.send_command(f"/sc {lua}")
