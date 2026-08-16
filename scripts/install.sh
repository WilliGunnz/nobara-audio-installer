#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$ROOT/lib/common.sh"
source "$ROOT/lib/logger.sh"
source "$ROOT/lib/checks.sh"
source "$ROOT/lib/gui.sh"
source "$ROOT/lib/packages.sh"
source "$ROOT/lib/realtime.sh"

init_log
banner

check_system || exit 1
check_dependencies || exit 1

welcome

PROFILE=$(select_profile)
GROUPS=$(select_plugins)

log "Profile=$PROFILE"
log "Groups=$GROUPS"

install_base
install_groups "$GROUPS"

if [[ "$PROFILE" != "Beginner" ]]; then
    setup_realtime
fi

done_screen
