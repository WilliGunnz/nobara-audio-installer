setup_realtime() {
    log "Realtime setup"

    sudo dnf install -y realtime-setup rtkit

    sudo usermod -aG pipewire,realtime "$USER"

    if ! grep -q "vm.swappiness=10" /etc/sysctl.conf; then
        echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
    fi
}
