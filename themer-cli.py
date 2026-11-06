#!/usr/bin/env python3
"""
===================================================================
🌲 GNOME THEME STUDIO — CLI STUDIO INTERACTIVO (PANTALLA ÚNICA)
===================================================================
Interfaz interactiva de panel dual (estilo htop / kconfig) para
seleccionar presets, ajustar valores en vivo con la barra espaciadora
y aplicar con recarga en caliente en Wayland / X11.
===================================================================
"""

import os
import sys
import copy
import time
import shutil
import argparse
import termios
import tty
import re

# Local theme engine modules
import presets
import compiler
import installer
import exporter
import wallpaper_generator

# ANSI Color & Formatting Constants
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
INVERSE = "\033[7m"

GREEN = "\033[38;2;167;192;128m"      # Everforest Green
BLUE = "\033[38;2;122;162;247m"       # Tokyo Night Blue
CYAN = "\033[38;2;127;187;179m"       # Soft Cyan
YELLOW = "\033[38;2;219;188;127m"     # Warm Yellow
RED = "\033[38;2;230;126;128m"        # Soft Red
PURPLE = "\033[38;2;203;166;247m"     # Catppuccin Mauve
GRAY = "\033[38;2;133;146;137m"       # Muted Gray
WHITE = "\033[38;2;235;235;235m"      # Bright White

BG_SELECT = "\033[48;2;52;63;68m"     # Active selection row
BG_ACTIVE = "\033[48;2;45;53;59m"     # Panel active border

ANSI_RE = re.compile(r'\033\[[0-9;]*[a-zA-Z]')

# Standard GNOME Accent Palette
GNOME_ACCENTS = [
    ("original", "Original", None),
    ("blue",     "Azul",      "#3584e4"),
    ("teal",     "Teal",      "#21a499"),
    ("green",    "Verde",     "#33d17a"),
    ("yellow",   "Amarillo",  "#f6d32d"),
    ("orange",   "Naranja",   "#ff7800"),
    ("red",      "Rojo",      "#e01b24"),
    ("pink",     "Rosa",      "#ff6188"),
    ("purple",   "Purpura",   "#9141ac"),
    ("slate",    "Pizarra",   "#859289")
]

GNOME_ACCENT_HEX = {name: h for name, _, h in GNOME_ACCENTS if h}

CONTROLS_STYLES = [
    ("traffic-hover", "Semaforo macOS (hover)"),
    ("traffic-light", "Semaforo macOS (fijo)"),
    ("monochrome",    "Monocromo (GNOME)"),
    ("minimal",       "Minimalista")
]

BUTTON_LAYOUTS = [
    ("right", "Derecha (GNOME)"),
    ("left",  "Izquierda (macOS)")
]

RADII_PRESETS = [
    (4, 2,   "Cuadrado (4px)"),
    (12, 8,  "Estandar (12px)"),
    (16, 10, "Moderno (16px)"),
    (22, 14, "Muy Redondo (22px)")
]

WALLPAPER_STYLES = [
    ("abstract_waves", "Ondas fluidas (Waves)"),
    ("aurora",         "Aurora boreal"),
    ("geometric",      "Geometrico"),
    ("none",           "Ninguno")
]


# ===================================================================
# ANSI Formatting & String Width Helpers
# ===================================================================

def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes to measure visible text width."""
    return ANSI_RE.sub('', text)


def visible_len(text: str) -> int:
    """Returns visible character length of a string containing ANSI codes."""
    return len(strip_ansi(text))


def pad_visible(text: str, width: int, align: str = 'left') -> str:
    """Pads text to exact visible column width, ignoring ANSI sequences."""
    vlen = visible_len(text)
    pad = max(0, width - vlen)
    if align == 'right':
        return (' ' * pad) + text
    elif align == 'center':
        left_pad = pad // 2
        right_pad = pad - left_pad
        return (' ' * left_pad) + text + (' ' * right_pad)
    return text + (' ' * pad)


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Converts hex string (#RRGGBB or #RGB) to RGB tuple."""
    hex_clean = hex_str.lstrip("#").strip()
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    if len(hex_clean) != 6:
        return (128, 128, 128)
    try:
        return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (128, 128, 128)


def rgb_chip(hex_str: str, width: int = 2) -> str:
    """Returns an ANSI TrueColor background block representing the hex color."""
    r, g, b = hex_to_rgb(hex_str)
    return f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m"


def clear_screen():
    """Clears the terminal screen and moves cursor to home."""
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def get_key() -> str:
    """Reads a single keypress or escape sequence from stdin."""
    if not sys.stdin.isatty():
        ch = sys.stdin.read(1)
        if not ch:
            return "EOF"
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A": return "UP"
                elif ch3 == "B": return "DOWN"
                elif ch3 == "C": return "RIGHT"
                elif ch3 == "D": return "LEFT"
            return "ESC"
        elif ch in ("\r", "\n"):
            return "ENTER"
        elif ch == " ":
            return "SPACE"
        elif ch == "\t":
            return "TAB"
        return ch

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A": return "UP"
                elif ch3 == "B": return "DOWN"
                elif ch3 == "C": return "RIGHT"
                elif ch3 == "D": return "LEFT"
                elif ch3 == "H": return "HOME"
                elif ch3 == "F": return "END"
                elif ch3 in ("5", "6"):
                    sys.stdin.read(1)  # Consume trailing ~
                    return "PGUP" if ch3 == "5" else "PGDN"
            return "ESC"
        elif ch in ("\r", "\n"):
            return "ENTER"
        elif ch == " ":
            return "SPACE"
        elif ch == "\t":
            return "TAB"
        elif ch == "\x03":
            raise KeyboardInterrupt
        elif ch == "\x04":
            return "EOF"
        elif ch in ("\x7f", "\x08"):
            return "BACKSPACE"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def prompt_cooked_input(prompt_text: str, default_val: str = "") -> str:
    """Prompts for text input in normal cooked mode."""
    if default_val:
        display_prompt = f"{BOLD}{CYAN}{prompt_text}{RESET} [{WHITE}{default_val}{RESET}]: "
    else:
        display_prompt = f"{BOLD}{CYAN}{prompt_text}{RESET}: "
    try:
        val = input(display_prompt).strip()
        return val if val else default_val
    except (KeyboardInterrupt, EOFError):
        print()
        return default_val


# ===================================================================
# Actions Execution (Apply, Reset, Export)
# ===================================================================

def execute_apply_theme(config: dict, targets: dict, interactive: bool = True):
    """Compiles theme, applies to system, and triggers live hot-reload pulse."""
    theme_name = config.get("theme_name", "Studio-Theme")
    clear_screen()

    print(f"\n{BOLD}{YELLOW}⚡ Compilando y aplicando tema: '{theme_name}'...{RESET}\n")

    # 1. Compile Theme
    t0 = time.perf_counter()
    print(f" {CYAN}[1/4]{RESET} Compilando hojas de estilo SCSS con sassc (GTK4, GTK3, Shell, Firefox)...")
    compile_res = compiler.compile_theme(config)
    if not compile_res.get("success"):
        print(f"\n{RED}{BOLD}[X] ERROR EN LA COMPILACION:{RESET}")
        print(f"{RED}{compile_res.get('error')}{RESET}\n")
        if interactive:
            prompt_cooked_input("Presiona Enter para volver")
        return

    duration = compile_res.get("duration_ms", 0)
    compiled_dir = compile_res.get("output_dir")
    print(f" {GREEN}[✓]{RESET} Compilado exitosamente en {duration:.1f} ms.")

    # 2. Wallpaper Step
    apply_wp = targets.get("apply_wallpaper", True)
    if apply_wp:
        print(f" {CYAN}[2/4]{RESET} Generando fondo de pantalla vectorial 4K ({config.get('wallpaper_style')})...")
    else:
        print(f" {DIM}[2/4] Omitiendo fondo de pantalla.{RESET}")

    # 3. Installation & Libadwaita
    print(f" {CYAN}[3/4]{RESET} Desplegando en ~/.themes y ~/.config/gtk-4.0...")

    # 4. Apply & Live Hot-Reload
    print(f" {CYAN}[4/4]{RESET} Sincronizando Firefox y ejecutando pulso Wayland...")
    apply_res = installer.install_and_apply_theme(
        theme_name,
        compiled_dir,
        config=config,
        apply_gtk4=targets.get("apply_gtk4", True),
        apply_wallpaper=apply_wp,
        apply_firefox=targets.get("apply_firefox", True)
    )

    total_time = (time.perf_counter() - t0) * 1000

    print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f" {BOLD}{GREEN}[✓] TEMA '{theme_name}' APLICADO CON EXITO AL ESCRITORIO GNOME ({total_time:.0f} ms){RESET}")
    print(f"{BOLD}{GREEN}══════════════════════════════════════════════════════════════════════════════{RESET}\n")

    for log in apply_res.get("logs", []):
        print(f"  {DIM}•{RESET} {log}")

    print()
    if interactive:
        prompt_cooked_input("Presiona Enter para volver al estudio")


def execute_export_theme(config: dict, interactive: bool = True):
    """Compiles theme and packages into a portable .zip file."""
    theme_name = config.get("theme_name", "Studio-Theme")
    clear_screen()

    print(f"\n{BOLD}{YELLOW}📦 Empaquetando tema '{theme_name}' en archivo .ZIP autonomo...{RESET}\n")

    compile_res = compiler.compile_theme(config)
    if not compile_res.get("success"):
        print(f"{RED}[X] Fallo la compilacion: {compile_res.get('error')}{RESET}")
        if interactive:
            prompt_cooked_input("Presiona Enter para continuar")
        return

    compiled_dir = compile_res["output_dir"]
    zip_path = exporter.create_theme_zip(theme_name, compiled_dir)

    print(f"{BOLD}{GREEN}[✓] Paquete ZIP generado exitosamente!{RESET}")
    print(f"  Ruta del archivo: {WHITE}{zip_path}{RESET}")
    print(f"  {DIM}Incluye index.theme, GTK 3/4, Shell, Firefox y script install.sh.{RESET}\n")
    if interactive:
        prompt_cooked_input("Presiona Enter para volver")


def execute_reset_gnome(interactive: bool = True):
    """Restores GNOME desktop to factory out-of-the-box defaults."""
    clear_screen()
    print(f"\n{BOLD}{RED}⚠️  RESTAURAR VALORES DE FABRICA DE GNOME{RESET}\n")
    print("Esta accion restablecera:")
    print("  • Tema GTK a 'Adwaita'")
    print("  • Tema de GNOME Shell a default")
    print("  • Fondo de pantalla del sistema")
    print("  • Eliminara los overrides de Libadwaita en ~/.config/gtk-4.0/")
    print("  • Eliminara estilos personalizados en perfiles de Firefox\n")

    if interactive:
        confirm = prompt_cooked_input("¿Estas seguro de que deseas restablecer GNOME? (s/n)", "n")
        should_reset = confirm.lower() in ("s", "si", "y", "yes")
    else:
        should_reset = True

    if should_reset:
        res = installer.reset_gnome_defaults()
        print(f"\n{BOLD}{GREEN}[✓] {res.get('message')}{RESET}\n")
        for log in res.get("logs", []):
            print(f"  {DIM}•{RESET} {log}")
        print()
    else:
        print(f"\n{YELLOW}[i] Operacion cancelada.{RESET}")

    if interactive:
        prompt_cooked_input("Presiona Enter para volver")


# ===================================================================
# Dual-Panel Single-Screen Studio Interface (Option 1)
# ===================================================================

def run_single_screen_studio():
    """
    Main interactive loop for the single-screen dual-panel Theme Studio.
    Left panel: Preset selector.
    Right panel: Live setting toggles/cycles via Spacebar.
    """
    all_presets = presets.load_presets()
    if not all_presets:
        print(f"{RED}[!] Error: presets.json no encontrado o vacio.{RESET}")
        return

    preset_keys = list(all_presets.keys())

    # Initial State
    active_panel = "presets"  # "presets" or "settings"
    preset_idx = 0
    setting_row = 0
    scroll_top = 0

    # Working copy of the active preset configuration
    current_key = preset_keys[preset_idx]
    current_cfg = copy.deepcopy(all_presets[current_key])
    orig_accent = current_cfg.get("accent_color", "#a7c080")
    accent_idx = 0  # 0 = original

    targets = {
        "apply_gtk4": True,
        "apply_wallpaper": True,
        "apply_firefox": True
    }

    while True:
        term_cols, term_rows = shutil.get_terminal_size((80, 24))
        term_cols = max(80, term_cols)
        term_rows = max(24, term_rows)

        # Panel width calculations
        left_w = 30
        right_w = term_cols - left_w - 3  # Exact terminal fit
        content_h = 14                     # 14 rows fit in standard 24-line terminal

        # Adjust scroll window for presets
        if preset_idx < scroll_top:
            scroll_top = preset_idx
        elif preset_idx >= scroll_top + content_h:
            scroll_top = preset_idx - content_h + 1

        # Read current GNOME interface status
        sys_status = installer.get_current_theme_status()
        cur_gtk = sys_status.get("gtk_theme", "Adwaita")
        cur_scheme = sys_status.get("color_scheme", "default")
        cur_accent = sys_status.get("accent_color", "blue")

        lines_out = []
        lines_out.append("\033[H")  # Move cursor to top-left (flicker-free redraw)

        # Top Banner
        lines_out.append(f"{BOLD}{GREEN}╔" + "═" * (term_cols - 2) + f"╗{RESET}")
        header_text = "  🌲 GNOME THEME STUDIO — CLI STUDIO INTERACTIVO  (v2.0)"
        lines_out.append(f"{BOLD}{GREEN}║{WHITE}" + pad_visible(header_text, term_cols - 2) + f"{GREEN}║{RESET}")
        status_text = f"  Escritorio: {WHITE}{cur_gtk}{RESET} | Esquema: {CYAN}{cur_scheme}{RESET} | Acento GNOME: {PURPLE}{cur_accent}{RESET}"
        lines_out.append(f"{BOLD}{GREEN}║" + pad_visible(status_text, term_cols - 2) + f"{GREEN}║{RESET}")
        lines_out.append(f"{BOLD}{GREEN}╚" + "═" * (term_cols - 2) + f"╝{RESET}")

        # Top borders of panels
        p_focus_color = GREEN if active_panel == "presets" else GRAY
        s_focus_color = GREEN if active_panel == "settings" else GRAY

        left_top = f"{p_focus_color}┌── PRESETS ({len(preset_keys)}) " + "─" * max(0, left_w - 18) + f"┐{RESET}"
        t_name = current_cfg.get("theme_name", "Theme")
        right_title = f" AJUSTES: {t_name} "
        r_dash_len = max(2, right_w - visible_len(right_title) - 4)
        right_top = f"{s_focus_color}┌──{WHITE}{BOLD}{right_title}{RESET}{s_focus_color}" + "─" * r_dash_len + f"┐{RESET}"
        lines_out.append(f"{left_top} {right_top}")

        # Panel content rows (14 lines)
        for row in range(content_h):
            # 1. Left Panel Cell (Preset Item)
            p_i = scroll_top + row
            if p_i < len(preset_keys):
                p_key = preset_keys[p_i]
                p_cfg = all_presets[p_key]
                is_dark = (p_cfg.get("color_scheme") == "dark")
                tag_badge = f"{PURPLE}[D]{RESET}" if is_dark else f"{YELLOW}[L]{RESET}"
                is_cur = (p_i == preset_idx)
                p_cur_tag = f"{BOLD}{GREEN}➜{RESET}" if is_cur else " "

                # Short display name to fit in left panel
                disp_name = p_key
                max_txt_len = left_w - 9
                if len(disp_name) > max_txt_len:
                    disp_name = disp_name[:max_txt_len - 1] + "…"

                if is_cur and active_panel == "presets":
                    cell_l = f" {p_cur_tag} {tag_badge} {BOLD}{WHITE}{disp_name}{RESET}"
                    cell_l = f"{BG_SELECT}{pad_visible(cell_l, left_w - 2)}{RESET}"
                elif is_cur:
                    cell_l = f" {p_cur_tag} {tag_badge} {CYAN}{disp_name}{RESET}"
                    cell_l = pad_visible(cell_l, left_w - 2)
                else:
                    cell_l = f"   {tag_badge} {DIM}{disp_name}{RESET}"
                    cell_l = pad_visible(cell_l, left_w - 2)
            else:
                cell_l = " " * (left_w - 2)

            left_border = f"{p_focus_color}│{RESET}"
            left_block = f"{left_border}{cell_l}{left_border}"

            # 2. Right Panel Cell (Settings & Live Swatches)
            cell_r = ""
            is_s_row = (active_panel == "settings" and setting_row == row)
            cursor_r = f"{BOLD}{GREEN}➜{RESET} " if is_s_row else "  "

            if row == 0:
                # Esquema
                sch = current_cfg.get("color_scheme", "dark")
                sch_txt = f"{PURPLE}Oscuro (Dark){RESET}" if sch == "dark" else f"{YELLOW}Claro (Light){RESET}"
                cell_r = f"{cursor_r}{BOLD}Esquema:{RESET}    [ {sch_txt} ]"
            elif row == 1:
                # Acento
                acc_hex = current_cfg.get("accent_color", "#a7c080")
                acc_name = GNOME_ACCENTS[accent_idx][1] if accent_idx < len(GNOME_ACCENTS) else "Custom"
                cell_r = f"{cursor_r}{BOLD}Acento:{RESET}     [ {rgb_chip(acc_hex, 2)} {WHITE}{acc_hex}{RESET} {acc_name} ]"
            elif row == 2:
                # Controles de Ventana
                ctrl = current_cfg.get("window_controls_style", "traffic-hover")
                ctrl_lbl = dict(CONTROLS_STYLES).get(ctrl, ctrl)
                cell_r = f"{cursor_r}{BOLD}Botones:{RESET}    [ {WHITE}{ctrl_lbl}{RESET} ]"
            elif row == 3:
                # Posición de Botones
                lay = current_cfg.get("button_layout", "right")
                lay_lbl = dict(BUTTON_LAYOUTS).get(lay, lay)
                cell_r = f"{cursor_r}{BOLD}Posicion:{RESET}   [ {WHITE}{lay_lbl}{RESET} ]"
            elif row == 4:
                # Curvatura y Radios
                rad = current_cfg.get("window_radius", 12)
                rad_lbl = f"{rad}px"
                for w_r, _, lbl in RADII_PRESETS:
                    if w_r == rad:
                        rad_lbl = lbl
                        break
                cell_r = f"{cursor_r}{BOLD}Curvatura:{RESET}  [ {WHITE}{rad_lbl}{RESET} ]"
            elif row == 5:
                # Fondo 4K
                wp = current_cfg.get("wallpaper_style", "abstract_waves")
                wp_lbl = dict(WALLPAPER_STYLES).get(wp, wp)
                cell_r = f"{cursor_r}{BOLD}Fondo 4K:{RESET}   [ {WHITE}{wp_lbl}{RESET} ]"
            elif row == 6:
                # Libadwaita toggle
                gtk4_on = targets.get("apply_gtk4", True)
                gtk4_txt = f"{GREEN}SI (~/.config/gtk-4.0){RESET}" if gtk4_on else f"{RED}NO{RESET}"
                cell_r = f"{cursor_r}{BOLD}Libadwaita:{RESET} [ {gtk4_txt} ]"
            elif row == 7:
                # Firefox toggle
                ff_on = targets.get("apply_firefox", True)
                ff_txt = f"{GREEN}SI (userChrome){RESET}" if ff_on else f"{RED}NO{RESET}"
                cell_r = f"{cursor_r}{BOLD}Firefox:{RESET}    [ {ff_txt} ]"
            elif row == 8:
                # Separador sutil
                cell_r = f"  {DIM}" + "─" * max(4, right_w - 6) + f"{RESET}"
            elif row == 9:
                # Muestras de Color en Vivo
                win = current_cfg.get("window_bg", "#2d353b")
                side = current_cfg.get("sidebar_bg", "#272e33")
                cell_r = f"  {BOLD}Paleta:{RESET} Win {rgb_chip(win, 2)} {WHITE}{win}{RESET}  Side {rgb_chip(side, 2)} {WHITE}{side}{RESET}"
            elif row == 10:
                hdr = current_cfg.get("headerbar_bg", "#232a2e")
                txt = current_cfg.get("text_primary", "#d3c6aa")
                cell_r = f"          Hdr {rgb_chip(hdr, 2)} {WHITE}{hdr}{RESET}  Txt  {rgb_chip(txt, 2)} {WHITE}{txt}{RESET}"
            elif row == 11:
                # Separador sutil
                cell_r = f"  {DIM}" + "─" * max(4, right_w - 6) + f"{RESET}"
            elif row == 12:
                # Botón de acción destacado
                action_text = "⚡ [ A / Enter ] APLICAR ESTE TEMA AL ESCRITORIO"
                if row == setting_row and active_panel == "settings":
                    cell_r = f"  {BG_SELECT}{BOLD}{GREEN} {action_text} {RESET}"
                else:
                    cell_r = f"  {BOLD}{GREEN} {action_text} {RESET}"
            else:
                cell_r = ""

            if is_s_row and row != 12:
                cell_r = f"{BG_SELECT}{pad_visible(cell_r, right_w - 2)}{RESET}"
            else:
                cell_r = pad_visible(cell_r, right_w - 2)

            right_border = f"{s_focus_color}│{RESET}"
            right_block = f"{right_border}{cell_r}{right_border}"

            lines_out.append(f"{left_block} {right_block}")

        # Bottom borders of panels
        p_bot_tag = f"─ [↑/↓] {preset_idx + 1}/{len(preset_keys)} "
        left_bot = f"{p_focus_color}└" + p_bot_tag + "─" * max(0, left_w - visible_len(p_bot_tag) - 2) + f"┘{RESET}"

        s_bot_tag = "─ [Tab/→] Ajustes ─ [Espacio] Alternar "
        right_bot = f"{s_focus_color}└" + s_bot_tag + "─" * max(0, right_w - visible_len(s_bot_tag) - 2) + f"┘{RESET}"
        lines_out.append(f"{left_bot} {right_bot}")

        # Footer Action Bar
        lines_out.append(
            f" {BOLD}{GREEN}[A / Enter]{RESET} ⚡ Aplicar  |  "
            f"{BOLD}{CYAN}[Tab / ← / →]{RESET} Panel  |  "
            f"{BOLD}{YELLOW}[Espacio]{RESET} Alternar  |  "
            f"{BOLD}{PURPLE}[S]{RESET} Guardar  |  "
            f"{BOLD}{PURPLE}[E]{RESET} Exportar  |  "
            f"{BOLD}{PURPLE}[R]{RESET} Reset  |  "
            f"{BOLD}{RED}[Q]{RESET} Salir"
        )

        # Output the whole frame in one write (flicker-free)
        sys.stdout.write("\n".join(lines_out) + "\n")
        sys.stdout.flush()

        # Input reading
        key = get_key()

        # Global Hotkeys
        if key in ("q", "Q", "ESC"):
            clear_screen()
            print(f"{GREEN}¡Gracias por usar GNOME Theme Studio! Hasta luego.{RESET}\n")
            break

        elif key in ("a", "A"):
            execute_apply_theme(current_cfg, targets, interactive=True)
            continue

        elif key in ("e", "E"):
            execute_export_theme(current_cfg, interactive=True)
            continue

        elif key in ("r", "R"):
            execute_reset_gnome(interactive=True)
            continue

        elif key in ("s", "S"):
            clear_screen()
            def_name = current_cfg.get("theme_name", "Mi-Tema-Personalizado")
            s_name = prompt_cooked_input("Guardar en presets.json con nombre", def_name)
            if s_name:
                presets.save_preset(s_name, current_cfg)
                all_presets = presets.load_presets()
                preset_keys = list(all_presets.keys())
                print(f"{GREEN}[✓] ¡Preset '{s_name}' guardado exitosamente!{RESET}")
                time.sleep(1.0)
            continue

        # Panel Navigation & Switching
        if key == "TAB":
            active_panel = "settings" if active_panel == "presets" else "presets"

        elif key == "RIGHT":
            if active_panel == "presets":
                active_panel = "settings"

        elif key == "LEFT":
            if active_panel == "settings":
                active_panel = "presets"

        elif key in ("UP", "k"):
            if active_panel == "presets":
                preset_idx = (preset_idx - 1) % len(preset_keys)
                current_key = preset_keys[preset_idx]
                current_cfg = copy.deepcopy(all_presets[current_key])
                orig_accent = current_cfg.get("accent_color", "#a7c080")
                accent_idx = 0
            else:
                # Move within settings rows (0 to 8, skipping separator rows)
                valid_rows = [0, 1, 2, 3, 4, 5, 6, 7, 12]
                curr_idx = valid_rows.index(setting_row) if setting_row in valid_rows else 0
                setting_row = valid_rows[(curr_idx - 1) % len(valid_rows)]

        elif key in ("DOWN", "j"):
            if active_panel == "presets":
                preset_idx = (preset_idx + 1) % len(preset_keys)
                current_key = preset_keys[preset_idx]
                current_cfg = copy.deepcopy(all_presets[current_key])
                orig_accent = current_cfg.get("accent_color", "#a7c080")
                accent_idx = 0
            else:
                valid_rows = [0, 1, 2, 3, 4, 5, 6, 7, 12]
                curr_idx = valid_rows.index(setting_row) if setting_row in valid_rows else 0
                setting_row = valid_rows[(curr_idx + 1) % len(valid_rows)]

        # Action Keys (Space or Enter)
        elif key in ("SPACE", "ENTER"):
            if active_panel == "presets":
                if key == "ENTER":
                    active_panel = "settings"
                elif key == "SPACE":
                    active_panel = "settings"
            else:
                # Active panel is settings -> toggle or cycle value!
                if setting_row == 0:
                    # Esquema: Dark <-> Light
                    old_sch = current_cfg.get("color_scheme", "dark")
                    new_sch = "light" if old_sch == "dark" else "dark"
                    current_cfg["color_scheme"] = new_sch

                    # If paired counterpart preset exists in presets.json, adopt its harmonious palette
                    paired_map = {
                        "Everforest Dark": "Everforest Light",
                        "Everforest Light": "Everforest Dark",
                        "Tokyo Night": "Tokyo Night Day",
                        "Tokyo Night Day": "Tokyo Night",
                        "Catppuccin Mocha": "Catppuccin Latte",
                        "Catppuccin Latte": "Catppuccin Mocha",
                        "Nord Dark": "Nord Snow Storm",
                        "Nord Snow Storm": "Nord Dark",
                        "Solarized Dark": "Solarized Light",
                        "Solarized Light": "Solarized Dark",
                        "Gruvbox Dark": "Gruvbox Light",
                        "Gruvbox Light": "Gruvbox Dark",
                        "Rosé Pine": "Rosé Pine Dawn",
                        "Rosé Pine Dawn": "Rosé Pine",
                        "One Dark Pro": "One Light",
                        "One Light": "One Dark Pro",
                        "Adwaita Dark (GNOME Default)": "Adwaita Light (GNOME Default)",
                        "Adwaita Light (GNOME Default)": "Adwaita Dark (GNOME Default)"
                    }
                    if current_key in paired_map and paired_map[current_key] in all_presets:
                        target_key = paired_map[current_key]
                        current_cfg = copy.deepcopy(all_presets[target_key])
                        current_cfg["color_scheme"] = new_sch
                        orig_accent = current_cfg.get("accent_color", "#a7c080")
                        accent_idx = 0

                elif setting_row == 1:
                    # Acento: cycle through GNOME accents
                    accent_idx = (accent_idx + 1) % len(GNOME_ACCENTS)
                    _, _, h = GNOME_ACCENTS[accent_idx]
                    if h:
                        current_cfg["accent_color"] = h
                    else:
                        current_cfg["accent_color"] = orig_accent

                elif setting_row == 2:
                    # Controles de ventana
                    curr_c = current_cfg.get("window_controls_style", "traffic-hover")
                    keys_c = [k for k, _ in CONTROLS_STYLES]
                    curr_i = keys_c.index(curr_c) if curr_c in keys_c else 0
                    current_cfg["window_controls_style"] = keys_c[(curr_i + 1) % len(keys_c)]

                elif setting_row == 3:
                    # Posición de botones (derecha / izquierda)
                    curr_l = current_cfg.get("button_layout", "right")
                    current_cfg["button_layout"] = "left" if curr_l == "right" else "right"

                elif setting_row == 4:
                    # Curvatura y radios
                    curr_r = current_cfg.get("window_radius", 12)
                    radii_vals = [r for r, _, _ in RADII_PRESETS]
                    r_i = radii_vals.index(curr_r) if curr_r in radii_vals else 1
                    next_i = (r_i + 1) % len(RADII_PRESETS)
                    w_r, b_r, _ = RADII_PRESETS[next_i]
                    current_cfg["window_radius"] = w_r
                    current_cfg["button_radius"] = b_r

                elif setting_row == 5:
                    # Fondo 4K
                    curr_w = current_cfg.get("wallpaper_style", "abstract_waves")
                    keys_w = [k for k, _ in WALLPAPER_STYLES]
                    w_i = keys_w.index(curr_w) if curr_w in keys_w else 0
                    current_cfg["wallpaper_style"] = keys_w[(w_i + 1) % len(keys_w)]

                elif setting_row == 6:
                    # Toggle GTK4
                    targets["apply_gtk4"] = not targets.get("apply_gtk4", True)

                elif setting_row == 7:
                    # Toggle Firefox
                    targets["apply_firefox"] = not targets.get("apply_firefox", True)

                elif setting_row == 12:
                    # Action row: Apply theme!
                    execute_apply_theme(current_cfg, targets, interactive=True)


# ===================================================================
# Non-Interactive / Scriptable CLI Entrypoint
# ===================================================================

def parse_cli_args():
    """Parses command-line arguments for automated or script usage."""
    parser = argparse.ArgumentParser(
        description="GNOME Theme Studio — CLI Studio & Themer",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-p", "--preset", type=str, help="Nombre del preset a cargar (ej: 'Tokyo Night', 'Everforest Dark').")
    parser.add_argument("-a", "--apply", action="store_true", help="Compila e instala el tema directamente en el sistema.")
    parser.add_argument("-l", "--list", action="store_true", help="Lista todos los presets disponibles y finaliza.")
    parser.add_argument("-s", "--status", action="store_true", help="Muestra el estado actual del entorno GNOME y finaliza.")
    parser.add_argument("-r", "--reset", action="store_true", help="Restablece GNOME a la configuracion estandar Adwaita.")
    parser.add_argument("-e", "--export", action="store_true", help="Compila y empaqueta el tema en un archivo .ZIP descargable.")

    # Overrides
    parser.add_argument("--scheme", choices=["dark", "light"], help="Sobrescribe el esquema de color (dark / light).")
    parser.add_argument("--accent", type=str, help="Sobrescribe el color de acento (#hex o nombre oficial GNOME).")
    parser.add_argument("--window-bg", type=str, help="Sobrescribe el fondo de ventana (#hex).")
    parser.add_argument("--wallpaper-style", choices=["abstract_waves", "aurora", "geometric", "none"], help="Estilo de fondo vectorial.")
    parser.add_argument("--controls-style", choices=["traffic-hover", "traffic-light", "monochrome", "minimal"], help="Estilo de botones.")
    parser.add_argument("--layout", choices=["right", "left"], help="Posicion de botones (right: GNOME, left: macOS).")

    # Target toggles
    parser.add_argument("--no-gtk4", action="store_true", help="No aplicar estilos a GTK4 / Libadwaita.")
    parser.add_argument("--no-wallpaper", action="store_true", help="No generar ni cambiar el fondo de pantalla.")
    parser.add_argument("--no-firefox", action="store_true", help="No tematizar perfiles de Mozilla Firefox.")
    parser.add_argument("--name", type=str, help="Asignar un nombre personalizado al tema compilado.")

    return parser.parse_args()


def list_presets_cli():
    """Prints a clean CLI table of all presets with RGB color swatches."""
    data = presets.load_presets()
    print(f"\n{BOLD}{GREEN}=== BIBLIOTECA DE PRESETS DE GNOME THEME STUDIO ==={RESET}\n")
    print(f"  {'#':<3} {'Esquema':<8} {'Nombre del Preset':<28} {'Acento':<16} {'Fondo Ventana':<16} {'Controles'}")
    print(f"  {'-'*3} {'-'*8} {'-'*28} {'-'*16} {'-'*16} {'-'*12}")

    for idx, (name, cfg) in enumerate(data.items(), 1):
        scheme_icon = "[D] Dark " if cfg.get("color_scheme") == "dark" else "[L] Light"
        accent = cfg.get("accent_color", "#a7c080")
        win_bg = cfg.get("window_bg", "#2d353b")
        ctrl = cfg.get("window_controls_style", "traffic-hover")
        accent_swatch = f"{rgb_chip(accent, 2)} {accent}"
        win_swatch = f"{rgb_chip(win_bg, 2)} {win_bg}"
        print(f"  {idx:2d}. {scheme_icon:<8} {BOLD}{name:<28}{RESET} {accent_swatch:<24} {win_swatch:<24} {DIM}{ctrl}{RESET}")
    print(f"\nTotal: {len(data)} presets. Para aplicar uno ejecuta: {CYAN}./themer-cli.py --preset \"<Nombre>\" --apply{RESET}\n")


def main():
    """Main program entrypoint."""
    args = parse_cli_args()

    # 1. Non-interactive commands
    if args.list:
        list_presets_cli()
        return

    if args.status:
        status = installer.get_current_theme_status()
        print(f"\n{BOLD}{CYAN}=== ESTADO ACTUAL DEL ENTORNO GNOME ==={RESET}\n")
        for k, v in status.items():
            print(f"  {BOLD}{k:<24}:{RESET} {WHITE}{v}{RESET}")
        print()
        return

    if args.reset:
        execute_reset_gnome(interactive=False)
        return

    if args.preset:
        all_presets = presets.load_presets()
        matched_key = None
        for k in all_presets.keys():
            if k.lower() == args.preset.lower():
                matched_key = k
                break

        if not matched_key:
            for k in all_presets.keys():
                if args.preset.lower() in k.lower():
                    matched_key = k
                    break

        if not matched_key:
            print(f"{RED}[✗] Error: No se encontro ningun preset que coincida con '{args.preset}'.{RESET}")
            print(f"    Ejecuta {CYAN}./themer-cli.py --list{RESET} para ver los nombres disponibles.")
            sys.exit(1)

        config = copy.deepcopy(all_presets[matched_key])

        # Apply CLI overrides if present
        if args.name:
            config["theme_name"] = compiler.sanitize_theme_name(args.name)
        if args.scheme:
            config["color_scheme"] = args.scheme
        if args.accent:
            if args.accent.lower() in GNOME_ACCENT_HEX:
                config["accent_color"] = GNOME_ACCENT_HEX[args.accent.lower()]
            else:
                config["accent_color"] = args.accent
        if args.window_bg:
            config["window_bg"] = args.window_bg
        if args.wallpaper_style:
            config["wallpaper_style"] = args.wallpaper_style
        if args.controls_style:
            config["window_controls_style"] = args.controls_style
        if args.layout:
            config["button_layout"] = args.layout

        targets = {
            "apply_gtk4": not args.no_gtk4,
            "apply_wallpaper": not args.no_wallpaper,
            "apply_firefox": not args.no_firefox
        }

        if args.apply:
            execute_apply_theme(config, targets, interactive=False)
            return

        if args.export:
            execute_export_theme(config, interactive=False)
            return

    # 2. Launch Interactive Single-Screen Dual-Panel Studio
    try:
        run_single_screen_studio()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n{YELLOW}[i] GNOME Theme Studio CLI detenido.{RESET}\n")


if __name__ == "__main__":
    main()
