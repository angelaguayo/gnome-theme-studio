"""
GNOME Theme Studio - Flask Application Server
Visual Real-Time Editor, SCSS Compiler, and 1-Click Installer for Linux GNOME Desktop.
"""

import os
from flask import Flask, render_template, request, jsonify, send_file
import compiler
import installer
import presets
import exporter

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    """Renders the main GNOME Theme Studio web interface."""
    return render_template("index.html")


@app.route("/api/system-status", methods=["GET"])
def system_status():
    """Returns current active GNOME desktop theme settings."""
    try:
        status = installer.get_current_theme_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Returns all available theme presets."""
    try:
        data = presets.load_presets()
        return jsonify({"success": True, "presets": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/presets", methods=["POST"])
def save_user_preset():
    """Saves or updates a preset."""
    payload = request.get_json() or {}
    name = payload.get("name")
    config = payload.get("config")

    if not name or not config:
        return jsonify({"success": False, "error": "Preset name and configuration are required."}), 400

    ok = presets.save_preset(name, config)
    if ok:
        return jsonify({"success": True, "message": f"Preset '{name}' saved successfully."})
    return jsonify({"success": False, "error": "Failed to save preset."}), 500


@app.route("/api/presets/<name>", methods=["DELETE"])
def delete_user_preset(name):
    """Deletes a saved preset."""
    ok = presets.delete_preset(name)
    if ok:
        return jsonify({"success": True, "message": f"Preset '{name}' deleted."})
    return jsonify({"success": False, "error": f"Preset '{name}' not found or cannot be deleted."}), 404


@app.route("/api/compile", methods=["POST"])
def compile_endpoint():
    """Compiles the theme with current user parameters."""
    config = request.get_json() or {}
    try:
        result = compiler.compile_theme(config)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/apply", methods=["POST"])
def apply_endpoint():
    """
    1-Click: Compiles theme, installs to ~/.themes, applies to Libadwaita & GNOME Shell,
    generates matching wallpaper, and performs the live hot-reload trick.
    """
    data = request.get_json() or {}
    config = data.get("config", {})
    apply_gtk4 = data.get("apply_gtk4", True)
    apply_wallpaper = data.get("apply_wallpaper", True)
    apply_firefox = data.get("apply_firefox", True)

    try:
        # 1. Compile
        compile_res = compiler.compile_theme(config)
        if not compile_res.get("success"):
            return jsonify(compile_res), 400

        theme_name = compile_res["theme_name"]
        compiled_dir = compile_res["output_dir"]

        # 2. Install, set wallpaper, firefox and live reload
        install_res = installer.install_and_apply_theme(
            theme_name,
            compiled_dir,
            config=config,
            apply_gtk4=apply_gtk4,
            apply_wallpaper=apply_wallpaper,
            apply_firefox=apply_firefox
        )

        combined_logs = compile_res.get("logs", []) + install_res.get("logs", [])

        return jsonify({
            "success": True,
            "theme_name": theme_name,
            "duration_ms": compile_res.get("duration_ms", 0),
            "logs": combined_logs,
            "message": f"¡Tema '{theme_name}' compilado, instalado y aplicado con éxito!"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export", methods=["POST"])
def export_endpoint():
    """Compiles theme and returns downloadable .zip file."""
    config = request.get_json() or {}
    try:
        compile_res = compiler.compile_theme(config)
        if not compile_res.get("success"):
            return jsonify(compile_res), 400

        theme_name = compile_res["theme_name"]
        compiled_dir = compile_res["output_dir"]

        zip_path = exporter.create_theme_zip(theme_name, compiled_dir)
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"{theme_name}.zip",
            mimetype="application/zip"
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset-defaults", methods=["POST"])
def reset_defaults_endpoint():
    """
    Restores GNOME desktop to factory default settings:
    Stock GTK theme (Adwaita), default color scheme, accent color, button layout,
    default GNOME Shell theme, system wallpaper, and cleans custom GTK4 config.
    """
    try:
        result = installer.reset_gnome_defaults()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting GNOME Theme Studio on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
