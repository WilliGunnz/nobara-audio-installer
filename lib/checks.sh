check_system() {
    command -v dnf >/dev/null || {
        echo "DNF not found"
        return 1
    }
}

check_dependencies() {
    for c in zenity sudo bash; do
        command -v "$c" >/dev/null || return 1
    done
}
