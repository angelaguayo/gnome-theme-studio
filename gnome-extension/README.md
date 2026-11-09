# 🧩 GNOME Theme Studio — Quick Settings Extension

Extensión oficial para **GNOME Shell (45, 46, 47, 48, 49, 50, 51+)** que integra **GNOME Theme Studio** directamente en el panel de control rápido (*Quick Settings*).

---

## ✨ Características

* **Acceso Inmediato en Quick Settings**: Botón nativo de GNOME con icono de paleta, indicando el tema activo en el subtítulo.
* **5 Presets Favoritos en 1 Clic**: Selector rápido de 5 temas preferidos personalizables desde la ventana de configuración.
* **Modo Compacto o Catálogo Completo**: Alterna entre mostrar únicamente los 5 favoritos seleccionados o el catálogo completo de más de 20 temas con scroll.
* **Ventana de Preferencias Nativa (Libadwaita / `prefs.js`)**: Modifica la selección de los 5 presets y opciones desde el **Gestor de Extensiones** (*Extensions app*).
* **Aplicación 1-Click Asíncrona**: Compila y aplica GTK4 (Libadwaita), GTK3, GNOME Shell, Firefox y fondos 4K sin congelar el escritorio ni la pantalla.
* **Sincronización en Tiempo Real**: Si cambias de tema desde la Web UI o la terminal (`themer-cli.py`), el Quick Settings actualiza su subtítulo y la marca de verificación automáticamente.
* **Acciones Rápidas**:
  * 🌐 *Abrir Web Studio (`localhost:5000`)* con un solo clic.
  * 🔄 *Restablecer GNOME a Adwaita por defecto* en caso de querer restaurar el escritorio de fábrica.
  * ⚙️ *Configuración de la extensión...* para abrir las preferencias al vuelo.

---

## ⚙️ Configuración y Personalización

Puedes abrir la ventana de preferencias de tres formas:
1. Desde la app **Extensiones** (o *Gestor de Extensiones* de GNOME): haz clic en el icono del engranaje **⚙** al lado de «GNOME Theme Studio».
2. Desde el menú de **Quick Settings**: haz clic en **«Configuración de la extensión...»** al pie del menú.
3. Desde la terminal:
   ```bash
   gnome-extensions prefs theme-studio@angelaguayo.github.io
   ```

### Opciones configurables:
* **Mostrar únicamente los 5 favoritos**: Activa o desactiva para mantener el menú ultra-compacto o ver la lista completa.
* **Opciones 1 a 5 de Quick Settings**: Desplegables independientes (`Adw.ComboRow`) para asignar cada uno de los 5 temas favoritos (Everforest, Catppuccin, Tokyo Night, Nord, Gruvbox, etc.).
* **Acceso a Web Studio**: Muestra u oculta el botón para abrir `http://localhost:5000`.
* **Botón de Restauración**: Muestra u oculta la acción para devolver GNOME a Adwaita.
* **Notificaciones del escritorio**: Habilita o deshabilita los avisos emergentes al aplicar temas.

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
* **`ExtensionPreferences` (`prefs.js`)**: Diálogo de preferencias nativo Libadwaita integrado con el Gestor de Extensiones (`gnome-extensions-app`) que permite seleccionar dinámicamente los 5 favoritos mediante `Adw.ComboRow`.
* **Esquema GSettings (`schemas/`)**: Guarda las preferencias del usuario bajo el esquema `org.gnome.shell.extensions.theme-studio` con sincronización reactiva en vivo en el menú del panel superior.
* **`QuickSettings.QuickMenuToggle`**: Hereda del componente estándar de GNOME para garantizar consistencia visual y de comportamiento.
* **`Gio.Subprocess` Asíncrono**: Dispara las llamadas al CLI de `themer-cli.py --preset "<Nombre>" --apply` usando tuberías asíncronas para que el hilo de renderizado del compositor de GNOME permanezca a 60/120+ FPS.
* **Detección Automática de `venv`**: Si el repositorio tiene un entorno virtual de Python (`venv/bin/python3`), la extensión lo utiliza automáticamente para garantizar la disponibilidad de todas las dependencias (`rich`, `sassc`, etc.).
