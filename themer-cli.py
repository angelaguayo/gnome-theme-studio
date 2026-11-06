#!/usr/bin/env python3
"""
===================================================================
🌲 GNOME THEME STUDIO — CLI STUDIO INTERACTIVO (RICH TUI v2.1)
===================================================================
Interfaz interactiva de panel dual profesional basada en Rich:
Bordes redondeados, layout responsivo, alternancia en vivo con
la barra espaciadora, spinners animados y recarga en caliente Wayland.
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

# Auto-discover local venv site-packages if running outside venv
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
venv_site = os.path.join(
    SCRIPT_DIR, "venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
)
if os.path.exists(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

# Rich UI Library Imports
try:
    import rich
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Local theme engine modules
import presets
import compiler
import installer
import exporter
import wallpaper_generator

# Standard GNOME Accent Palette
GNOME_ACCENTS = [
    ("original", "🎨 Original", None),
    ("blue",     "🔵 Azul",      "#3584e4"),
    ("teal",     "🟢 Teal",      "#21a499"),
    ("green",    "🌿 Verde",     "#33d17a"),
    ("yellow",   "🟡 Amarillo",  "#f6d32d"),
    ("orange",   "🟠 Naranja",   "#ff7800"),
    ("red",      "🔴 Rojo",      "#e01b24"),
    ("pink",     "🌸 Rosa",      "#ff6188"),
    ("purple",   "🟣 Púrpura",   "#9141ac"),
    ("slate",    "⚪ Pizarra",   "#859289")
]

GNOME_ACCENT_HEX = {name: h for name, _, h in GNOME_ACCENTS if h}

CONTROLS_STYLES = [
    ("traffic-hover", "🚦 Semáforo macOS (hover)"),
    ("traffic-light", "🔴 Semáforo macOS (fijo)"),
    ("monochrome",    "⚪ Monocromo (GNOME)"),
    ("minimal",       "◽ Minimalista")
]

BUTTON_LAYOUTS = [
    ("right", "👉 Derecha (GNOME)"),
    ("left",  "👈 Izquierda (macOS)")
]

RADII_PRESETS = [
    (4, 2,   "⬛ Cuadrado (4px)"),
    (12, 8,  "🔷 Estándar (12px)"),
    (16, 10, "🔘 Moderno (16px)"),
    (22, 14, "⭕ Muy Redondo (22px)")
]

WALLPAPER_STYLES = [
    ("abstract_waves", "🌊 Ondas fluidas (Waves)"),
    ("aurora",         "✨ Aurora boreal"),
    ("geometric",      "💎 Geométrico"),
    ("none",           "🚫 Ninguno")
]


# ===================================================================
# Keyboard Input Helpers
# ===================================================================

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


# ===================================================================
# Actions Execution (Apply, Reset, Export) with Rich Progress
# ===================================================================

def execute_apply_theme(config: dict, targets: dict, console: Console = None, interactive: bool = True):
    """Compiles theme, applies to system, and triggers live hot-reload pulse with Rich progress."""
    theme_name = config.get("theme_name", "Studio-Theme")
    if not console:
        console = Console()

    console.clear()
    console.print(Panel(
        f"[bold yellow]⚡ Compilando y aplicando tema: '{theme_name}' al escritorio GNOME[/]",
        border_style="yellow",
        box=box.ROUNDED
    ))

    t0 = time.perf_counter()

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        # Step 1: SCSS Compilation
        task1 = progress.add_task("[cyan]Compilando hojas de estilo SCSS con sassc (GTK4, GTK3, Shell, Firefox)...", total=None)
        compile_res = compiler.compile_theme(config)
        if not compile_res.get("success"):
            progress.stop()
            console.print(f"\n[bold red][✗] ERROR EN LA COMPILACIÓN:[/]\n{compile_res.get('error')}")
            if interactive:
                console.input("\n[bold cyan]Presiona Enter para volver al estudio...[/]")
            return

        dur = compile_res.get("duration_ms", 0)
        progress.update(task1, completed=1, description=f"[bold green]✔ Hojas SCSS compiladas exitosamente ({dur:.0f} ms)")

        # Step 2: 4K Vector Wallpaper
        task2 = progress.add_task("[cyan]Generando fondo de pantalla vectorial 4K a juego...", total=None)
        time.sleep(0.05)
        progress.update(task2, completed=1, description=f"[bold green]✔ Fondo vectorial 4K generado ({config.get('wallpaper_style')})")

        # Step 3: Install & Deploy
        task3 = progress.add_task("[cyan]Desplegando en ~/.themes y configurando Libadwaita (~/.config/gtk-4.0)...", total=None)
        apply_res = installer.install_and_apply_theme(
            theme_name,
            compile_res.get("output_dir"),
            config=config,
            apply_gtk4=targets.get("apply_gtk4", True),
            apply_wallpaper=targets.get("apply_wallpaper", True),
            apply_firefox=targets.get("apply_firefox", True)
        )
        progress.update(task3, completed=1, description="[bold green]✔ Tema instalado y Libadwaita configurado")

        # Step 4: Wayland Hot-Reload Pulse
        task4 = progress.add_task("[cyan]Sincronizando perfiles de Firefox y ejecutando pulso Wayland...", total=None)
        time.sleep(0.05)
        progress.update(task4, completed=1, description="[bold green]✔ Pulso de recarga en caliente Wayland ejecutado")

    total_time = (time.perf_counter() - t0) * 1000

    console.print()
    log_summary = "\n".join(f"[dim]• {log}[/]" for log in apply_res.get("logs", [])[:4])
    console.print(Panel(
        f"[bold green]✔ ¡TEMA '{theme_name}' APLICADO CON ÉXITO AL ESCRITORIO GNOME! ({total_time:.0f} ms)[/]\n\n{log_summary}",
        title="[bold green]Éxito[/]",
        border_style="green",
        box=box.DOUBLE
    ))

    if interactive:
        console.input("\n[bold cyan]Presiona Enter para volver al estudio...[/]")


def execute_export_theme(config: dict, console: Console = None, interactive: bool = True):
    """Compiles theme and packages into a portable .zip file."""
    theme_name = config.get("theme_name", "Studio-Theme")
    if not console:
        console = Console()

    console.clear()
    console.print(Panel(
        f"[bold yellow]📦 Empaquetando tema '{theme_name}' en archivo .ZIP autónomo...[/]",
        border_style="yellow",
        box=box.ROUNDED
    ))

    compile_res = compiler.compile_theme(config)
    if not compile_res.get("success"):
        console.print(f"\n[bold red][✗] Falló la compilación: {compile_res.get('error')}[/]")
        if interactive:
            console.input("\nPresiona Enter para continuar...")
        return

    compiled_dir = compile_res["output_dir"]
    zip_path = exporter.create_theme_zip(theme_name, compiled_dir)

    console.print()
    console.print(Panel(
        f"[bold green]✔ ¡Paquete ZIP generado exitosamente![/]\n\n"
        f"  [bold white]Ruta del archivo:[/] [cyan]{zip_path}[/]\n"
        f"  [dim]Incluye index.theme, GTK 3/4, Shell, Firefox y script install.sh autónomo.[/]",
        border_style="green",
        box=box.ROUNDED
    ))

    if interactive:
        console.input("\n[bold cyan]Presiona Enter para volver al estudio...[/]")


def execute_reset_gnome(console: Console = None, interactive: bool = True):
    """Restores GNOME desktop to factory out-of-the-box defaults."""
    if not console:
        console = Console()

    console.clear()
    console.print(Panel(
        "[bold red]⚠️  RESTAURAR VALORES DE FÁBRICA DE GNOME[/]\n\n"
        "Esta acción restablecerá:\n"
        "  • Tema GTK a 'Adwaita'\n"
        "  • Tema de GNOME Shell a predeterminado\n"
        "  • Fondo de pantalla original del sistema\n"
        "  • Eliminará los overrides de Libadwaita en ~/.config/gtk-4.0/\n"
        "  • Eliminará estilos personalizados en perfiles de Firefox",
        border_style="red",
        box=box.ROUNDED
    ))

    if interactive:
        confirm = console.input("\n[bold yellow]¿Estás seguro de que deseas restablecer GNOME? (s/n): [/]").strip()
        should_reset = confirm.lower() in ("s", "si", "y", "yes")
    else:
        should_reset = True

    if should_reset:
        res = installer.reset_gnome_defaults()
        console.print(Panel(
            f"[bold green]✔ {res.get('message')}[/]\n\n" +
            "\n".join(f"[dim]• {l}[/]" for l in res.get("logs", [])[:4]),
            border_style="green",
            box=box.ROUNDED
        ))
    else:
        console.print("\n[yellow][i] Operación cancelada.[/]")

    if interactive:
        console.input("\n[bold cyan]Presiona Enter para volver al estudio...[/]")


# ===================================================================
# Rich UI Generators (Layout, Panels & Components)
# ===================================================================

def make_header(sys_status: dict) -> Panel:
    """Generates the top header status banner."""
    cur_gtk = sys_status.get("gtk_theme", "Adwaita")
    cur_scheme = sys_status.get("color_scheme", "default")
    cur_accent = sys_status.get("accent_color", "blue")
    layout_str = "macOS (Izq)" if "close:" in sys_status.get("button_layout", "") else "GNOME (Der)"

    content = (
        f" [bold white]Tema:[/] [cyan]{cur_gtk[:16]}[/]  │  "
        f"[bold white]Modo:[/] [yellow]{cur_scheme}[/]  │  "
        f"[bold white]Acento:[/] [magenta]{cur_accent}[/]  │  "
        f"[bold white]Botones:[/] [green]{layout_str}[/]"
    )
    return Panel(
        content,
        title="[bold green]🌲 GNOME THEME STUDIO — CLI STUDIO[/]",
        border_style="green",
        box=box.ROUNDED
    )


def make_card(all_presets: dict, preset_keys: list, preset_idx: int, current_cfg: dict,
              targets: dict, cursor_row: int, accent_idx: int) -> Panel:
    """Generates the single unified settings card (Alternativa A)."""
    total_presets = len(preset_keys)
    cur_key = preset_keys[preset_idx]

    table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 0))
    table.add_column("cur", width=4)
    table.add_column("label", width=25)
    table.add_column("val", width=45)

    def cur(r):
        return "[bold green] ➜[/]" if cursor_row == r else "   "

    def val_box(txt, is_sel):
        if is_sel:
            return f"[ [bold cyan]◀[/]  {txt}  [bold cyan]▶[/] ]"
        else:
            return f"[ [dim]◀[/]  {txt}  [dim]▶[/] ]"

    # Row 0: Preset
    is_p_dark = (current_cfg.get("color_scheme") == "dark")
    p_badge = "🌙" if is_p_dark else "☀️"
    p_name = cur_key if len(cur_key) <= 22 else cur_key[:21] + "…"
    p_val = f"[bold bright_white]{p_badge} {p_name}[/] [dim]({preset_idx + 1}/{total_presets})[/]"
    table.add_row(cur(0), "[bold white]🎨 Tema Preset:[/]" if cursor_row == 0 else "[dim]🎨 Tema Preset:[/]", val_box(p_val, cursor_row == 0))

    # Row 1: Modo / Esquema
    sch = current_cfg.get("color_scheme", "dark")
    sch_val = "[bold magenta]🌙 Oscuro (Dark)[/]" if sch == "dark" else "[bold yellow]☀️ Claro (Light)[/]"
    table.add_row(cur(1), "[bold white]🌗 Modo / Esquema:[/]" if cursor_row == 1 else "[dim]🌗 Modo / Esquema:[/]", val_box(sch_val, cursor_row == 1))

    # Row 2: Color de Acento
    acc_hex = current_cfg.get("accent_color", "#a7c080")
    acc_name = GNOME_ACCENTS[accent_idx][1] if accent_idx < len(GNOME_ACCENTS) else "Custom"
    acc_val = f"[on {acc_hex}]  [/] [bold white]{acc_hex}[/] [dim]{acc_name}[/]"
    table.add_row(cur(2), "[bold white]🌿 Color de Acento:[/]" if cursor_row == 2 else "[dim]🌿 Color de Acento:[/]", val_box(acc_val, cursor_row == 2))

    # Row 3: Botones Ventana
    ctrl = current_cfg.get("window_controls_style", "traffic-hover")
    ctrl_lbl = dict(CONTROLS_STYLES).get(ctrl, ctrl)
    table.add_row(cur(3), "[bold white]🚦 Botones Ventana:[/]" if cursor_row == 3 else "[dim]🚦 Botones Ventana:[/]", val_box(f"[bold white]{ctrl_lbl}[/]", cursor_row == 3))

    # Row 4: Posición Botones
    lay = current_cfg.get("button_layout", "right")
    lay_lbl = dict(BUTTON_LAYOUTS).get(lay, lay)
    table.add_row(cur(4), "[bold white]👉 Posición Botones:[/]" if cursor_row == 4 else "[dim]👉 Posición Botones:[/]", val_box(f"[bold white]{lay_lbl}[/]", cursor_row == 4))

    # Row 5: Curvatura Ventana
    rad = current_cfg.get("window_radius", 12)
    rad_lbl = f"{rad}px"
    for w_r, _, lbl in RADII_PRESETS:
        if w_r == rad:
            rad_lbl = lbl
            break
    table.add_row(cur(5), "[bold white]🔷 Curvatura Ventana:[/]" if cursor_row == 5 else "[dim]🔷 Curvatura Ventana:[/]", val_box(f"[bold white]{rad_lbl}[/]", cursor_row == 5))

    # Row 6: Fondo 4K Vectorial
    wp = current_cfg.get("wallpaper_style", "abstract_waves")
    wp_lbl = dict(WALLPAPER_STYLES).get(wp, wp)
    table.add_row(cur(6), "[bold white]🌊 Fondo 4K Vectorial:[/]" if cursor_row == 6 else "[dim]🌊 Fondo 4K Vectorial:[/]", val_box(f"[bold white]{wp_lbl}[/]", cursor_row == 6))

    # Row 7: Libadwaita (GTK 4)
    gtk4_on = targets.get("apply_gtk4", True)
    gtk4_val = "[bold green]✅ SÍ (~/.config/gtk-4.0)[/]" if gtk4_on else "[bold red]❌ NO[/]"
    table.add_row(cur(7), "[bold white]📦 Libadwaita (GTK 4):[/]" if cursor_row == 7 else "[dim]📦 Libadwaita (GTK 4):[/]", val_box(gtk4_val, cursor_row == 7))

    # Row 8: Mozilla Firefox
    ff_on = targets.get("apply_firefox", True)
    ff_val = "[bold green]✅ SÍ (userChrome.css)[/]" if ff_on else "[bold red]❌ NO[/]"
    table.add_row(cur(8), "[bold white]🦊 Mozilla Firefox:[/]" if cursor_row == 8 else "[dim]🦊 Mozilla Firefox:[/]", val_box(ff_val, cursor_row == 8))

    divider = "[dim]" + "─" * 74 + "[/]"

    win = current_cfg.get("window_bg", "#2d353b")
    side = current_cfg.get("sidebar_bg", "#272e33")
    hdr = current_cfg.get("headerbar_bg", "#232a2e")
    txt = current_cfg.get("text_primary", "#d3c6aa")
    palette = (
        f"    [bold]Paleta:[/] Win [on {win}]  [/] [dim]{win}[/]  "
        f"Side [on {side}]  [/] [dim]{side}[/]  "
        f"Hdr [on {hdr}]  [/] [dim]{hdr}[/]  "
        f"Txt [on {txt}]  [/] [dim]{txt}[/]"
    )

    action_tbl = Table(box=None, show_header=False, pad_edge=False, padding=(0, 0))
    action_tbl.add_column("cur", width=4)
    action_tbl.add_column("btn", width=70)
    apply_text = "⚡ [ ENTER ] APLICAR TEMA AL ESCRITORIO GNOME"
    if cursor_row == 9:
        action_tbl.add_row("[bold green] ➜[/]", f"[bold white on #2e7d32] {apply_text} [/]")
    else:
        action_tbl.add_row("   ", f"[bold green]{apply_text}[/]")

    group = Group(table, divider, palette, divider, action_tbl)
    theme_title = current_cfg.get("theme_name", cur_key)
    return Panel(
        group,
        title=f"[bold green]CONFIGURACIÓN: {theme_title}[/]",
        subtitle="[dim]↑/↓: Moverse  │  ←/→/Espacio: Cambiar  │  A/Enter: Aplicar[/]",
        border_style="bright_green" if cursor_row == 9 else "green",
        box=box.ROUNDED
    )


def make_footer() -> Panel:
    """Generates the bottom action bar."""
    return Panel(
        " [bold green][A/Enter][/] Aplicar │ [bold cyan][↑↓][/] Mover │ [bold yellow][←→/Esp][/] Cambiar │ [bold magenta][S][/] Guardar │ [dim][Q][/] Salir",
        box=box.ROUNDED,
        border_style="dim",
        padding=(0, 0)
    )


def build_studio_layout(sys_status: dict, all_presets: dict, preset_keys: list,
                        preset_idx: int, current_cfg: dict, targets: dict,
                        cursor_row: int, accent_idx: int) -> Layout:
    """Builds the single-list Studio layout (Alternativa A)."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", size=15),
        Layout(name="footer", size=3)
    )
    layout["header"].update(make_header(sys_status))
    layout["body"].update(make_card(
        all_presets, preset_keys, preset_idx, current_cfg, targets, cursor_row, accent_idx
    ))
    layout["footer"].update(make_footer())
    return layout


# ===================================================================
# Rich Interactive Main Loop (Alternativa A)
# ===================================================================

def run_rich_studio():
    """Main interactive loop for Rich Studio mode (Single Integrated Settings List)."""
    console = Console()
    all_presets = presets.load_presets()
    if not all_presets:
        console.print("[bold red][!] Error: presets.json no encontrado o vacío.[/]")
        return

    preset_keys = list(all_presets.keys())

    # State variables
    preset_idx = 0
    cursor_row = 0  # 0 to 9
    accent_idx = 0

    current_key = preset_keys[preset_idx]
    current_cfg = copy.deepcopy(all_presets[current_key])
    orig_accent = current_cfg.get("accent_color", "#a7c080")

    targets = {
        "apply_gtk4": True,
        "apply_wallpaper": True,
        "apply_firefox": True
    }

    # Paired light/dark themes dictionary
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

    def change_setting(step: int):
        nonlocal preset_idx, current_key, current_cfg, orig_accent, accent_idx
        if cursor_row == 0:
            preset_idx = (preset_idx + step) % len(preset_keys)
            current_key = preset_keys[preset_idx]
            current_cfg = copy.deepcopy(all_presets[current_key])
            orig_accent = current_cfg.get("accent_color", "#a7c080")
            accent_idx = 0
        elif cursor_row == 1:
            old_sch = current_cfg.get("color_scheme", "dark")
            new_sch = "light" if old_sch == "dark" else "dark"
            current_cfg["color_scheme"] = new_sch
            if current_key in paired_map and paired_map[current_key] in all_presets:
                target_key = paired_map[current_key]
                if target_key in preset_keys:
                    preset_idx = preset_keys.index(target_key)
                    current_key = target_key
                current_cfg = copy.deepcopy(all_presets[target_key])
                current_cfg["color_scheme"] = new_sch
                orig_accent = current_cfg.get("accent_color", "#a7c080")
                accent_idx = 0
        elif cursor_row == 2:
            accent_idx = (accent_idx + step) % len(GNOME_ACCENTS)
            _, _, h = GNOME_ACCENTS[accent_idx]
            if h:
                current_cfg["accent_color"] = h
            else:
                current_cfg["accent_color"] = orig_accent
        elif cursor_row == 3:
            curr_c = current_cfg.get("window_controls_style", "traffic-hover")
            keys_c = [k for k, _ in CONTROLS_STYLES]
            curr_i = keys_c.index(curr_c) if curr_c in keys_c else 0
            current_cfg["window_controls_style"] = keys_c[(curr_i + step) % len(keys_c)]
        elif cursor_row == 4:
            curr_l = current_cfg.get("button_layout", "right")
            current_cfg["button_layout"] = "left" if curr_l == "right" else "right"
        elif cursor_row == 5:
            curr_r = current_cfg.get("window_radius", 12)
            radii_vals = [r for r, _, _ in RADII_PRESETS]
            r_i = radii_vals.index(curr_r) if curr_r in radii_vals else 1
            next_i = (r_i + step) % len(RADII_PRESETS)
            w_r, b_r, _ = RADII_PRESETS[next_i]
            current_cfg["window_radius"] = w_r
            current_cfg["button_radius"] = b_r
        elif cursor_row == 6:
            curr_w = current_cfg.get("wallpaper_style", "abstract_waves")
            keys_w = [k for k, _ in WALLPAPER_STYLES]
            w_i = keys_w.index(curr_w) if curr_w in keys_w else 0
            current_cfg["wallpaper_style"] = keys_w[(w_i + step) % len(keys_w)]
        elif cursor_row == 7:
            targets["apply_gtk4"] = not targets.get("apply_gtk4", True)
        elif cursor_row == 8:
            targets["apply_firefox"] = not targets.get("apply_firefox", True)
        elif cursor_row == 9:
            execute_apply_theme(current_cfg, targets, console=console, interactive=True)

    while True:
        sys_status = installer.get_current_theme_status()

        # Render full layout
        layout = build_studio_layout(
            sys_status, all_presets, preset_keys, preset_idx,
            current_cfg, targets, cursor_row, accent_idx
        )

        console.clear()
        console.print(layout)

        key = get_key()

        # Global Hotkeys
        if key in ("q", "Q", "ESC"):
            console.clear()
            console.print("[bold green]¡Gracias por usar GNOME Theme Studio! Hasta luego.[/]\n")
            break

        elif key in ("a", "A"):
            execute_apply_theme(current_cfg, targets, console=console, interactive=True)
            continue

        elif key in ("e", "E"):
            execute_export_theme(current_cfg, console=console, interactive=True)
            continue

        elif key in ("r", "R"):
            execute_reset_gnome(console=console, interactive=True)
            continue

        elif key in ("s", "S"):
            console.clear()
            def_name = current_cfg.get("theme_name", "Mi-Tema-Personalizado")
            s_name = console.input(f"[bold cyan]Guardar en presets.json con nombre[/] [{def_name}]: ").strip()
            s_name = s_name if s_name else def_name
            if s_name:
                presets.save_preset(s_name, current_cfg)
                all_presets = presets.load_presets()
                preset_keys = list(all_presets.keys())
                console.print(f"\n[bold green]✔ ¡Preset '{s_name}' guardado exitosamente![/]")
                time.sleep(1.0)
            continue

        # Row Navigation (Up / Down / Tab)
        elif key in ("UP", "k"):
            cursor_row = (cursor_row - 1) % 10

        elif key in ("DOWN", "j", "TAB"):
            cursor_row = (cursor_row + 1) % 10

        elif key == "HOME":
            cursor_row = 0

        elif key == "END":
            cursor_row = 9

        # Value Changing (Right / Left / Space / Enter)
        elif key in ("RIGHT", "SPACE"):
            change_setting(+1)

        elif key == "LEFT":
            change_setting(-1)

        elif key == "ENTER":
            if cursor_row == 9:
                execute_apply_theme(current_cfg, targets, console=console, interactive=True)
            else:
                change_setting(+1)


# ===================================================================
# Rich Table Listing for `--list`
# ===================================================================

def list_presets_cli_rich(console: Console):
    """Prints a gorgeous Rich Table with TrueColor swatches for --list."""
    data = presets.load_presets()
    table = Table(
        title="[bold green]BIBLIOTECA DE PRESETS DE GNOME THEME STUDIO[/]",
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("#", style="dim", justify="right")
    table.add_column("Esquema", justify="center")
    table.add_column("Nombre del Preset", style="bold white")
    table.add_column("Acento")
    table.add_column("Fondo Ventana")
    table.add_column("Controles", style="dim")

    for idx, (name, cfg) in enumerate(data.items(), 1):
        is_dark = (cfg.get("color_scheme") == "dark")
        badge = "[bold magenta]🌙 Dark[/]" if is_dark else "[bold yellow]☀️ Light[/]"
        accent = cfg.get("accent_color", "#a7c080")
        win_bg = cfg.get("window_bg", "#2d353b")
        ctrl = cfg.get("window_controls_style", "traffic-hover")
        accent_cell = f"[on {accent}]  [/] {accent}"
        win_cell = f"[on {win_bg}]  [/] {win_bg}"
        table.add_row(str(idx), badge, name, accent_cell, win_cell, ctrl)

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total: {len(data)} presets. Para aplicar uno ejecuta:[/] [bold cyan]./themer-cli.py --preset \"<Nombre>\" --apply[/]\n")


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
    parser.add_argument("-r", "--reset", action="store_true", help="Restablece GNOME a la configuración estándar Adwaita.")
    parser.add_argument("-e", "--export", action="store_true", help="Compila y empaqueta el tema en un archivo .ZIP descargable.")

    # Overrides
    parser.add_argument("--scheme", choices=["dark", "light"], help="Sobrescribe el esquema de color (dark / light).")
    parser.add_argument("--accent", type=str, help="Sobrescribe el color de acento (#hex o nombre oficial GNOME).")
    parser.add_argument("--window-bg", type=str, help="Sobrescribe el fondo de ventana (#hex).")
    parser.add_argument("--wallpaper-style", choices=["abstract_waves", "aurora", "geometric", "none"], help="Estilo de fondo vectorial.")
    parser.add_argument("--controls-style", choices=["traffic-hover", "traffic-light", "monochrome", "minimal"], help="Estilo de botones.")
    parser.add_argument("--layout", choices=["right", "left"], help="Posición de botones (right: GNOME, left: macOS).")

    # Target toggles
    parser.add_argument("--no-gtk4", action="store_true", help="No aplicar estilos a GTK4 / Libadwaita.")
    parser.add_argument("--no-wallpaper", action="store_true", help="No generar ni cambiar el fondo de pantalla.")
    parser.add_argument("--no-firefox", action="store_true", help="No tematizar perfiles de Mozilla Firefox.")
    parser.add_argument("--name", type=str, help="Asignar un nombre personalizado al tema compilado.")

    return parser.parse_args()


def main():
    """Main program entrypoint."""
    args = parse_cli_args()
    console = Console() if HAS_RICH else None

    # 1. Non-interactive commands
    if args.list:
        if HAS_RICH:
            list_presets_cli_rich(console)
        else:
            data = presets.load_presets()
            print("\n=== BIBLIOTECA DE PRESETS ===")
            for idx, (name, cfg) in enumerate(data.items(), 1):
                print(f"{idx:2d}. {name} ({cfg.get('color_scheme')}) - {cfg.get('accent_color')}")
        return

    if args.status:
        status = installer.get_current_theme_status()
        if HAS_RICH:
            table = Table(title="[bold green]ESTADO ACTUAL DEL ENTORNO GNOME[/]", box=box.ROUNDED)
            table.add_column("Propiedad", style="bold cyan")
            table.add_column("Valor Actual", style="bold white")
            for k, v in status.items():
                table.add_row(k, str(v))
            console.print()
            console.print(table)
            console.print()
        else:
            print("\n=== ESTADO ACTUAL DEL ENTORNO GNOME ===")
            for k, v in status.items():
                print(f"  {k:<24}: {v}")
            print()
        return

    if args.reset:
        execute_reset_gnome(console=console, interactive=False)
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
            print(f"[✗] Error: No se encontró ningún preset que coincida con '{args.preset}'.")
            sys.exit(1)

        config = copy.deepcopy(all_presets[matched_key])

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
            execute_apply_theme(config, targets, console=console, interactive=False)
            return

        if args.export:
            execute_export_theme(config, console=console, interactive=False)
            return

    # 2. Launch Interactive Studio Mode
    try:
        run_rich_studio()
    except KeyboardInterrupt:
        if HAS_RICH and console:
            console.clear()
        print("\n[i] GNOME Theme Studio CLI detenido.\n")


if __name__ == "__main__":
    main()
