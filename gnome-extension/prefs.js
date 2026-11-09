/**
 * GNOME Theme Studio — Preferences Window (prefs.js)
 * Compatible with GNOME Shell 45–51+ (ESM architecture)
 *
 * Allows configuring favorite presets shown in Quick Settings,
 * toggling compact mode (5 favorites only), and customizing shortcuts
 * from the Extensions Manager (Gestor de Extensiones).
 */

import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Gtk from 'gi://Gtk';

import { ExtensionPreferences, gettext as _ } from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

const FALLBACK_PRESETS = [
    'Everforest Dark',
    'Everforest Light',
    'Catppuccin Mocha',
    'Catppuccin Latte',
    'Tokyo Night',
    'Tokyo Night Day',
    'Nord Dark',
    'Nord Snow Storm',
    'Gruvbox Dark',
    'Gruvbox Light',
    'Dracula',
    'Rosé Pine',
    'Rosé Pine Dawn',
    'Cyberpunk 2077',
    'One Dark Pro',
    'One Light',
    'Kanagawa Wave',
    'Monokai Pro',
    'Adwaita Dark',
    'Adwaita Light',
    'Solarized Dark',
    'Solarized Light',
];

export default class ThemeStudioPreferences extends ExtensionPreferences {
    /**
     * Resolves project root directory to read presets.json dynamically.
     */
    _findProjectDir() {
        const envDir = GLib.getenv('GNOME_THEME_STUDIO_DIR');
        if (envDir && GLib.file_test(envDir, GLib.FileTest.IS_DIR)) {
            return envDir;
        }

        const extPath = this.path;
        if (extPath) {
            const parentDir = GLib.path_get_dirname(extPath);
            const parentCli = GLib.build_filenamev([parentDir, 'themer-cli.py']);
            if (GLib.file_test(parentCli, GLib.FileTest.EXISTS)) {
                return parentDir;
            }

            try {
                const file = Gio.File.new_for_path(extPath);
                const info = file.query_info('standard::symlink-target', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
                const target = info.get_symlink_target();
                if (target) {
                    const resolvedParent = GLib.path_get_dirname(target);
                    const targetCli = GLib.build_filenamev([resolvedParent, 'themer-cli.py']);
                    if (GLib.file_test(targetCli, GLib.FileTest.EXISTS)) {
                        return resolvedParent;
                    }
                }
            } catch (_) {}
        }

        const homeDir = GLib.get_home_dir();
        const candidateHome = GLib.build_filenamev([homeDir, 'gnome-theme-studio']);
        if (GLib.file_test(GLib.build_filenamev([candidateHome, 'themer-cli.py']), GLib.FileTest.EXISTS)) {
            return candidateHome;
        }

        return '/home/angelaguayo/gnome-theme-studio';
    }

    /**
     * Loads preset names from presets.json or returns fallbacks.
     */
    _loadPresetNames() {
        try {
            const projectDir = this._findProjectDir();
            const presetsPath = GLib.build_filenamev([projectDir, 'presets.json']);
            const [ok, contents] = GLib.file_get_contents(presetsPath);
            if (ok) {
                const data = JSON.parse(new TextDecoder().decode(contents));
                const names = Object.keys(data);
                if (names.length > 0) {
                    return names;
                }
            }
        } catch (e) {
            console.warn(`[ThemeStudioPrefs] Fallback a presets por defecto: ${e.message}`);
        }
        return FALLBACK_PRESETS;
    }

    /**
     * Populates the Preferences Window when opened from the Extensions app.
     */
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        const presetNames = this._loadPresetNames();

        window.set_default_size(680, 750);

        // --- Main Preferences Page ---
        const page = new Adw.PreferencesPage({
            title: _('Personalización'),
            icon_name: 'preferences-desktop-theme-symbolic',
        });
        window.add(page);

        // --- Group 1: 5 Quick Presets for Quick Settings ---
        const groupPresets = new Adw.PreferencesGroup({
            title: _('Presets Rápidos en Quick Settings'),
            description: _('Selecciona los 5 temas que aparecerán directamente en el menú de Quick Settings para un acceso inmediato en 1 clic.'),
        });
        page.add(groupPresets);

        // Compact Mode Switch: Show only favorites
        const onlyFavRow = new Adw.SwitchRow({
            title: _('Mostrar únicamente los 5 favoritos'),
            subtitle: _('Mantiene el menú desplegable ligero, compacto y libre de scroll largo.'),
        });
        settings.bind('show-only-favorites', onlyFavRow, 'active', Gio.SettingsBindFlags.DEFAULT);
        groupPresets.add(onlyFavRow);

        // 5 ComboRows for selecting each favorite preset
        const defaultFavorites = [
            'Everforest Dark',
            'Catppuccin Mocha',
            'Tokyo Night',
            'Nord Dark',
            'Gruvbox Dark',
        ];

        for (let i = 1; i <= 5; i++) {
            const key = `favorite-preset-${i}`;
            const stringList = new Gtk.StringList();
            for (const name of presetNames) {
                stringList.append(name);
            }

            const comboRow = new Adw.ComboRow({
                title: _(`Opción ${i} de Quick Settings`),
                subtitle: _(`Tema asignado a la posición ${i}`),
                model: stringList,
            });

            // Set current selection
            let currentVal = settings.get_string(key);
            if (!currentVal) {
                currentVal = defaultFavorites[i - 1] || presetNames[0];
                settings.set_string(key, currentVal);
            }

            let idx = presetNames.indexOf(currentVal);
            if (idx >= 0) {
                comboRow.selected = idx;
            }

            // Save on user selection
            comboRow.connect('notify::selected', () => {
                const selectedText = presetNames[comboRow.selected];
                if (selectedText && selectedText !== settings.get_string(key)) {
                    settings.set_string(key, selectedText);
                }
            });

            // Sync if external change occurs
            settings.connect(`changed::${key}`, () => {
                const newVal = settings.get_string(key);
                const newIdx = presetNames.indexOf(newVal);
                if (newIdx >= 0 && comboRow.selected !== newIdx) {
                    comboRow.selected = newIdx;
                }
            });

            groupPresets.add(comboRow);
        }

        // --- Group 2: Quick Actions & Shortcuts ---
        const groupActions = new Adw.PreferencesGroup({
            title: _('Acciones y Accesos Directos'),
            description: _('Controla qué botones auxiliares se muestran al final del menú desplegable.'),
        });
        page.add(groupActions);

        const webStudioRow = new Adw.SwitchRow({
            title: _('Acceso a Web Studio (localhost:5000)'),
            subtitle: _('Muestra el botón para abrir el estudio visual en tu navegador.'),
        });
        settings.bind('show-web-studio-shortcut', webStudioRow, 'active', Gio.SettingsBindFlags.DEFAULT);
        groupActions.add(webStudioRow);

        const resetRow = new Adw.SwitchRow({
            title: _('Botón de Restauración (Adwaita)'),
            subtitle: _('Muestra el botón para devolver el entorno a los valores de fábrica.'),
        });
        settings.bind('show-reset-shortcut', resetRow, 'active', Gio.SettingsBindFlags.DEFAULT);
        groupActions.add(resetRow);

        // --- Group 3: Behavior & Notifications ---
        const groupBehavior = new Adw.PreferencesGroup({
            title: _('Comportamiento y Notificaciones'),
        });
        page.add(groupBehavior);

        const notifyRow = new Adw.SwitchRow({
            title: _('Notificaciones del escritorio'),
            subtitle: _('Envía una notificación al sistema al compilar y aplicar un tema con éxito.'),
        });
        settings.bind('show-notifications', notifyRow, 'active', Gio.SettingsBindFlags.DEFAULT);
        groupBehavior.add(notifyRow);

        // --- Group 4: About & Links ---
        const groupAbout = new Adw.PreferencesGroup({
            title: _('Acerca de GNOME Theme Studio'),
        });
        page.add(groupAbout);

        const linkRow = new Adw.ActionRow({
            title: _('Repositorio oficial en GitHub'),
            subtitle: 'https://github.com/angelaguayo/gnome-theme-studio',
            activatable: true,
        });
        linkRow.add_suffix(new Gtk.Image({
            icon_name: 'external-link-symbolic',
            valign: Gtk.Align.CENTER,
        }));
        linkRow.connect('activated', () => {
            Gio.AppInfo.launch_default_for_uri('https://github.com/angelaguayo/gnome-theme-studio', null);
        });
        groupAbout.add(linkRow);
    }
}
