#!/usr/bin/env bash
# ===================================================================
# GNOME Theme Studio — Quick Settings Extension Installer
# ===================================================================
set -e

UUID="theme-studio@angelaguayo.github.io"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXT_DEST="$HOME/.local/share/gnome-shell/extensions/$UUID"

GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "\n${BOLD}${GREEN}=== GNOME Theme Studio Extension Installer ===${RESET}\n"

# 1. Check GNOME Shell
if command -v gnome-shell &>/dev/null; then
    SHELL_VER=$(gnome-shell --version)
    echo -e " ${GREEN}[✓]${RESET} Detectado: ${BOLD}$SHELL_VER${RESET}"
else
    echo -e " ${YELLOW}[!]${RESET} GNOME Shell no se encontró en el PATH. ¿Estás en un entorno GNOME?"
fi

# 2. Prepare extensions directory
mkdir -p "$HOME/.local/share/gnome-shell/extensions"

# 3. Compile GSettings schemas
if command -v glib-compile-schemas &>/dev/null && [ -d "$SCRIPT_DIR/schemas" ]; then
    echo -e " ${BLUE}[i]${RESET} Compilando esquemas GSettings en schemas/..."
    glib-compile-schemas "$SCRIPT_DIR/schemas"
    echo -e " ${GREEN}[✓]${RESET} Esquemas GSettings compilados correctamente."
fi

# 4. Create Symlink (development-friendly) or copy
if [ -L "$EXT_DEST" ] || [ -d "$EXT_DEST" ]; then
    echo -e " ${BLUE}[i]${RESET} Eliminando instalación previa en $EXT_DEST..."
    rm -rf "$EXT_DEST"
fi

echo -e " ${BLUE}[i]${RESET} Enlazando extensión a ${BOLD}$EXT_DEST${RESET}..."
ln -s "$SCRIPT_DIR" "$EXT_DEST"
echo -e " ${GREEN}[✓]${RESET} Enlace simbólico creado correctamente."

# 5. Attempt to enable extension via gnome-extensions CLI
if command -v gnome-extensions &>/dev/null; then
    echo -e " ${BLUE}[i]${RESET} Habilitando extensión con gnome-extensions..."
    gnome-extensions enable "$UUID" 2>/dev/null || true
    echo -e " ${GREEN}[✓]${RESET} Comando enable ejecutado para: ${BOLD}$UUID${RESET}"
fi

echo -e "\n${BOLD}${GREEN}=====================================================${RESET}"
echo -e "${BOLD}${GREEN}✔ ¡Extensión instalada exitosamente!${RESET}"
echo -e "${BOLD}${GREEN}=====================================================${RESET}\n"

echo -e "${BOLD}¿Cómo activarla en tu escritorio?${RESET}"
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo -e "  • En ${BOLD}Wayland${RESET}: GNOME Shell no recarga extensiones nuevas en caliente."
    echo -e "    Debes ${BOLD}cerrar sesión y volver a entrar${RESET} para que GNOME cargue la nueva extensión."
else
    echo -e "  • En ${BOLD}X11${RESET}: Presiona ${BOLD}Alt + F2${RESET}, escribe ${BOLD}r${RESET} y presiona Enter."
    echo -e "  • O bien cierra sesión y vuelve a iniciarla."
fi
echo -e "  • Una vez reiniciado el Shell, abre el ${BOLD}Quick Settings${RESET} (esquina superior derecha)."
echo -e "    Verás el botón ${BOLD}«Theme Studio»${RESET} con tu tema activo y los 5 accesos rápidos."
echo -e "\n${BOLD}¿Cómo personalizar los 5 presets desde el Gestor de Extensiones?${RESET}"
echo -e "  • Abre la app ${BOLD}Extensiones${RESET} (o Gestor de Extensiones) y haz clic en el botón de engranaje ${BOLD}⚙${RESET} junto a Theme Studio."
echo -e "  • O ejecuta en terminal: ${BOLD}gnome-extensions prefs $UUID${RESET}"
echo -e "  • O dentro del menú de Quick Settings, haz clic en ${BOLD}«Configuración de la extensión...»${RESET}\n"
