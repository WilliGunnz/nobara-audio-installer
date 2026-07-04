welcome() {
zenity --info --title="Installer" \
--text="Nobara Audio Production Installer v5"
}

select_profile() {
zenity --list --title="Profile" \
--column="Mode" \
"Beginner" \
"Producer" \
"Pro Studio"
}

select_plugins() {
zenity --list --checklist \
--title="Plugins" \
--column="Use" --column="Group" \
TRUE synths \
TRUE fx \
TRUE drums \
FALSE mastering \
--separator=":"
}

done_screen() {
zenity --info --title="Done" \
--text="Installation complete. Please reboot."
}
