"""skynet-harness tools — Python wrappers for common Factorio operations.

Inline-port from FLE's tool pattern (vendored at ../vendored/factorio-learning-environment).
We don't depend on FLE's runtime (Docker, FactorioLuaScriptManager, FactorioNamespace);
we use our own RCON connection (SkynetClient) and send hand-crafted Lua.

API shape mirrors FLE so future swap-in is plausible.
"""

from __future__ import annotations

import json
from typing import Optional

from .client import SkynetClient


class Tools:
    """Composable tools layer over SkynetClient.

    Usage:
        with SkynetClient() as c:
            t = Tools(c)
            t.place_entity("solar-panel", (40, 0))
            entities = t.find_entities(area=(0, 0, 50, 20), name="solar-panel")
    """

    def __init__(self, client: SkynetClient) -> None:
        self._c = client

    # ---------- placement / removal ----------

    def place_entity(
        self,
        name: str,
        position: tuple[float, float],
        direction: str = "north",
        force: str = "player",
    ) -> dict:
        """Place an entity. Direction one of: north/east/south/west.
        Returns {ok: bool, unit_number: int|None, position: (x,y)|None, error: str|None}.
        """
        dir_map = {"north": 0, "east": 4, "south": 8, "west": 12}
        d = dir_map.get(direction.lower(), 0)
        x, y = position
        lua = (
            f"local e = game.surfaces.nauvis.create_entity{{name='{name}', "
            f"position={{{x},{y}}}, direction={d}, force='{force}'}}; "
            f"if e and e.valid then rcon.print(helpers.table_to_json("
            f"{{ok=true, unit_number=e.unit_number, x=e.position.x, y=e.position.y}})) "
            f"else rcon.print(helpers.table_to_json({{ok=false, error='create_entity returned nil'}})) end"
        )
        try:
            return json.loads(self._c.raw_cmd("/sc " + lua))
        except (json.JSONDecodeError, TypeError):
            return {"ok": False, "error": "no JSON response"}

    def place_blueprint(
        self,
        entities: list[tuple[str, tuple[float, float]]],
        direction: str = "north",
    ) -> int:
        """Place multiple entities at once. Returns count successfully placed."""
        dir_map = {"north": 0, "east": 4, "south": 8, "west": 12}
        d = dir_map.get(direction.lower(), 0)
        parts = []
        for name, (x, y) in entities:
            parts.append(
                f"local e = s.create_entity{{name='{name}', position={{{x},{y}}}, "
                f"direction={d}, force='player'}}; if e and e.valid then n=n+1 end"
            )
        lua = "local s = game.surfaces.nauvis; local n=0; " + "; ".join(parts) + f"; rcon.print('{name}_count=' .. n)"
        return int(self._c.raw_cmd("/sc " + lua).split("=")[-1])

    # ---------- queries ----------

    def find_entities(
        self,
        area: Optional[tuple[float, float, float, float]] = None,
        name: Optional[str] = None,
        position: Optional[tuple[float, float]] = None,
        radius: Optional[float] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Find entities. Filter by area (x1,y1,x2,y2) OR position+radius. Optional name.
        Returns list of {name, x, y, unit_number, health}.
        """
        if area:
            x1, y1, x2, y2 = area
            filter_str = f"area={{{{{x1},{y1}}},{{{x2},{y2}}}}}"
        elif position and radius is not None:
            px, py = position
            filter_str = f"position={{{px},{py}}}, radius={radius}"
        else:
            return []
        if name:
            filter_str += f", name='{name}'"
        lua = (
            f"local es = game.surfaces.nauvis.find_entities_filtered{{{filter_str}, limit={limit}}}; "
            f"local r = {{}}; for i,e in ipairs(es) do r[i] = {{name=e.name, x=e.position.x, "
            f"y=e.position.y, unit_number=e.unit_number, health=e.health}} end; "
            f"rcon.print(helpers.table_to_json(r))"
        )
        try:
            r = json.loads(self._c.raw_cmd("/sc " + lua))
            if isinstance(r, dict):
                r = [r[k] for k in sorted(r.keys(), key=lambda x: int(x))]
            return r
        except (json.JSONDecodeError, TypeError):
            return []

    def nearest(self, name: str, from_position: tuple[float, float], max_radius: float = 100.0) -> Optional[dict]:
        """Find the nearest entity of name from a position, within max_radius. Returns dict or None."""
        es = self.find_entities(position=from_position, radius=max_radius, name=name, limit=200)
        if not es:
            return None
        fx, fy = from_position
        return min(es, key=lambda e: (e["x"] - fx) ** 2 + (e["y"] - fy) ** 2)

    # ---------- inventory ----------

    def give_item(self, entity_storage_name: str, item_name: str, count: int = 1) -> int:
        """Conjure items into a bot's spider_trunk inventory. Returns count inserted.
        entity_storage_name: "facet_char" / "vellum_char" / "skynet_char"
        """
        lua = (
            f"local e = storage.{entity_storage_name}; "
            f"if not (e and e.valid) then rcon.print('0'); return end "
            f"local inv = e.get_inventory(defines.inventory.spider_trunk); "
            f"local n = inv.insert{{name='{item_name}', count={count}}}; rcon.print(tostring(n))"
        )
        r = self._c.raw_cmd("/sc " + lua)
        try:
            return int(r)
        except (ValueError, TypeError):
            return 0

    def inspect_inventory(self, entity_storage_name: str) -> dict[str, int]:
        """Return {item_name: count} for the bot's spider_trunk."""
        lua = (
            f"local e = storage.{entity_storage_name}; "
            f"if not (e and e.valid) then rcon.print('{{}}'); return end "
            f"local inv = e.get_inventory(defines.inventory.spider_trunk); "
            f"local contents = inv.get_contents(); "
            f"local r = {{}}; for _,item in ipairs(contents) do r[item.name] = (r[item.name] or 0) + item.count end; "
            f"rcon.print(helpers.table_to_json(r))"
        )
        try:
            return json.loads(self._c.raw_cmd("/sc " + lua))
        except (json.JSONDecodeError, TypeError):
            return {}

    # ---------- movement ----------

    def move_to(self, bot_storage_name: str, position: tuple[float, float]) -> bool:
        """Set autopilot for a bot. Returns True if dispatch succeeded."""
        x, y = position
        lua = (
            f"local b = storage.{bot_storage_name}; "
            f"if not (b and b.valid) then rcon.print('false'); return end "
            f"b.autopilot_destination = {{{x},{y}}}; rcon.print('true')"
        )
        return self._c.raw_cmd("/sc " + lua).strip() == "true"

    def teleport(self, bot_storage_name: str, position: tuple[float, float]) -> bool:
        """Immediate teleport. Returns True if succeeded."""
        x, y = position
        lua = (
            f"local b = storage.{bot_storage_name}; "
            f"if not (b and b.valid) then rcon.print('false'); return end "
            f"local ok = b.teleport({{{x},{y}}}); rcon.print(tostring(ok))"
        )
        return self._c.raw_cmd("/sc " + lua).strip() == "true"

    # ---------- chat ----------

    def say(self, speaker: str, message: str) -> None:
        """Emit a chat message via _G.skynet_say_as. Captured in chat_buffer."""
        safe = message.replace("\\", "\\\\").replace("'", "\\'")
        self._c.raw_cmd(f"/sc _G.skynet_say_as('{speaker}', '{safe}')")


__all__ = ["Tools"]
