"""Smoke-test script: connect to the running headless server and round-trip
a ping + state snapshot. Requires the server to be running (see
scripts/run_headless.sh).

Run with: uv run python -m skynet_harness.smoke
"""

from __future__ import annotations

import json
import sys

from .client import SkynetClient


def main() -> int:
    print("Connecting to headless Factorio on 127.0.0.1:27015 ...")
    try:
        with SkynetClient() as c:
            print("  ping ->", json.dumps(c.ping()))
            snap = c.state_snapshot()
            print("  state_snapshot ->")
            print(json.dumps(snap, indent=2))
            print("  say -> ", c.say("hello from python smoke test"))
    except Exception as exc:
        print("SMOKE FAILED:", type(exc).__name__, exc, file=sys.stderr)
        return 1
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
