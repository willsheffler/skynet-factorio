#!/usr/bin/env bash
# run_headless.sh — launch the headless Factorio server.
#
# Usage:
#   ./scripts/run_headless.sh <save-name>
#
# If the save does not exist, it is created with default map-gen-settings.
# The skynet_observer mod is symlinked into the runtime mods dir before launch.

set -euo pipefail

save_name="${1:-skynet_test}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_dir="${repo_root}/runtime/factorio-headless"
steam_dir="${HOME}/.local/share/Steam/steamapps/common/Factorio"
factorio_bin="${steam_dir}/bin/x64/factorio"
save_path="${runtime_dir}/saves/${save_name}.zip"
rcon_pw_file="${runtime_dir}/rcon-password"

if [[ ! -d "${runtime_dir}" ]]; then
  echo "ERROR: runtime dir not initialized. Run scripts/init_headless.sh first." >&2
  exit 1
fi

# Symlink the mod into the runtime mods dir (idempotent).
mod_src="${repo_root}/mod/skynet_observer"
mod_dst="${runtime_dir}/mods/skynet_observer"
if [[ -d "${mod_src}" && ! -L "${mod_dst}" ]]; then
  ln -s "${mod_src}" "${mod_dst}"
fi

# Enable our mod in mod-list.json (factorio convention).
mod_list="${runtime_dir}/mods/mod-list.json"
python3 - <<PY
import json, pathlib
p = pathlib.Path("${mod_list}")
if p.exists():
    d = json.loads(p.read_text())
else:
    d = {"mods": [{"name": "base", "enabled": True}]}
names = {m["name"] for m in d.get("mods", [])}
if "skynet_observer" not in names:
    d.setdefault("mods", []).append({"name": "skynet_observer", "enabled": True})
p.write_text(json.dumps(d, indent=2))
PY

# Create the save if missing.
if [[ ! -f "${save_path}" ]]; then
  echo "Save not found at ${save_path} — creating default."
  "${factorio_bin}" \
    --config "${runtime_dir}/config/config.ini" \
    --mod-directory "${runtime_dir}/mods" \
    --create "${save_path}"
fi

# Launch the headless server.
exec "${factorio_bin}" \
  --config "${runtime_dir}/config/config.ini" \
  --mod-directory "${runtime_dir}/mods" \
  --start-server "${save_path}" \
  --server-settings "${runtime_dir}/server-settings.json" \
  --port 34197 \
  --rcon-port 27015 \
  --rcon-password "$(cat "${rcon_pw_file}")"
