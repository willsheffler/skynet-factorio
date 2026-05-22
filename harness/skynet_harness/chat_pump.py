"""chat_pump — poll the Factorio chat buffer and fire inter-agent messages to the driving agent.

Each batch of new chat messages becomes one inter-agent message (one turn for the
driving agent). Default driving agent is `vellum`; override with --recipient.

Run with: uv run python -m skynet_harness.chat_pump
Stop with: SIGTERM / Ctrl-C
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
import sys
import time

from .client import SkynetClient


HARNESS_CTL = (
    "/home/sheffler/.openclaw/workspace/pensieve_backend/bin/harness_ctl.sh"
)


def fire_chat_batch(sender: str, recipient: str, thread: str, entries: list[dict]) -> str | None:
    """Fire an inter-agent message containing the chat batch. Returns message_id or None."""
    lines = ["Factorio chat relay (skynet-factorio bot). New messages:"]
    for e in entries:
        lines.append(f"  [tick {e['tick']}] {e['player_name']}: {e['message']}")
    text = "\n".join(lines)
    cmd = [
        HARNESS_CTL,
        "run-inter-agent-message",
        "--sender", sender,
        "--recipient", recipient,
        "--thread", thread,
        "--text", text,
        "--reply-mode", "optional",
        "--timeout-seconds", "15",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        # Try to parse message_id from JSON output; OK if we can't (TimeoutError-despite-delivery)
        try:
            parsed = json.loads(result.stdout)
            return parsed.get("message_id") or parsed.get("result", {}).get("message_id")
        except json.JSONDecodeError:
            return None
    except subprocess.TimeoutExpired:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", default="eval-haiku", help="Driving agent to receive chat turns (default: eval-haiku)")
    parser.add_argument("--sender", default="vellum", help="Sender label for inter-agent message (default: vellum)")
    parser.add_argument("--thread", default="skynet_factorio_chat_relay", help="Thread name")
    parser.add_argument("--interval-s", type=float, default=5.0, help="Poll interval seconds")
    parser.add_argument("--no-batch", action="store_true", help="One inter-agent message per chat message (high noise)")
    args = parser.parse_args()

    print(f"chat_pump starting: interval={args.interval_s}s recipient={args.recipient} sender={args.sender}")
    last_tick = 0
    with SkynetClient() as c:
        # Skip any pre-existing chat
        try:
            initial = c.chat_since(0)
            last_tick = initial.get("tick", 0)
            print(f"  starting at tick {last_tick}; skipped {len(initial.get('entries', []) or [])} pre-existing entries")
        except Exception as exc:
            print(f"  initial chat_since failed: {exc}; starting from tick 0")
            last_tick = 0

        while True:
            try:
                resp = c.chat_since(last_tick)
            except Exception as exc:
                print(f"  poll error (will retry): {exc}", file=sys.stderr)
                time.sleep(args.interval_s)
                continue

            entries = resp.get("entries") or []
            # Coerce Lua-style dict-with-int-keys into list if needed
            if isinstance(entries, dict):
                entries = [entries[k] for k in sorted(entries.keys(), key=lambda x: int(x))]

            # Filter out bot-output entries (those starting with "[" — bot speaker label)
            # to avoid feedback loops where eval-haiku reads its own output.
            entries = [e for e in entries if not str(e.get("message", "")).lstrip().startswith("[")]
            if entries:
                if args.no_batch:
                    for e in entries:
                        msg_id = fire_chat_batch(args.sender, args.recipient, args.thread, [e])
                        print(f"  fired single → {msg_id or '?'}: {e['player_name']}: {e['message']!r}")
                else:
                    msg_id = fire_chat_batch(args.sender, args.recipient, args.thread, entries)
                    print(f"  fired batch ({len(entries)} msgs) → {msg_id or '?'}")
                last_tick = resp.get("tick", last_tick)
            else:
                last_tick = resp.get("tick", last_tick)

            time.sleep(args.interval_s)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("chat_pump stopped")
        raise SystemExit(0)
