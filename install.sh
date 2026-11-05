#!/usr/bin/env bash
# ===================================================================
# Everforest Dark Theme - Installer & Configurator
# For GNOME Shell 51 & GTK 3 / 4 (Libadwaita)
# ===================================================================

set -e

THEME_NAME="Everforest-Dark"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_THEMES_DIR="$HOME/.themes/$THEME_NAME"
USER_LOCAL_THEMES_DIR="$HOME/.local/share/themes/$THEME_NAME"
GTK4_CONFIG_DIR="$HOME/.config/gtk-4.0"
USER_THEME_UUID="user-theme@gnome-shell-extensions.gcampax.github.com"

# Colors for terminal output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

print_title() {
    echo -e "\n${BOLD}${GREEN}=== $1 ===${RESET}\n"
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

check_dependencies() {
    print_info "Verifying system environment..."
    if command -v gnome-shell &>/dev/null; then
        SHELL_VER=$(gnome-shell --version)
        print_success "Found $SHELL_VER"
    else
        print_warning "GNOME Shell binary not detected in PATH."
    fi
}

install_theme() {
    print_title "Installing $THEME_NAME"

    # 1. Install to ~/.themes and ~/.local/share/themes
    print_info "Copying theme files to $USER_THEMES_DIR..."
    mkdir -p "$USER_THEMES_DIR"
    cp "$SCRIPT_DIR/index.theme" "$USER_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gnome-shell" "$USER_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gtk-3.0" "$USER_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gtk-4.0" "$USER_THEMES_DIR/"

    print_info "Copying theme files to $USER_LOCAL_THEMES_DIR..."
    mkdir -p "$USER_LOCAL_THEMES_DIR"
    cp "$SCRIPT_DIR/index.theme" "$USER_LOCAL_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gnome-shell" "$USER_LOCAL_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gtk-3.0" "$USER_LOCAL_THEMES_DIR/"
    cp -r "$SCRIPT_DIR/gtk-4.0" "$USER_LOCAL_THEMES_DIR/"

    print_success "Theme directories installed."

    # 2. Setup Libadwaita / GTK4 in ~/.config/gtk-4.0
    print_info "Configuring Libadwaita in $GTK4_CONFIG_DIR..."
    mkdir -p "$GTK4_CONFIG_DIR"

    if [ -f "$GTK4_CONFIG_DIR/gtk.css" ] && [ ! -L "$GTK4_CONFIG_DIR/gtk.css" ]; then
        if [ ! -f "$GTK4_CONFIG_DIR/gtk.css.bak" ]; then
            print_info "Backing up existing gtk.css to gtk.css.bak"
            cp "$GTK4_CONFIG_DIR/gtk.css" "$GTK4_CONFIG_DIR/gtk.css.bak"
        fi
    fi

    cp "$SCRIPT_DIR/gtk-4.0/gtk.css" "$GTK4_CONFIG_DIR/gtk.css"
    cp "$SCRIPT_DIR/gtk-4.0/gtk-dark.css" "$GTK4_CONFIG_DIR/gtk-dark.css"
    print_success "Libadwaita / GTK4 configuration applied."

    # 3. Setup Flatpak overrides if Flatpak is present
    if command -v flatpak &>/dev/null; then
        print_info "Detected Flatpak; granting filesystem access to ~/.themes..."
        flatpak --user override --filesystem="$HOME/.themes:ro" 2>/dev/null || true
        flatpak --user override --filesystem="$HOME/.local/share/themes:ro" 2>/dev/null || true
        
        # Propagate gtk.css to existing flatpak app configs
        for app_dir in "$HOME/.var/app"/*; do
            if [ -d "$app_dir/config" ]; then
                mkdir -p "$app_dir/config/gtk-4.0"
                cp "$SCRIPT_DIR/gtk-4.0/gtk.css" "$app_dir/config/gtk-4.0/gtk.css" 2>/dev/null || true
                cp "$SCRIPT_DIR/gtk-4.0/gtk-dark.css" "$app_dir/config/gtk-4.0/gtk-dark.css" 2>/dev/null || true
            fi
        done
        print_success "Flatpak integration configured."
    fi

    # 4. Enable User Themes GNOME Shell Extension
    if command -v gnome-extensions &>/dev/null; then
        print_info "Enabling user-theme extension..."
        gnome-extensions enable "$USER_THEME_UUID" 2>/dev/null || true
    fi

    # 5. Apply GSettings & dconf
    print_info "Applying desktop interface settings..."
    gsettings set org.gnome.desktop.interface gtk-theme "$THEME_NAME" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface accent-color 'green' 2>/dev/null || true

    # Shell theme via dconf (Toggle to force GNOME Shell to reload CSS live on Wayland)
    dconf write /org/gnome/shell/extensions/user-theme/name "''" 2>/dev/null || true
    sleep 0.2
    dconf write /org/gnome/shell/extensions/user-theme/name "'$THEME_NAME'" 2>/dev/null || true

    # 6. Setup Mozilla Firefox Theme in User Profiles
    print_info "Configuring Firefox user profiles..."
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

    FF_PROFILES=()
    for root in "${FF_DIRS[@]}"; do
        if [ -d "$root" ]; then
            if [ -f "$root/profiles.ini" ]; then
                while IFS='=' read -r key val; do
                    if [ "$key" = "Path" ]; then
                        p_full="$root/$val"
                        if [ -d "$p_full" ]; then
                            FF_PROFILES+=("$p_full")
                        fi
                    fi
                done < "$root/profiles.ini"
            fi
            for d in "$root"/*; do
                if [ -d "$d" ] && [[ "$d" == *default* || -f "$d/prefs.js" ]]; then
                    FF_PROFILES+=("$d")
                fi
            done
        fi
    done

    if [ ${#FF_PROFILES[@]} -gt 0 ]; then
        IFS=" " read -r -a UNIQUE_FF_PROFILES <<< "$(printf '%s\n' "${FF_PROFILES[@]}" | sort -u | tr '\n' ' ')"
        FF_COUNT=0
        for prof in "${UNIQUE_FF_PROFILES[@]}"; do
            if [ -d "$prof" ]; then
                mkdir -p "$prof/chrome"
                if [ -f "$SCRIPT_DIR/firefox/userChrome.css" ]; then
                    cp "$SCRIPT_DIR/firefox/userChrome.css" "$prof/chrome/userChrome.css"
                fi
                if [ -f "$SCRIPT_DIR/firefox/userContent.css" ]; then
                    cp "$SCRIPT_DIR/firefox/userContent.css" "$prof/chrome/userContent.css"
                fi

                USER_JS="$prof/user.js"
                touch "$USER_JS"
                if ! grep -q "toolkit.legacyUserProfileCustomizations.stylesheets" "$USER_JS" 2>/dev/null; then
                    echo 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' >> "$USER_JS"
                fi
                if ! grep -q "browser.tabs.drawInTitlebar" "$USER_JS" 2>/dev/null; then
                    echo 'user_pref("browser.tabs.drawInTitlebar", true);' >> "$USER_JS"
                fi
                if ! grep -q "svg.context-properties.content.enabled" "$USER_JS" 2>/dev/null; then
                    echo 'user_pref("svg.context-properties.content.enabled", true);' >> "$USER_JS"
                fi
                FF_COUNT=$((FF_COUNT + 1))
            fi
        done
        if [ $FF_COUNT -gt 0 ]; then
            print_success "Applied theme to $FF_COUNT Firefox profile(s)."
        fi
    fi

    print_title "Theme Applied Successfully!"
    echo -e "Summary of configured components:"
    echo -e "  • ${BOLD}GNOME Shell Theme:${RESET} $THEME_NAME"
    echo -e "  • ${BOLD}GTK 3 Theme:${RESET}       $THEME_NAME"
    echo -e "  • ${BOLD}GTK 4 / Libadwaita:${RESET} Everforest Dark Palette Active"
    echo -e "  • ${BOLD}Firefox Theming:${RESET}   userChrome.css Active ($FF_COUNT profiles)"
    echo -e "  • ${BOLD}Accent Color:${RESET}       Green (#a7c080)"
    echo -e "  • ${BOLD}Color Scheme:${RESET}       Prefer Dark"
    echo -e ""
    echo -e "${YELLOW}Note:${RESET} If GNOME Shell does not refresh immediately, press ${BOLD}Alt + F2${RESET}, type ${BOLD}r${RESET} and hit ${BOLD}Enter${RESET} (on X11), or log out and log back in (on Wayland)."
}

uninstall_theme() {
    if [ -x "$SCRIPT_DIR/uninstall.sh" ]; then
        "$SCRIPT_DIR/uninstall.sh"
    else
        print_title "Uninstalling $THEME_NAME"
        gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita' 2>/dev/null || true
        gsettings set org.gnome.desktop.interface color-scheme 'default' 2>/dev/null || true
        gsettings set org.gnome.desktop.interface accent-color 'blue' 2>/dev/null || true
        dconf write /org/gnome/shell/extensions/user-theme/name "''" 2>/dev/null || true
        rm -rf "$USER_THEMES_DIR" "$USER_LOCAL_THEMES_DIR"
        if [ -f "$GTK4_CONFIG_DIR/gtk.css.bak" ]; then
            mv "$GTK4_CONFIG_DIR/gtk.css.bak" "$GTK4_CONFIG_DIR/gtk.css"
        else
            rm -f "$GTK4_CONFIG_DIR/gtk.css" "$GTK4_CONFIG_DIR/gtk-dark.css"
        fi
        print_success "Everforest theme removed and default settings restored."
    fi
}

show_status() {
    print_title "Current GNOME Theme Status"

    echo -n "  GTK Theme:            "
    gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null || echo "Unknown"

    echo -n "  Color Scheme:         "
    gsettings get org.gnome.desktop.interface color-scheme 2>/dev/null || echo "Unknown"

    echo -n "  Accent Color:         "
    gsettings get org.gnome.desktop.interface accent-color 2>/dev/null || echo "Unknown"

    echo -n "  GNOME Shell Theme:    "
    dconf read /org/gnome/shell/extensions/user-theme/name 2>/dev/null || echo "Default"

    echo -n "  User-Theme Extension: "
    if command -v gnome-extensions &>/dev/null; then
        gnome-extensions info "$USER_THEME_UUID" 2>/dev/null | grep -i "Estado\|State" || echo "Unknown"
    fi
}

case "$1" in
    --uninstall|-u)
        uninstall_theme
        ;;
    --status|-s)
        show_status
        ;;
    --help|-h)
        echo "Usage: ./install.sh [OPTION]"
        echo "Options:"
        echo "  (no args), --install  Install and activate Everforest-Dark theme"
        echo "  --uninstall, -u       Remove Everforest-Dark and restore defaults"
        echo "  --status, -s          Show current GNOME theming configuration"
        echo "  --help, -h            Show this help message"
        ;;
    *)
        check_dependencies
        install_theme
        ;;
esac
