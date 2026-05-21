"""Diagnostic: try several RCON command shapes to find one that works.

Run with: uv run python -m skynet_harness.diag
"""

from __future__ import annotations

import pathlib

import factorio_rcon


def main() -> None:
    pw = (
        pathlib.Path(__file__).resolve().parents[2]
        / "runtime"
        / "factorio-headless"
        / "rcon-password"
    ).read_text().strip()
    c = factorio_rcon.RCONClient("127.0.0.1", 27015, pw)

    cases = [
        # 1. plain /help — should always work
        "/help",
        # 2. /skynet_state — our mod's command (prints to game.print)
        "/skynet_state",
        # 3. /c with rcon.print
        "/c rcon.print('hello from /c')",
        # 4. /sc with rcon.print
        "/sc rcon.print('hello from /sc')",
        # 5. /sc with remote call
        "/sc rcon.print(helpers.table_to_json(remote.call('skynet', 'ping')))",
        # 6. plain Lua expression
        "/c print(game.tick)",
        # 7. /silent-command (full form of /sc)
        "/silent-command rcon.print(1+1)",
    ]

    for i, cmd in enumerate(cases, 1):
        try:
            r = c.send_command(cmd)
            print(f"[{i}] {cmd!r}")
            print(f"    -> {r!r}")
        except Exception as exc:
            print(f"[{i}] {cmd!r}")
            print(f"    EXC {type(exc).__name__}: {exc}")
    c.close()


if __name__ == "__main__":
    main()
