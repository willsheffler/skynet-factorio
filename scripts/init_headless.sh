#!/usr/bin/env bash
# init_headless.sh — set up a runtime directory layout for the headless
# Factorio server instance. Idempotent.
#
# Layout created under <repo>/runtime/:
#   factorio-headless/
#     config/
#       config.ini          (write-dir paths)
#     mods/
#       (skynet_observer symlinked here on demand)
#     saves/
#     server-settings.json  (multiplayer config)
#     rcon-password         (chmod 600)

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_dir="${repo_root}/runtime/factorio-headless"
steam_dir="${HOME}/.local/share/Steam/steamapps/common/Factorio"

if [[ ! -x "${steam_dir}/bin/x64/factorio" ]]; then
  echo "ERROR: Steam Factorio binary not found at ${steam_dir}/bin/x64/factorio" >&2
  echo "Install Factorio via Steam first." >&2
  exit 1
fi

mkdir -p "${runtime_dir}"/{config,mods,saves,scenarios}

# Server-settings: pulled from the example, then customized.
if [[ ! -f "${runtime_dir}/server-settings.json" ]]; then
  cp "${steam_dir}/data/server-settings.example.json" "${runtime_dir}/server-settings.json"
  # Customize: name + visibility + auth.
  python3 - <<PY
import json, pathlib
p = pathlib.Path("${runtime_dir}/server-settings.json")
d = json.loads(p.read_text())
d["name"] = "Skynet bot host (Will-private)"
d["description"] = "Factorio multiplayer hosted by skynet-factorio; bot is a participant."
d["tags"] = ["skynet", "bot", "private"]
d["visibility"] = {"public": False, "lan": True, "steam": False}
d["require_user_verification"] = False
d["auto_pause"] = False
d["auto_pause_when_players_connect"] = False
# Username/token left blank for LAN-only mode
p.write_text(json.dumps(d, indent=2))
PY
fi

# RCON password: random hex, 600.
if [[ ! -f "${runtime_dir}/rcon-password" ]]; then
  head -c 16 /dev/urandom | xxd -p > "${runtime_dir}/rcon-password"
  chmod 600 "${runtime_dir}/rcon-password"
fi

# Minimal config.ini that points all write-paths into runtime_dir.
if [[ ! -f "${runtime_dir}/config/config.ini" ]]; then
  cat > "${runtime_dir}/config/config.ini" <<EOF
; Headless instance config for skynet-factorio. Do not edit by hand;
; rerun scripts/init_headless.sh to regenerate.

[path]
read-data=__PATH__executable__/../../data
write-data=${runtime_dir}

[other]
check-updates=false
enable-crash-log-uploading=false
EOF
fi

echo "Headless runtime initialized at ${runtime_dir}"
echo "RCON password file: ${runtime_dir}/rcon-password"
echo "Server settings:    ${runtime_dir}/server-settings.json"
echo
echo "Next: ./scripts/run_headless.sh <save-name>"
