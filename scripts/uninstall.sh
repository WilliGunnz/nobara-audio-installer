#!/usr/bin/env bash

echo "Uninstalling Nobara Audio Production Installer components..."

sudo dnf remove -y ardour9 carla surge-xt helm yoshimi drumgizmo lsp-plugins-lv2

echo "Removing realtime tweaks (manual cleanup required):"
echo " - /etc/sysctl.conf entries"
echo " - user groups (pipewire/realtime)"

echo "Done."
