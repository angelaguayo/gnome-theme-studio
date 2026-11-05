/**
 * GNOME Theme Studio - Frontend Controller
 * Real-time 60fps reactive mockup synchronization, presets manager, dynamic wallpaper & 1-click installer.
 */

// Global State
let currentConfig = {};
let availablePresets = {};
let selectedPresetKey = "Everforest Dark";

// DOM Elements
const mockupViewport = document.getElementById("mockup-viewport");
const presetSelector = document.getElementById("preset-selector");
const inputThemeName = document.getElementById("input-theme-name");
const currentSystemThemeEl = document.getElementById("current-system-theme");
const reloadPulseEl = document.getElementById("reload-pulse");
const toggleApplyGTK4 = document.getElementById("toggle-apply-gtk4");
const toggleApplyWallpaper = document.getElementById("toggle-apply-wallpaper");
const toggleApplyFirefox = document.getElementById("toggle-apply-firefox");

// Window Controls Elements
const mockupLeftControls = document.getElementById("mockup-left-controls");
const mockupRightControls = document.getElementById("mockup-right-controls");
const btnLayoutLeft = document.getElementById("btn-layout-left");
const btnLayoutRight = document.getElementById("btn-layout-right");
const selectColorScheme = document.getElementById("select-color-scheme");

// Modals & Drawers
const modalSavePreset = document.getElementById("modal-save-preset");
const inputPresetName = document.getElementById("input-preset-name");
const logsDrawer = document.getElementById("logs-drawer");
const logsContent = document.getElementById("logs-content");
const quickSettingsMenu = document.getElementById("mockup-quick-settings-menu");

// Action Buttons
const btnApplyTheme = document.getElementById("btn-apply-theme");
const btnApplyText = document.getElementById("btn-apply-text");
const btnApplyIcon = document.getElementById("btn-apply-icon");
const btnApplySpinner = document.getElementById("btn-apply-spinner");
const btnExportZip = document.getElementById("btn-export-zip");
const btnResetDefaultsOpen = document.getElementById("btn-reset-defaults-open");
const modalResetDefaults = document.getElementById("modal-reset-defaults");
const btnCloseResetModal = document.getElementById("btn-close-reset-modal");
const btnCancelResetModal = document.getElementById("btn-cancel-reset-modal");
const btnConfirmResetDefaults = document.getElementById("btn-confirm-reset-defaults");
const resetSpinner = document.getElementById("reset-spinner");
const resetBtnText = document.getElementById("reset-btn-text");
const btnSavePresetModal = document.getElementById("btn-save-preset-modal");
const btnConfirmSavePreset = document.getElementById("btn-confirm-save-preset");
const btnCloseSaveModal = document.getElementById("btn-close-save-modal");
const btnCancelSaveModal = document.getElementById("btn-cancel-save-modal");
const btnToggleLogs = document.getElementById("btn-toggle-logs");
const btnCloseLogs = document.getElementById("btn-close-logs");
const btnClearLogs = document.getElementById("btn-clear-logs");
const btnResetPreset = document.getElementById("btn-reset-preset");
const btnToggleQuickSettings = document.getElementById("btn-toggle-quick-settings");
const trayQuickTrigger = document.getElementById("tray-quick-trigger");

// CSS Variable Mapping
const CSS_VAR_MAP = {
  accent_color: "--accent-color",
  accent_secondary: "--accent-secondary",
  window_bg: "--window-bg",
  sidebar_bg: "--sidebar-bg",
  surface_elevated: "--surface-elevated",
  headerbar_bg: "--headerbar-bg",
  text_primary: "--text-primary",
  text_muted: "--text-muted",
  border_color: "--border-color",
  border_active: "--border-active",
  destructive_color: "--destructive-color",
  warning_color: "--warning-color",
  info_color: "--info-color",
  purple_color: "--purple-color",
  orange_color: "--orange-color",
  window_radius: "--window-radius",
  button_radius: "--button-radius",
  border_width: "--border-width",
  panel_opacity: "--panel-opacity",
  quick_settings_radius: "--quick-settings-radius",
  window_controls_size: "--window-controls-size",
};


// 1. INITIALIZATION
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupInputs();
  setupEventListeners();
  loadSystemStatus();
  loadPresets();
});


// 2. TAB SYSTEM
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");

      tabButtons.forEach(b => {
        b.classList.remove("border-[#a7c080]", "text-[#a7c080]");
        b.classList.add("border-transparent", "text-[#859289]");
      });

      btn.classList.add("border-[#a7c080]", "text-[#a7c080]");
      btn.classList.remove("border-transparent", "text-[#859289]");

      tabPanes.forEach(pane => {
        if (pane.id === targetTab) {
          pane.classList.remove("hidden");
        } else {
          pane.classList.add("hidden");
        }
      });
    });
  });
}


// 3. INPUT SYNCHRONIZATION & 60FPS MOCKUP
function setupInputs() {
  // Color Pickers
  document.querySelectorAll('input[type="color"]').forEach(colorInput => {
    const varName = colorInput.getAttribute("data-var");
    const hexInput = document.querySelector(`.hex-input[data-var="${varName}"]`);

    colorInput.addEventListener("input", (e) => {
      const val = e.target.value.toLowerCase();
      if (hexInput) hexInput.value = val.toUpperCase();
      updateVariable(varName, val);
      updateClientWallpaper();
    });
  });

  // Hex Text Inputs
  document.querySelectorAll(".hex-input").forEach(hexInput => {
    const varName = hexInput.getAttribute("data-var");
    const colorInput = document.querySelector(`input[type="color"][data-var="${varName}"]`);

    hexInput.addEventListener("input", (e) => {
      let val = e.target.value.trim();
      if (!val.startsWith("#")) val = "#" + val;
      if (/^#[0-9a-fA-F]{6}$/i.test(val)) {
        if (colorInput) colorInput.value = val;
        updateVariable(varName, val);
        updateClientWallpaper();
      }
    });
  });

  // Sliders
  document.querySelectorAll('input[type="range"]').forEach(slider => {
    const varName = slider.getAttribute("data-var");
    slider.addEventListener("input", (e) => {
      const val = e.target.value;
      updateVariable(varName, val);
      updateBadge(varName, val);
    });
  });

  // Window Controls Style buttons
  document.querySelectorAll(".btn-ctrl-style").forEach(btn => {
    btn.addEventListener("click", () => {
      const style = btn.getAttribute("data-style");
      setWindowControlsStyle(style);
    });
  });

  // Button layout (left vs right)
  btnLayoutLeft.addEventListener("click", () => setButtonLayout("left"));
  btnLayoutRight.addEventListener("click", () => setButtonLayout("right"));

  // Wallpaper style radio buttons
  document.querySelectorAll('input[name="wallpaper_style"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      currentConfig.wallpaper_style = e.target.value;
      updateClientWallpaper();
    });
  });

  // Color scheme selector
  selectColorScheme.addEventListener("change", (e) => {
    currentConfig.color_scheme = e.target.value;
  });

  // Theme name
  inputThemeName.addEventListener("input", (e) => {
    currentConfig.theme_name = e.target.value.trim();
  });
}

function updateBadge(varName, val) {
  const badge = document.getElementById(`badge-${varName.replace(/_/g, "-")}`);
  if (!badge) return;

  if (varName === "panel_opacity") {
    badge.textContent = `${Math.round(parseFloat(val) * 100)}%`;
  } else {
    badge.textContent = `${val}px`;
  }
}

function updateVariable(varName, val) {
  currentConfig[varName] = val;
  const cssVar = CSS_VAR_MAP[varName];
  if (!cssVar) return;

  let cssValue = val;
  if (varName.includes("radius") || varName === "border_width" || varName === "window_controls_size") {
    cssValue = `${val}px`;
  }

  mockupViewport.style.setProperty(cssVar, cssValue);
}

function setWindowControlsStyle(style) {
  currentConfig.window_controls_style = style;

  // Update button active state
  document.querySelectorAll(".btn-ctrl-style").forEach(btn => {
    if (btn.getAttribute("data-style") === style) {
      btn.classList.add("border-[#a7c080]", "bg-[#252c31]");
      btn.classList.remove("border-[#3d484d]", "bg-[#1a1f23]");
    } else {
      btn.classList.remove("border-[#a7c080]", "bg-[#252c31]");
      btn.classList.add("border-[#3d484d]", "bg-[#1a1f23]");
    }
  });

  // Update Mockup controls container class
  const ctrlContainer = document.querySelector(".mockup-window-controls");
  if (ctrlContainer) {
    ctrlContainer.className = `mockup-window-controls mockup-ctrl-style-${style}`;
  }
}

function setButtonLayout(layout) {
  currentConfig.button_layout = layout;
  const ctrlContainer = document.querySelector(".mockup-window-controls");

  if (layout === "left") {
    btnLayoutLeft.classList.add("bg-[#2d353b]", "text-[#a7c080]");
    btnLayoutLeft.classList.remove("text-[#859289]");
    btnLayoutRight.classList.remove("bg-[#2d353b]", "text-[#a7c080]");
    btnLayoutRight.classList.add("text-[#859289]");

    // Move to left
    if (ctrlContainer && mockupLeftControls) {
      mockupLeftControls.appendChild(ctrlContainer);
    }
  } else {
    btnLayoutRight.classList.add("bg-[#2d353b]", "text-[#a7c080]");
    btnLayoutRight.classList.remove("text-[#859289]");
    btnLayoutLeft.classList.remove("bg-[#2d353b]", "text-[#a7c080]");
    btnLayoutLeft.classList.add("text-[#859289]");

    // Move to right
    if (ctrlContainer && mockupRightControls) {
      mockupRightControls.appendChild(ctrlContainer);
    }
  }
}


// 4. CLIENT-SIDE 60FPS VECTOR WALLPAPER RENDERER
function updateClientWallpaper() {
  const bg = currentConfig.window_bg || "#2d353b";
  const bgDim = currentConfig.headerbar_bg || "#232a2e";
  const accent = currentConfig.accent_color || "#a7c080";
  const secondary = currentConfig.accent_secondary || "#83c092";
  const surface = currentConfig.surface_elevated || "#343f44";
  const cardBg = currentConfig.sidebar_bg || "#272e33";
  const style = currentConfig.wallpaper_style || "abstract_waves";

  let svg = "";
  if (style === "aurora") {
    svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
      <defs>
        <radialGradient id="aurora1" cx="30%" cy="20%" r="65%">
          <stop offset="0%" stop-color="${accent}" stop-opacity="0.45"/>
          <stop offset="60%" stop-color="${secondary}" stop-opacity="0.15"/>
          <stop offset="100%" stop-color="${bg}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="aurora2" cx="80%" cy="85%" r="70%">
          <stop offset="0%" stop-color="${secondary}" stop-opacity="0.4"/>
          <stop offset="50%" stop-color="${accent}" stop-opacity="0.15"/>
          <stop offset="100%" stop-color="${bgDim}" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="1600" height="900" fill="${bgDim}"/>
      <rect width="1600" height="900" fill="${bg}" opacity="0.85"/>
      <rect width="1600" height="900" fill="url(#aurora1)"/>
      <rect width="1600" height="900" fill="url(#aurora2)"/>
    </svg>`;
  } else if (style === "geometric") {
    svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
      <defs>
        <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${bgDim}"/>
          <stop offset="100%" stop-color="${bg}"/>
        </linearGradient>
        <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${accent}" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="${secondary}" stop-opacity="0.1"/>
        </linearGradient>
      </defs>
      <rect width="1600" height="900" fill="url(#g1)"/>
      <polygon points="0,0 1000,0 600,900 0,900" fill="${surface}" opacity="0.35"/>
      <polygon points="400,0 1600,0 1600,680 700,900" fill="url(#g2)"/>
      <polygon points="800,0 1360,0 960,450" fill="${accent}" opacity="0.25"/>
    </svg>`;
  } else {
    // Abstract waves
    svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
      <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${bgDim}"/>
          <stop offset="50%" stop-color="${bg}"/>
          <stop offset="100%" stop-color="${cardBg}"/>
        </linearGradient>
        <linearGradient id="wave1Grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${accent}" stop-opacity="0.55"/>
          <stop offset="100%" stop-color="${secondary}" stop-opacity="0.15"/>
        </linearGradient>
        <linearGradient id="wave2Grad" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="${secondary}" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="${accent}" stop-opacity="0.1"/>
        </linearGradient>
        <linearGradient id="wave3Grad" x1="0%" y1="50%" x2="100%" y2="50%">
          <stop offset="0%" stop-color="${surface}" stop-opacity="0.7"/>
          <stop offset="100%" stop-color="${bgDim}" stop-opacity="0.9"/>
        </linearGradient>
      </defs>
      <rect width="1600" height="900" fill="url(#bgGrad)"/>
      <circle cx="1040" cy="315" r="450" fill="${accent}" opacity="0.12"/>
      <path d="M 0,585 Q 560,360 1040,675 T 1600,495 L 1600,900 L 0,900 Z" fill="url(#wave3Grad)"/>
      <path d="M 0,720 Q 400,495 880,738 T 1600,612 L 1600,900 L 0,900 Z" fill="url(#wave2Grad)"/>
      <path d="M 0,810 Q 640,648 1200,792 T 1600,738 L 1600,900 L 0,900 Z" fill="url(#wave1Grad)"/>
    </svg>`;
  }

  const encodedSvg = encodeURIComponent(svg);
  mockupViewport.style.backgroundImage = `url("data:image/svg+xml;utf8,${encodedSvg}")`;
}


// 5. PRESETS MANAGER
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    const data = await res.json();
    if (data.success && data.presets) {
      availablePresets = data.presets;
      renderPresetDropdown();
      applyPreset("Everforest Dark");
    }
  } catch (err) {
    showToast("Error cargando presets: " + err.message, "error");
  }
}

function renderPresetDropdown() {
  presetSelector.innerHTML = "";
  Object.keys(availablePresets).forEach(name => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    presetSelector.appendChild(opt);
  });
  presetSelector.value = selectedPresetKey;
}

function applyPreset(name) {
  const preset = availablePresets[name];
  if (!preset) return;

  selectedPresetKey = name;
  presetSelector.value = name;
  currentConfig = JSON.parse(JSON.stringify(preset));

  if (preset.theme_name) {
    inputThemeName.value = preset.theme_name;
  }

  // Populate color inputs and apply CSS variables
  Object.keys(preset).forEach(varName => {
    const val = preset[varName];
    const colorInput = document.querySelector(`input[type="color"][data-var="${varName}"]`);
    const hexInput = document.querySelector(`.hex-input[data-var="${varName}"]`);
    const slider = document.querySelector(`input[type="range"][data-var="${varName}"]`);

    if (colorInput) colorInput.value = val;
    if (hexInput) hexInput.value = val.toUpperCase();
    if (slider) {
      slider.value = val;
      updateBadge(varName, val);
    }

    updateVariable(varName, val);
  });

  // Controls style & layout
  setWindowControlsStyle(preset.window_controls_style || "traffic-hover");
  setButtonLayout(preset.button_layout || "right");

  // Wallpaper style radio
  const wpStyle = preset.wallpaper_style || "abstract_waves";
  const radio = document.querySelector(`input[name="wallpaper_style"][value="${wpStyle}"]`);
  if (radio) radio.checked = true;

  // Color scheme
  selectColorScheme.value = preset.color_scheme || "dark";

  updateClientWallpaper();
  appendLog(`Preset cargado: '${name}'`);
}


// 6. EVENT LISTENERS
function setupEventListeners() {
  presetSelector.addEventListener("change", (e) => applyPreset(e.target.value));

  btnResetPreset.addEventListener("click", () => {
    applyPreset(selectedPresetKey);
    showToast(`Valores reiniciados al preset '${selectedPresetKey}'`, "info");
  });

  // Save preset modal
  btnSavePresetModal.addEventListener("click", () => {
    inputPresetName.value = `${inputThemeName.value} Custom`;
    modalSavePreset.classList.remove("hidden");
    inputPresetName.focus();
  });

  btnCloseSaveModal.addEventListener("click", () => modalSavePreset.classList.add("hidden"));
  btnCancelSaveModal.addEventListener("click", () => modalSavePreset.classList.add("hidden"));

  btnConfirmSavePreset.addEventListener("click", async () => {
    const name = inputPresetName.value.trim();
    if (!name) return;

    try {
      const res = await fetch("/api/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, config: currentConfig })
      });
      const data = await res.json();
      if (data.success) {
        availablePresets[name] = JSON.parse(JSON.stringify(currentConfig));
        renderPresetDropdown();
        presetSelector.value = name;
        modalSavePreset.classList.add("hidden");
        showToast(`Preset '${name}' guardado correctamente`, "success");
        appendLog(`Nuevo preset guardado: '${name}'`);
      } else {
        showToast(data.error || "Error guardando preset", "error");
      }
    } catch (err) {
      showToast("Error de red: " + err.message, "error");
    }
  });

  // Quick settings toggle in mockup
  const toggleQuickSettings = () => {
    quickSettingsMenu.classList.toggle("hidden");
  };
  btnToggleQuickSettings.addEventListener("click", toggleQuickSettings);
  trayQuickTrigger.addEventListener("click", toggleQuickSettings);

  // Logs drawer
  btnToggleLogs.addEventListener("click", () => logsDrawer.classList.toggle("hidden"));
  btnCloseLogs.addEventListener("click", () => logsDrawer.classList.add("hidden"));
  btnClearLogs.addEventListener("click", () => {
    logsContent.innerHTML = '<div class="text-[#859289]">// Consola limpiada.</div>';
  });

  // Reset Defaults Modal & Action
  btnResetDefaultsOpen.addEventListener("click", () => {
    modalResetDefaults.classList.remove("hidden");
  });
  btnCloseResetModal.addEventListener("click", () => {
    modalResetDefaults.classList.add("hidden");
  });
  btnCancelResetModal.addEventListener("click", () => {
    modalResetDefaults.classList.add("hidden");
  });
  btnConfirmResetDefaults.addEventListener("click", handleResetDefaults);

  btnExportZip.addEventListener("click", handleExportZip);
  btnApplyTheme.addEventListener("click", handleApplyTheme);
}


// 6.5 RESET GNOME DEFAULTS
async function handleResetDefaults() {
  btnConfirmResetDefaults.disabled = true;
  resetSpinner.classList.remove("hidden");
  resetBtnText.textContent = "Restableciendo...";
  reloadPulseEl.classList.remove("hidden");

  appendLog("--- INICIANDO RESTABLECIMIENTO A VALORES POR DEFECTO DE GNOME ---");

  try {
    const res = await fetch("/api/reset-defaults", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });

    const data = await res.json();

    if (data.success) {
      if (data.logs) {
        data.logs.forEach(l => appendLog(l));
      }
      showToast(data.message || "GNOME ha sido restablecido a valores por defecto.", "success");
      modalResetDefaults.classList.add("hidden");
      await loadSystemStatus();

      // If Adwaita preset exists in presets dropdown, load it into mockup
      const adwaitaKey = availablePresets["Adwaita Dark (GNOME Default)"] 
        ? "Adwaita Dark (GNOME Default)" 
        : Object.keys(availablePresets)[0];

      if (adwaitaKey) {
        applyPreset(adwaitaKey);
        presetSelector.value = adwaitaKey;
      }
    } else {
      showToast(data.error || "Error al restablecer valores por defecto", "error");
      if (data.logs) {
        data.logs.forEach(l => appendLog(l, "error"));
      }
      logsDrawer.classList.remove("hidden");
    }
  } catch (err) {
    showToast("Error de conexión: " + err.message, "error");
  } finally {
    btnConfirmResetDefaults.disabled = false;
    resetSpinner.classList.add("hidden");
    resetBtnText.textContent = "Sí, Restablecer Todo";
    setTimeout(() => reloadPulseEl.classList.add("hidden"), 1500);
  }
}



// 7. 1-CLICK COMPILE & APPLY
async function handleApplyTheme() {
  btnApplyTheme.disabled = true;
  btnApplyText.textContent = "Compilando SASS...";
  btnApplyIcon.classList.add("hidden");
  btnApplySpinner.classList.remove("hidden");
  reloadPulseEl.classList.remove("hidden");

  appendLog(`--- INICIANDO COMPILACIÓN E INSTALACIÓN 1-CLICK ---`);
  currentConfig.theme_name = inputThemeName.value.trim();

  try {
    const res = await fetch("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        config: currentConfig,
        apply_gtk4: toggleApplyGTK4.checked,
        apply_wallpaper: toggleApplyWallpaper.checked,
        apply_firefox: toggleApplyFirefox ? toggleApplyFirefox.checked : true
      })
    });

    const data = await res.json();

    if (data.success) {
      if (data.logs) {
        data.logs.forEach(l => appendLog(l));
      }
      showToast(data.message || `¡Tema '${data.theme_name}' aplicado con éxito!`, "success");
      loadSystemStatus();
    } else {
      if (data.logs) data.logs.forEach(l => appendLog(l, "error"));
      showToast(data.error || "Error durante la compilación", "error");
      logsDrawer.classList.remove("hidden");
    }

  } catch (err) {
    showToast("Error de conexión con el backend: " + err.message, "error");
  } finally {
    btnApplyTheme.disabled = false;
    btnApplyText.textContent = "Compilar, Instalar y Aplicar";
    btnApplyIcon.classList.remove("hidden");
    btnApplySpinner.classList.add("hidden");
    setTimeout(() => reloadPulseEl.classList.add("hidden"), 1500);
  }
}


// 8. EXPORT ZIP
async function handleExportZip() {
  btnExportZip.disabled = true;
  btnExportZip.innerHTML = `
    <svg class="w-4 h-4 animate-spin text-[#7fbbb3]" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
    <span>Generando .zip...</span>
  `;

  currentConfig.theme_name = inputThemeName.value.trim();

  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentConfig)
    });

    if (!res.ok) throw new Error("Error exportando tema.");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentConfig.theme_name || "Theme"}.zip`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    showToast(`Archivo ${a.download} descargado exitosamente.`, "success");
    appendLog(`Tema empaquetado y exportado: ${a.download}`);

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btnExportZip.disabled = false;
    btnExportZip.innerHTML = `
      <svg class="w-4 h-4 text-[#7fbbb3]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
      <span>Descargar (.zip)</span>
    `;
  }
}


// 9. SYSTEM STATUS & LIVE BADGE
async function loadSystemStatus() {
  try {
    const res = await fetch("/api/system-status");
    const data = await res.json();
    if (data.success && data.status) {
      const s = data.status;
      currentSystemThemeEl.textContent = s.gtk_theme || "Adwaita";
    }
  } catch (e) {
    currentSystemThemeEl.textContent = "Desconocido";
  }
}


// 10. LOGS & TOASTS
function appendLog(message, type = "info") {
  const time = new Date().toLocaleTimeString();
  const line = document.createElement("div");
  line.className = type === "error" ? "text-red-400 font-bold" : "text-[#a7c080]";
  line.textContent = `[${time}] ${message}`;
  logsContent.appendChild(line);
  logsContent.scrollTop = logsContent.scrollHeight;
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl text-xs font-semibold animate-slide-up border transition-all duration-300 max-w-sm";

  if (type === "success") {
    toast.className += " bg-[#1c2e22] text-[#a7c080] border-[#a7c080]/30 shadow-[#a7c080]/10";
    toast.innerHTML = `
      <svg class="w-4 h-4 text-[#a7c080] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
      <span>${message}</span>
    `;
  } else if (type === "error") {
    toast.className += " bg-[#2e1c1c] text-[#e67e80] border-[#e67e80]/30 shadow-[#e67e80]/10";
    toast.innerHTML = `
      <svg class="w-4 h-4 text-[#e67e80] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      <span>${message}</span>
    `;
  } else {
    toast.className += " bg-[#21272c] text-[#d3c6aa] border-[#3d484d]";
    toast.innerHTML = `
      <svg class="w-4 h-4 text-[#7fbbb3] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span>${message}</span>
    `;
  }

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
