install_base() {
    log "Installing base packages"
    sudo dnf install -y ardour9 carla pipewire-utils
}

install_groups() {
    IFS=":" read -ra groups <<< "$1"

    for g in "${groups[@]}"; do
        case "$g" in
            synths) sudo dnf install -y surge-xt helm yoshimi ;;
            fx) sudo dnf install -y lsp-plugins-lv2 lv2-airwindows ;;
            drums) sudo dnf install -y drumgizmo ;;
            mastering) sudo dnf install -y calf-plugins meterbridge ;;
        esac
    done
}
