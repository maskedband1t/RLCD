#!/usr/bin/env bash
# Fetch the public simulators and robot models the benches build on into third_party/.
# Nothing here is committed to this repository (see .gitignore); each source keeps its own licence.
#
#   scripts/fetch_third_party.sh            # everything below
#   scripts/fetch_third_party.sh drone      # one bench: drone | humanoid | ffw
#
# The sorting cell (src/cell, `python -m cell.run`) needs none of this: requirements.txt is enough.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third_party

fetch() {  # fetch <dest> <github owner/repo> <commit or "HEAD">
  local dest="third_party/$1" repo="$2" rev="$3"
  if [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
    echo "skip  $dest (already present)"; return
  fi
  echo "fetch $dest  <-  github.com/$repo @ $rev"
  git clone --quiet --filter=blob:none "https://github.com/$repo" "$dest"
  [ "$rev" = "HEAD" ] || git -C "$dest" checkout --quiet "$rev"
}

drone() {     # src/sim: the drone testbed is a fork of jev-drone and imports its flight.py and tactics.py
  fetch jev-drone RomanSlack/jev-drone 974b47378c14c6dcf7d11f7c813fba0f5f4d8b6a
}
humanoid() {  # src/humanoid fetch room: Unitree G1 model, scene and the walking policy that ships with it
  fetch mujoco_playground google-deepmind/mujoco_playground ef4fefc13033c0468af4ef651847f5348af0c7d7
  fetch mujoco_menagerie  google-deepmind/mujoco_menagerie  4d038b3feae26ec82b46a4d586379114012a8ac7
}
ffw() {       # src/humanoid/ffw_*: ROBOTIS AI Worker (FFW), the commit the record was measured on
  if [ -d third_party/robotis_ffw ]; then echo "skip  third_party/robotis_ffw (already present)"; return; fi
  local tmp; tmp="$(mktemp -d)"
  echo "fetch third_party/robotis_ffw  <-  github.com/ROBOTIS-GIT/robotis_mujoco_menagerie @ d8344c0"
  git clone --quiet --filter=blob:none https://github.com/ROBOTIS-GIT/robotis_mujoco_menagerie "$tmp/rmm"
  git -C "$tmp/rmm" checkout --quiet d8344c0dbe7a00208d0301111523dde65efc174a
  cp -R "$tmp/rmm/robotis_ffw" third_party/robotis_ffw
  rm -rf "$tmp"
}

case "${1:-all}" in
  drone) drone ;;
  humanoid) humanoid ;;
  ffw) ffw ;;
  all) drone; humanoid; ffw ;;
  *) echo "usage: $0 [drone|humanoid|ffw|all]"; exit 2 ;;
esac

echo
echo "Done. The FFW pin (d8344c0) is the commit the record was measured on; the other pins are the upstream commits verified on 2026-10-05."
