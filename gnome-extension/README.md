# 🧩 GNOME Theme Studio — Quick Settings Extension

Extensión oficial para **GNOME Shell (45, 46, 47, 48, 49, 50, 51+)** que integra **GNOME Theme Studio** directamente en el panel de control rápido (*Quick Settings*).

---

## ✨ Características

* **Acceso Inmediato en Quick Settings**: Botón nativo de GNOME con icono de paleta, indicando el tema activo en el subtítulo.
* **Menú Desplegable con Scroll**: Lista fluida de más de 20 temas y presets calibrados (Everforest, Catppuccin, Tokyo Night, Dracula, Nord, Gruvbox, etc.).
* **Aplicación 1-Click Asíncrona**: Compila y aplica GTK4 (Libadwaita), GTK3, GNOME Shell, Firefox y fondos 4K sin congelar el escritorio ni la pantalla.
* **Sincronización en Tiempo Real**: Si cambias de tema desde la Web UI o la terminal (`themer-cli.py`), el Quick Settings actualiza su subtítulo y la marca de verificación automáticamente.
* **Acciones Rápidas**:
  * 🌐 *Abrir Web Studio (`localhost:5000`)* con un solo clic.
  * 🔄 *Restablecer GNOME a Adwaita por defecto* en caso de querer restaurar el escritorio de fábrica.

---

## 🚀 Instalación Rápida

Desde la raíz del repositorio, ejecuta:

```bash
./gnome-extension/install.sh
```

El script creará un enlace simbólico en:
`~/.local/share/gnome-shell/extensions/theme-studio@angelaguayo.github.io`
y habilitará la extensión.

### 🔄 Activar por primera vez en GNOME:
* **En Wayland**: Como GNOME no permite recargar el compositor en caliente cuando se detecta una extensión nueva por primera vez, **cierra tu sesión de usuario y vuelve a iniciar sesión**.
* **En X11**: Presiona `Alt + F2`, escribe `r` y presiona Enter.

---

## 🛠️ Arquitectura Técnica

* **GJS ESM**: Utiliza la arquitectura de módulos ECMAScript moderna (`import ... from 'gi://...'` y `resource:///org/gnome/shell/...`).
* **`QuickSettings.QuickMenuToggle`**: Hereda del componente estándar de GNOME para garantizar consistencia visual y de comportamiento.
* **`Gio.Subprocess` Asíncrono**: Dispara las llamadas al CLI de `themer-cli.py --preset "<Nombre>" --apply` usando tuberías asíncronas para que el hilo de renderizado del compositor de GNOME permanezca a 60/120+ FPS.
* **Detección Automática de `venv`**: Si el repositorio tiene un entorno virtual de Python (`venv/bin/python3`), la extensión lo utiliza automáticamente para garantizar la disponibilidad de todas las dependencias (`rich`, `sassc`, etc.).
