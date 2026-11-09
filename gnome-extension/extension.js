/**
 * GNOME Theme Studio — Quick Settings Extension
 * Compatible with GNOME Shell 45–51+ (ESM architecture)
 *
 * Provides a native Quick Settings toggle button with a rich dropdown
 * to select, apply, and hot-reload theme presets in 1 click.
 */

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import { Extension, gettext as _ } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as QuickSettings from 'resource:///org/gnome/shell/ui/quickSettings.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

/**
 * Scrollable popup menu section to accommodate 20+ theme presets cleanly.
 */
class PopupScrollMenuSection extends PopupMenu.PopupMenuSection {
    constructor() {
        super();
        this.actor = new St.ScrollView({
            style_class: 'theme-studio-scroll-section',
            hscrollbar_policy: St.PolicyType.NEVER,
            vscrollbar_policy: St.PolicyType.AUTOMATIC,
            overlay_scrollbars: true,
            child: this.box,
        });
        this.actor._delegate = this;
        this.actor.clip_to_allocation = true;
    }
}

/**
 * Main Quick Settings Toggle Item
 */
const ThemeStudioToggle = GObject.registerClass(
class ThemeStudioToggle extends QuickSettings.QuickMenuToggle {
    _init(extension) {
        super._init({
            title: 'Theme Studio',
            subtitle: _('Cargando...'),
            iconName: 'preferences-desktop-theme-symbolic',
            toggleMode: false,
            menuButtonAccessibleName: _('Abrir catálogo de temas'),
        });

        this._extension = extension;
        this._isApplying = false;
        this._presets = {};
        this._menuItems = new Map();
        this._activePresetName = null;

        // Submenu header
        this.menu.setHeader('preferences-desktop-theme-symbolic', 'GNOME Theme Studio');

        // Scrollable preset list section
        this._presetSection = new PopupScrollMenuSection();
        this.menu.addMenuItem(this._presetSection);

        // Separator between presets and quick actions
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Action: Open Web Studio
        const webStudioItem = new PopupMenu.PopupImageMenuItem(
            _('Abrir Web Studio (localhost:5000)'),
            'applications-internet-symbolic'
        );
        webStudioItem.connect('activate', () => {
            this._openWebStudio();
        });
        this.menu.addMenuItem(webStudioItem);

        // Action: Reset GNOME desktop to Adwaita
        const resetItem = new PopupMenu.PopupImageMenuItem(
            _('Restablecer escritorio (Adwaita)'),
            'edit-undo-symbolic'
        );
        resetItem.connect('activate', () => {
            this._resetToDefault();
        });
        this.menu.addMenuItem(resetItem);

        // Clicking the main toggle body opens the presets menu
        this.connect('clicked', () => {
            this.menu.open();
        });

        // Re-read presets whenever the menu is opened (live-sync with Web Studio / CLI)
        this.menu.connectObject('open-state-changed', (menu, isOpen) => {
            if (isOpen) {
                this._loadPresets();
            }
        }, this);

        // Watch GNOME settings for GTK theme changes (sync from external apps/CLI)
        this._interfaceSettings = new Gio.Settings({
            schema_id: 'org.gnome.desktop.interface',
        });
        this._settingsChangedId = this._interfaceSettings.connect(
            'changed::gtk-theme',
            () => this._syncActiveTheme()
        );

        // Initial load and sync
        this._loadPresets();
        this._syncActiveTheme();
    }

    /**
     * Resolves the root project directory containing themer-cli.py and presets.json.
     */
    _findProjectDir() {
        // 1. Explicit environment variable
        const envDir = GLib.getenv('GNOME_THEME_STUDIO_DIR');
        if (envDir && GLib.file_test(envDir, GLib.FileTest.IS_DIR)) {
            return envDir;
        }

        // 2. Relative to extension location (if repo cloned or extension inside repo)
        const extPath = this._extension.path;
        if (extPath) {
            const parentDir = GLib.path_get_dirname(extPath);
            const parentCli = GLib.build_filenamev([parentDir, 'themer-cli.py']);
            if (GLib.file_test(parentCli, GLib.FileTest.EXISTS)) {
                return parentDir;
            }

            // If extension was symlinked to ~/.local/share/gnome-shell/extensions/
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

        // 3. Common clone path: ~/gnome-theme-studio
        const homeDir = GLib.get_home_dir();
        const candidateHome = GLib.build_filenamev([homeDir, 'gnome-theme-studio']);
        if (GLib.file_test(GLib.build_filenamev([candidateHome, 'themer-cli.py']), GLib.FileTest.EXISTS)) {
            return candidateHome;
        }

        // 4. Default fallback path
        return '/home/angelaguayo/gnome-theme-studio';
    }

    /**
     * Finds the best python binary to execute themer-cli.py (prefers project venv if present).
     */
    _getPythonBin(projectDir) {
        const venvPython = GLib.build_filenamev([projectDir, 'venv', 'bin', 'python3']);
        if (GLib.file_test(venvPython, GLib.FileTest.IS_EXECUTABLE)) {
            return venvPython;
        }
        return 'python3';
    }

    /**
     * Reads presets.json and populates the menu.
     */
    _loadPresets() {
        const projectDir = this._findProjectDir();
        const presetsPath = GLib.build_filenamev([projectDir, 'presets.json']);

        try {
            const [ok, contents] = GLib.file_get_contents(presetsPath);
            if (!ok) {
                console.error(`[ThemeStudio] No se pudo leer el archivo: ${presetsPath}`);
                return;
            }

            const data = JSON.parse(new TextDecoder().decode(contents));
            this._presets = data;
            this._rebuildPresetsMenu();
            this._syncActiveTheme();
        } catch (err) {
            console.error(`[ThemeStudio] Error al parsear presets.json: ${err.message}`);
        }
    }

    /**
     * Clears and rebuilds the preset list inside the scrollable section.
     */
    _rebuildPresetsMenu() {
        this._presetSection.removeAll();
        this._menuItems.clear();

        const presetNames = Object.keys(this._presets);

        for (const name of presetNames) {
            const cfg = this._presets[name] || {};
            const isDark = (cfg.color_scheme === 'dark');
            const iconName = isDark ? 'weather-clear-night-symbolic' : 'weather-clear-symbolic';

            const item = new PopupMenu.PopupImageMenuItem(name, iconName, {
                style_class: 'theme-studio-preset-item',
            });

            item.connect('activate', () => {
                this._applyPreset(name);
            });

            this._menuItems.set(name, item);
            this._presetSection.addMenuItem(item);
        }

        this._updateOrnaments();
    }

    /**
     * Synchronizes the currently active theme with GNOME settings and updates checkmarks.
     */
    _syncActiveTheme() {
        if (!this._interfaceSettings) return;

        const currentGtk = this._interfaceSettings.get_string('gtk-theme') || '';
        const normCurrent = currentGtk.toLowerCase().replace(/[-_ ]/g, '');

        let matched = null;
        for (const name of Object.keys(this._presets)) {
            const normName = name.toLowerCase().replace(/[-_ ]/g, '');
            if (normName === normCurrent || currentGtk.toLowerCase().includes(normName)) {
                matched = name;
                break;
            }
        }

        if (matched) {
            this._activePresetName = matched;
            this.subtitle = matched;
        } else if (currentGtk) {
            this._activePresetName = currentGtk;
            this.subtitle = currentGtk;
        } else {
            this.subtitle = 'Adwaita';
        }

        this._updateOrnaments();
    }

    /**
     * Sets a checkmark on the active preset item.
     */
    _updateOrnaments() {
        for (const [name, item] of this._menuItems) {
            const isCurrent = (name === this._activePresetName);
            item.setOrnament(isCurrent ? PopupMenu.Ornament.CHECK : PopupMenu.Ornament.NONE);
        }
    }

    /**
     * Asynchronously compiles, applies and hot-reloads the selected theme via themer-cli.py.
     */
    _applyPreset(presetName) {
        if (this._isApplying) return;

        this._isApplying = true;
        const prevSubtitle = this.subtitle;
        this.subtitle = `${_('Aplicando')} ${presetName}...`;

        const projectDir = this._findProjectDir();
        const pythonBin = this._getPythonBin(projectDir);
        const cliPath = GLib.build_filenamev([projectDir, 'themer-cli.py']);

        try {
            const proc = new Gio.Subprocess({
                argv: [pythonBin, cliPath, '--preset', presetName, '--apply'],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });

            proc.init(null);
            proc.communicate_utf8_async(null, null, (source, res) => {
                this._isApplying = false;
                try {
                    const [ok, stdout, stderr] = source.communicate_utf8_finish(res);
                    const exitStatus = source.get_exit_status();

                    if (exitStatus === 0) {
                        this._activePresetName = presetName;
                        this.subtitle = presetName;
                        this._updateOrnaments();
                        Main.notify('GNOME Theme Studio', `${_('Tema aplicado')}: ${presetName}`);
                    } else {
                        console.error(`[ThemeStudio] Error al aplicar (${exitStatus}): ${stderr || stdout}`);
                        this.subtitle = _('Error al aplicar');
                        Main.notifyError('GNOME Theme Studio', `${_('Error al aplicar')}: ${presetName}`);
                    }
                } catch (finishErr) {
                    console.error(`[ThemeStudio] Error en Subprocess finish: ${finishErr.message}`);
                    this.subtitle = prevSubtitle;
                }
            });
        } catch (procErr) {
            this._isApplying = false;
            console.error(`[ThemeStudio] No se pudo lanzar el subproceso: ${procErr.message}`);
            this.subtitle = prevSubtitle;
        }
    }

    /**
     * Asynchronously resets GNOME Desktop and clears overrides.
     */
    _resetToDefault() {
        if (this._isApplying) return;

        this._isApplying = true;
        this.subtitle = _('Restableciendo...');

        const projectDir = this._findProjectDir();
        const pythonBin = this._getPythonBin(projectDir);
        const cliPath = GLib.build_filenamev([projectDir, 'themer-cli.py']);

        try {
            const proc = new Gio.Subprocess({
                argv: [pythonBin, cliPath, '--reset'],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });

            proc.init(null);
            proc.communicate_utf8_async(null, null, (source, res) => {
                this._isApplying = false;
                try {
                    source.communicate_utf8_finish(res);
                    if (source.get_exit_status() === 0) {
                        this._activePresetName = null;
                        this.subtitle = 'Adwaita';
                        this._updateOrnaments();
                        Main.notify('GNOME Theme Studio', _('Escritorio restablecido a valores de fábrica.'));
                    } else {
                        this.subtitle = _('Error al restablecer');
                    }
                } catch (finishErr) {
                    console.error(`[ThemeStudio] Error en reset finish: ${finishErr.message}`);
                    this.subtitle = 'Adwaita';
                }
            });
        } catch (err) {
            this._isApplying = false;
            console.error(`[ThemeStudio] Error al ejecutar reset: ${err.message}`);
        }
    }

    /**
     * Launches Web Studio in user's default browser.
     */
    _openWebStudio() {
        try {
            Gio.AppInfo.launch_default_for_uri('http://127.0.0.1:5000', null);
        } catch (err) {
            console.error(`[ThemeStudio] No se pudo abrir Web Studio: ${err.message}`);
        }
    }

    /**
     * Cleanup on destroy.
     */
    destroy() {
        if (this._settingsChangedId && this._interfaceSettings) {
            this._interfaceSettings.disconnect(this._settingsChangedId);
            this._settingsChangedId = null;
        }
        this._interfaceSettings = null;
        this._menuItems.clear();
        super.destroy();
    }
});

/**
 * Main Extension Class (GNOME Shell 45+ ESM)
 */
export default class ThemeStudioExtension extends Extension {
    enable() {
        this._indicator = new QuickSettings.SystemIndicator();
        this._toggle = new ThemeStudioToggle(this);

        this._indicator.quickSettingsItems.push(this._toggle);

        // Add to panel statusArea QuickSettings (column span 1 = half width / 2 = full width)
        Main.panel.statusArea.quickSettings.addExternalIndicator(this._indicator, 1);
    }

    disable() {
        if (this._toggle) {
            this._toggle.destroy();
            this._toggle = null;
        }

        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
