LOG="$ROOT/logs/install.log"

init_log() {
    mkdir -p "$ROOT/logs"
    : > "$LOG"
}

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}
