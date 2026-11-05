#!/usr/bin/env bash
# ===================================================================
# GNOME Theme Studio - Startup Launcher
# ===================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[1;32m=== Iniciando GNOME Theme Studio ===\033[0m"

# 0. Check system dependencies
if ! command -v sassc &>/dev/null; then
    echo -e "\033[1;33m[!] Advertencia: 'sassc' no está instalado en el sistema.\033[0m"
    echo -e "    Para compilar temas necesitarás instalarlo (ej: sudo dnf install sassc / sudo apt install sassc)\n"
fi

# 1. Check venv
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creando entorno virtual en $SCRIPT_DIR/venv..."
    python3 -m venv "$SCRIPT_DIR/venv"
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

PORT="${PORT:-5000}"
URL="http://127.0.0.1:$PORT"

echo -e "Servidor local listo en: \033[1;34m$URL\033[0m"
echo -e "Presiona \033[1mCtrl + C\033[0m para detener el servidor.\n"

# Launch browser if command exists and not in headless/daemon
if command -v xdg-open &>/dev/null && [ -n "$DISPLAY$WAYLAND_DISPLAY" ]; then
    (sleep 1.2 && xdg-open "$URL" 2>/dev/null || true) &
fi

exec "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/app.py"
