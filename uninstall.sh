#!/usr/bin/env bash
# ===================================================================
# Everforest Dark Theme - Standalone Uninstaller
# For GNOME Shell 51 & GTK 3 / 4 (Libadwaita)
# ===================================================================

set -e

THEME_NAME="Everforest-Dark"
USER_THEMES_DIR="$HOME/.themes/$THEME_NAME"
USER_LOCAL_THEMES_DIR="$HOME/.local/share/themes/$THEME_NAME"
GTK4_CONFIG_DIR="$HOME/.config/gtk-4.0"

# Colors for terminal output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

print_title() {
    echo -e "\n${BOLD}${YELLOW}=== $1 ===${RESET}\n"
}

print_success() {
    echo -e " ${GREEN}[✓]${RESET} $1"
}

print_info() {
    echo -e " ${BLUE}[i]${RESET} $1"
}

print_warning() {
    echo -e " ${YELLOW}[!]${RESET} $1"
}

print_error() {
    echo -e " ${RED}[✗]${RESET} $1"
}

print_title "Uninstalling $THEME_NAME"

# 1. Reset GNOME Shell Theme
print_info "Resetting GNOME Shell theme to default..."
dconf write /org/gnome/shell/extensions/user-theme/name "''" 2>/dev/null || true
print_success "GNOME Shell theme reset."

# 2. Reset GTK and Desktop Interface Settings
print_info "Restoring GTK theme to 'Adwaita'..."
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita' 2>/dev/null || true

print_info "Restoring color scheme to 'default'..."
gsettings set org.gnome.desktop.interface color-scheme 'default' 2>/dev/null || true

print_info "Restoring accent color to 'blue'..."
gsettings set org.gnome.desktop.interface accent-color 'blue' 2>/dev/null || true
print_success "Desktop interface settings restored."

# 3. Remove installed theme directories
if [ -d "$USER_THEMES_DIR" ]; then
    print_info "Removing $USER_THEMES_DIR..."
    rm -rf "$USER_THEMES_DIR"
    print_success "Removed $USER_THEMES_DIR"
fi

if [ -d "$USER_LOCAL_THEMES_DIR" ]; then
    print_info "Removing $USER_LOCAL_THEMES_DIR..."
    rm -rf "$USER_LOCAL_THEMES_DIR"
    print_success "Removed $USER_LOCAL_THEMES_DIR"
fi

# 4. Restore or clean Libadwaita / GTK4 configs
if [ -f "$GTK4_CONFIG_DIR/gtk.css.bak" ]; then
    print_info "Restoring backup $GTK4_CONFIG_DIR/gtk.css..."
    mv "$GTK4_CONFIG_DIR/gtk.css.bak" "$GTK4_CONFIG_DIR/gtk.css"
    rm -f "$GTK4_CONFIG_DIR/gtk-dark.css"
    print_success "Restored original gtk.css"
elif [ -f "$GTK4_CONFIG_DIR/gtk.css" ]; then
    # Check if it was Everforest
    if grep -q "Everforest" "$GTK4_CONFIG_DIR/gtk.css" 2>/dev/null; then
        print_info "Removing Everforest config in $GTK4_CONFIG_DIR..."
        rm -f "$GTK4_CONFIG_DIR/gtk.css" "$GTK4_CONFIG_DIR/gtk-dark.css"
        print_success "Cleaned $GTK4_CONFIG_DIR"
    fi
fi

# 5. Clean Flatpak overrides & injected CSS
if [ -d "$HOME/.var/app" ]; then
    print_info "Checking Flatpak app configs..."
    for app_dir in "$HOME/.var/app"/*; do
        if [ -f "$app_dir/config/gtk-4.0/gtk.css" ]; then
            if grep -q "Everforest" "$app_dir/config/gtk-4.0/gtk.css" 2>/dev/null; then
                rm -f "$app_dir/config/gtk-4.0/gtk.css" "$app_dir/config/gtk-4.0/gtk-dark.css" 2>/dev/null || true
            fi
        fi
    done
    print_success "Cleaned Flatpak custom styles."
fi

# 6. Clean Firefox custom chrome stylesheets
print_info "Checking Firefox profiles..."
FF_DIRS=(
    "$HOME/.config/mozilla/firefox"
    "$HOME/.mozilla/firefox"
    "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox"
    "$HOME/snap/firefox/common/.mozilla/firefox"
    "$HOME/.config/librewolf"
    "$HOME/.librewolf"
    "$HOME/.var/app/io.gitlab.librewolf-community/.librewolf"
    "$HOME/.config/waterfox"
    "$HOME/.waterfox"
)
for root in "${FF_DIRS[@]}"; do
    if [ -d "$root" ]; then
        for d in "$root"/*; do
            if [ -d "$d/chrome" ]; then
                rm -f "$d/chrome/userChrome.css" "$d/chrome/userContent.css"
                rmdir "$d/chrome" 2>/dev/null || true
            fi
        done
    fi
done
print_success "Cleaned Firefox custom styles."

print_title "Theme Successfully Uninstalled!"
echo -e "Summary of restored defaults:"
echo -e "  • ${BOLD}GNOME Shell Theme:${RESET} Default"
echo -e "  • ${BOLD}GTK 3 Theme:${RESET}       Adwaita"
echo -e "  • ${BOLD}GTK 4 / Libadwaita:${RESET} Default (Everforest overrides removed)"
echo -e "  • ${BOLD}Accent Color:${RESET}       Blue"
echo -e "  • ${BOLD}Color Scheme:${RESET}       Default"
echo -e ""
echo -e "${YELLOW}Note:${RESET} If GNOME Shell does not refresh immediately, press ${BOLD}Alt + F2${RESET}, type ${BOLD}r${RESET} and hit ${BOLD}Enter${RESET} (on X11), or log out and log back in (on Wayland)."
