# 🌲 GNOME Theme Studio

[![Linux](https://img.shields.io/badge/Platform-Linux%20%7C%20GNOME-blue?logo=linux&logoColor=white)](https://www.gnome.org/)
[![GNOME Shell](https://img.shields.io/badge/GNOME%20Shell-45%20%7C%2046%20%7C%2047%20%7C%2051%2B-orange?logo=gnome)](https://gitlab.gnome.org/GNOME/gnome-shell)
[![GTK Versions](https://img.shields.io/badge/GTK-3%20%7C%204%20(Libadwaita)-green?logo=gtk)](https://www.gtk.org/)
[![Firefox](https://img.shields.io/badge/Browser-Mozilla%20Firefox-critical?logo=firefox)](https://www.mozilla.org/firefox/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

**GNOME Theme Studio** es una suite profesional, visual y completa para crear, personalizar, compilar y aplicar temas extremadamente pulidos y unificados para el entorno de escritorio **Linux GNOME Desktop**.

Tematiza de forma sincronizada y con consistencia milimétrica:
* **GNOME Shell** (45, 46, 47, 51+)
* **GTK 4 / Libadwaita** (Nautilus, Ajustes, Monitor del Sistema, Visor de Textos, etc.)
* **GTK 3** (GIMP, Inkscape, Nemo, pavucontrol, gestores de archivos clásicos)
* **Mozilla Firefox**, LibreWolf y Waterfox (mediante `userChrome.css` y `userContent.css`)
* **Aplicaciones Flatpak** sandboxed
* **Fondos de pantalla vectoriales 4K a juego** generados algorítmicamente.

---

## 📸 Capturas de Pantalla (Showcase)

<!-- Coloca tus capturas en la carpeta screenshots/ con los nombres: desktop.png, studio.png, nautilus.png y firefox.png -->

<p align="center">
  <img src="screenshots/desktop.png" alt="GNOME Theme Studio Desktop Showcase" width="100%">
  <br>
  <em>Escritorio GNOME completo con tema aplicado, panel superior, aplicaciones Libadwaita y fondo de pantalla vectorial 4K a juego.</em>
</p>

<p align="center">
  <img src="screenshots/studio.png" alt="GNOME Theme Studio Web Interface" width="100%">
  <br>
  <em>Estudio visual interactivo en tiempo real con selector de presets, paleta de colores y ajuste de métricas.</em>
</p>

<table align="center" width="100%">
  <tr>
    <td width="50%" align="center">
      <img src="screenshots/nautilus.png" alt="Integración GTK 4 / Libadwaita en Nautilus" width="100%"><br>
      <b>Libadwaita / Nautilus (Zero-Desfase)</b><br>
      <sub>Headerbar continuo de borde a borde y barra lateral perfectamente alineada sin franjas residuales.</sub>
    </td>
    <td width="50%" align="center">
      <img src="screenshots/firefox.png" alt="Integración Mozilla Firefox userChrome" width="100%"><br>
      <b>Mozilla Firefox + userChrome</b><br>
      <sub>Pestañas nativas integradas y botones de ventana con semáforo hover interactivo.</sub>
    </td>
  </tr>
</table>

> 💡 **Nota para capturas**: Consulta la [Guía de Capturas de Pantalla](screenshots/README.md) para conocer las resoluciones y nombres recomendados al subir tus imágenes a GitHub.

---

## ✨ Características Destacadas (Key Features)

### 🎨 1. Estudio Visual en Tiempo Real (Web UI)
Interfaz web moderna con visualizador interactivo (Mockup) que refleja en vivo cada cambio de color, radio de curvatura y grosor de bordes antes de compilar o aplicar al sistema.

### 📐 2. Arquitectura de Título y Barra Superior de Nautilus (Zero-Desfase)
En Libadwaita moderna (`AdwToolbarView`), muchas implementaciones de temas provocan un desfase o franja de 6 píxeles sobre la barra de título de Nautilus (donde el fondo de la ventana se filtra). GNOME Theme Studio implementa una estructura CSS de alta precisión:
* El contenedor superior (`toolbarview > .top-bar`) absorbe uniformemente el color de la barra desde el píxel 0.
* Los `headerbar` interiores se mantienen 100% transparentes, eliminando solapamientos o sombras duplicadas.
* La barra superior del panel lateral (`.sidebar-pane`) adopta de extremo a extremo el color del sidebar (`@sidebar_bg_color`), asegurando una continuidad estética perfecta entre panel y contenido.
* Ventanas maximizadas o a pantalla completa eliminan limpiamente los bordes redondeados (`border-radius: 0 !important`).

### 🦊 3. Integración Nativa con Mozilla Firefox
A diferencia de otros temas donde el navegador queda aislado del resto del escritorio:
* Detecta automáticamente perfiles activos en rutas **XDG modernas** (`~/.config/mozilla/firefox/`), rutas clásicas (`~/.mozilla/firefox/`), **Flatpak** y **Snap**, así como LibreWolf y Waterfox.
* Compila dinámicamente `userChrome.css` y `userContent.css` con los colores exactos de la paleta.
* Configura de forma transparente `user.js` con `toolkit.legacyUserProfileCustomizations.stylesheets = true` y dibujado en barra de título.
* **Controles de ventana precisos**: El contenedor exterior permanece 100% transparente y el semáforo hover (`traffic-hover`) ilumina únicamente el botón que recibe el foco, sin desbordamientos de color.

### ⚡ 4. Compilador Multi-Destino Basado en SCSS (`sassc`)
Compila hojas de estilo completas en menos de 300 milisegundos:
* Inyección dinámica de variables y métricas.
* Sustitución inteligente de color primario y secundario en iconos SVG (`gnome-shell-start.svg`, calendarios, workspaces).
* Conmutación automática en GTK 3: hereda de `gtk-contained.css` si el tema es claro, o `gtk-contained-dark.css` si es oscuro.

### 🔁 5. Aplicador y Recarga en Caliente en 1-Clic (Hot-Reload)
* Aplica el tema sin reiniciar la sesión en entornos **Wayland** y **X11** mediante un pulso coordinado a través de `gsettings` y `dconf`.
* Sincroniza el color de acento oficial del sistema (`accent-color` de GNOME 47+) con el tono más cercano de la paleta.

### 🖼️ 6. Generador de Fondos de Pantalla Vectoriales 4K
Genera y aplica fondos SVG matemáticos (3840×2160) en estilos:
* **Abstract Waves** (Ondas orgánicas fluidas estilo GNOME)
* **Aurora** (Gradientes radiales atmosféricos de alto contraste)
* **Geometric** (Polígonos modernos facetados con transparencias sutiles)

### 📦 7. Exportador de Temas Portables (.ZIP)
Genera paquetes `.zip` listos para distribuir con un script instalador autónomo (`install.sh`) para que cualquier usuario de Linux pueda instalar tu creación con un solo comando.

---

## 🗂️ Biblioteca de Presets Incluidos (22 Paletas Calibradas)

| Preset | Variante | Acento Primario | Fondo de Ventana |
| :--- | :---: | :---: | :---: |
| **Everforest Dark** *(Flagship)* | Oscuro | `#a7c080` (Forest Green) | `#2d353b` |
| **Everforest Light** | Claro | `#8da101` (Soft Olive) | `#fdf6e3` |
| **Catppuccin Mocha** | Oscuro | `#cba6f7` (Mauve) | `#1e1e2e` |
| **Catppuccin Latte** | Claro | `#8839ef` (Mauve) | `#eff1f5` |
| **Tokyo Night** | Oscuro | `#7aa2f7` (Neon Blue) | `#1a1b26` |
| **Tokyo Night Day** | Claro | `#34548a` (Deep Blue) | `#e1e2e7` |
| **Nord Dark** | Oscuro | `#88c0d0` (Frost Cyan) | `#2e3440` |
| **Nord Snow Storm** | Claro | `#5e81ac` (Deep Frost) | `#eceff4` |
| **Gruvbox Dark** | Oscuro | `#b8bb26` (Bright Green) | `#282828` |
| **Gruvbox Light** | Claro | `#79740e` (Dark Green) | `#fbf1c7` |
| **Dracula** | Oscuro | `#bd93f9` (Purple) | `#282a36` |
| **Rosé Pine** | Oscuro | `#ebbcba` (Rose) | `#191724` |
| **Rosé Pine Dawn** | Claro | `#d7827e` (Rose Dawn) | `#faf4ed` |
| **Cyberpunk 2077** | Oscuro | `#00f0ff` (Cyan Neon) | `#12131a` |
| **One Dark Pro** | Oscuro | `#61afef` (Atom Blue) | `#282c34` |
| **One Light** | Claro | `#4078f2` (Atom Blue) | `#fafafa` |
| **Kanagawa Wave** | Oscuro | `#98bb6c` (Spring Green) | `#1f1f28` |
| **Monokai Pro** | Oscuro | `#ffd866` (Sun Yellow) | `#2d2a2e` |
| **Adwaita Dark** | Oscuro | `#3584e4` (GNOME Blue) | `#242424` |
| **Adwaita Light** | Claro | `#3584e4` (GNOME Blue) | `#fafafa` |
| **Solarized Dark** | Oscuro | `#268bd2` (Solar Blue) | `#002b36` |
| **Solarized Light** | Claro | `#268bd2` (Solar Blue) | `#fdf6e3` |

---

## 📋 Requisitos del Sistema (Prerequisites)

Para ejecutar GNOME Theme Studio o compilar temas en tu equipo necesitas:

### 1. Dependencias del Sistema
* **Entorno de escritorio GNOME** (GNOME Shell 45, 46, 47, 51+)
* **`sassc`**: Compilador binario de SCSS (imprescindible para el Theme Studio).
* **`python3`** (3.10 o superior) y módulo `python3-venv`.
* **Extensión `user-theme`**: Requerida por GNOME para permitir temas de terceros en el Shell (`user-theme@gnome-shell-extensions.gcampax.github.com`).

#### Comando de instalación según tu distribución:

**Fedora / RHEL / CentOS:**
```bash
sudo dnf install -y sassc python3 python3-pip gnome-shell-extension-user-theme
```

**Ubuntu / Debian / Linux Mint:**
```bash
sudo apt update
sudo apt install -y sassc python3 python3-venv python3-pip gnome-shell-extension-prefs gnome-shell-extensions
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S --needed sassc python gnome-shell-extensions
```

---

## 🚀 Guía de Inicio Rápido (Quick Start)

Puedes utilizar el proyecto en dos modalidades: mediante el **Estudio Visual Web interactivo** o mediante el **Instalador de Terminal CLI**.

### Método A: Estudio Visual Web (Recomendado)

1. Clona el repositorio y entra a la carpeta:
   ```bash
   git clone https://github.com/TU_USUARIO/gnome-theme-studio.git
   cd gnome-theme-studio
   ```

2. Inicia el servidor de Theme Studio:
   ```bash
   ./start.sh
   ```

3. Se abrirá automáticamente tu navegador en `http://localhost:5000`:
   - Selecciona cualquiera de los **22 presets** o crea tu paleta personalizada.
   - Ajusta colores de fondo, acento, cabeceras, superficies y texto.
   - Modifica métricas en vivo: radio de ventana, radio de botones y estilo de controles.
   - Elige el estilo de fondo de pantalla vectorial 4K.
   - Haz clic en **"Compilar, Instalar y Aplicar"** para ver tu escritorio transformarse al instante.

---

### Método B: Instalador CLI Directo (Terminal)

Si deseas aplicar de inmediato la versión precompilada del tema insigne (**Everforest Dark**) sin levantar el servidor web:

```bash
./install.sh
```

El script ejecutará automáticamente:
1. Copia de temas en `~/.themes/Everforest-Dark` y `~/.local/share/themes/Everforest-Dark`.
2. Configuración de **GTK 4 / Libadwaita** en `~/.config/gtk-4.0/gtk.css`.
3. Integración con **Mozilla Firefox** en todos los perfiles de usuario detectados.
4. Concesión de permisos a aplicaciones **Flatpak**.
5. Activación de la extensión `user-theme` y fijación del tema en `gsettings` y `dconf`.
6. Pulso de recarga en caliente para refrescar la interfaz sin cerrar sesión.

#### Comandos adicionales del instalador CLI:
```bash
# Ver el estado actual de tu entorno GNOME
./install.sh --status

# Desinstalar y volver a la configuración estándar Adwaita
./install.sh --uninstall
```

---

## 🛠️ Estructura del Repositorio (Repository Structure)

```text
gnome-theme-studio/
├── README.md                      # Documentación completa para usuarios y desarrolladores
├── AGENTS.md                      # Especificaciones técnicas y contratos para Agentes AI
├── LICENSE                        # Licencia de código abierto MIT
├── .gitignore                     # Filtro de archivos compilados, temporales y venv
├── requirements.txt               # Dependencias Python (Flask)
├── start.sh                       # Lanzador del Theme Studio Web (gestiona venv y navegador)
├── install.sh                     # Instalador y configurador CLI autónomo
├── uninstall.sh                   # Restaurador a valores de fábrica de GNOME
├── index.theme                    # Metadatos estándar FreeDesktop
├── app.py                         # Servidor Flask y API REST
├── compiler.py                    # Motor de inyección y compilación Sass/SCSS
├── installer.py                   # Motor del sistema: gsettings, dconf, Firefox y Flatpak
├── presets.py                     # Controlador de carga, guardado y borrado de presets
├── presets.json                   # Base de datos con las 22 paletas calibradas
├── wallpaper_generator.py         # Motor generador de fondos de pantalla vectoriales 4K SVG
├── exporter.py                    # Creador de paquetes ZIP distribuibles con instalador autónomo
├── base_theme/                    # Fuentes maestras SCSS inmutables
│   ├── scss/                      # Variables y métricas dinámicas
│   ├── gnome-shell/               # SCSS y assets SVG para GNOME Shell 51
│   ├── gtk-3.0/                   # SCSS y conmutador de base para GTK 3
│   ├── gtk-4.0/                   # SCSS con arquitectura Zero-Desfase para Libadwaita
│   └── firefox/                   # Plantillas maestras userChrome.scss y userContent.scss
├── screenshots/                   # Capturas de pantalla para el repositorio de GitHub
│   └── README.md                  # Guía de nombres y resoluciones para las capturas
├── templates/
│   └── index.html                 # Interfaz visual del Theme Studio con mockup interactivo
└── static/
    ├── css/                       # Estilos del Theme Studio
    └── js/
        └── app.js                 # Lógica interactiva del frontend, preview y peticiones API
```

---

## 🔧 Personalización Avanzada y Desarrollo (Hacking & Development)

### Añadir un nuevo Preset
Edita `presets.json` o guarda tu preset directamente desde la interfaz web haciendo clic en **"Guardar como nuevo preset"**. Cada preset contiene:
```json
{
  "theme_name": "Mi-Tema-Custom",
  "color_scheme": "dark",
  "accent_color": "#00f0ff",
  "accent_fg": "#101216",
  "accent_secondary": "#7000ff",
  "window_bg": "#12131a",
  "sidebar_bg": "#0c0d12",
  "surface_elevated": "#1b1d28",
  "headerbar_bg": "#08090d",
  "text_primary": "#f0f2f5",
  "text_muted": "#828799",
  "border_color": "#232636",
  "border_active": "#32374d",
  "destructive_color": "#ff0055",
  "warning_color": "#ffe600",
  "window_radius": 12,
  "button_radius": 8,
  "border_width": 1,
  "panel_opacity": 1.0,
  "popup_radius": 16,
  "quick_settings_radius": 32,
  "window_controls_style": "traffic-hover",
  "window_controls_size": 14,
  "button_layout": "right",
  "wallpaper_style": "abstract_waves"
}
```

### Probar compilación manual mediante Python:
```bash
python3 -c "
import compiler, presets
config = presets.load_presets()['Everforest Dark']
res = compiler.compile_theme(config)
print('Compilación exitosa:', res['success'], 'en', res['duration_ms'], 'ms')
"
```

---

## 🗑️ Restauración del Sistema (Uninstallation)

Si en cualquier momento deseas volver a la apariencia original y limpia de GNOME:
1. Desde la Web: Pulsa el botón **"Restablecer Predeterminados de GNOME"**.
2. Desde la Terminal: Ejecuta `./uninstall.sh`.

Esto restablecerá:
* Tema GTK a `Adwaita`
* Esquema de color y color de acento a los valores por defecto del sistema
* Tema de GNOME Shell al predeterminado del sistema
* Eliminación de estilos custom en `~/.config/gtk-4.0/gtk.css` y perfiles de Firefox
* Restauración del fondo de pantalla original de GNOME.

---

## 📄 Licencia y Créditos

* **Licencia:** Distribuido bajo la Licencia [MIT](LICENSE).
* **Créditos:** Diseñado para la comunidad GNOME, inspirado en el diseño limpio de Libadwaita y la elegancia cromática de paletas de código abierto como Everforest, Catppuccin, Nord y Tokyo Night.
