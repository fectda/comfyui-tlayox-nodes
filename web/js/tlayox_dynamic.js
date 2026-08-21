const { app } = window.comfyAPI.app;

const LABEL_MAP = {
    "Visual_Prompt": "Visual Prompt",
    "Atmosphere_Otra": "Atmosphere",
    "Atmosphere_Tlayox": "Atmosphere",
    "Atmosphere_Altepetl": "Atmosphere",
    "Base_Format": "Base Format",
    "Type_Photography": "Type",
};

const COMPOSITION_POSITIONS = [
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
];

const COMPOSITION_LABELS = {
    "top_left": "Top left",
    "top_center": "Top center",
    "top_right": "Top right",
    "center_left": "Center left",
    "center": "Center",
    "center_right": "Center right",
    "bottom_left": "Bottom left",
    "bottom_center": "Bottom center",
    "bottom_right": "Bottom right",
};

const COMPOSITION_ALIASES = {
    "Center": "center",
    "Left": "center_left",
    "Right": "center_right",
};

const normalizeComposition = (value) => {
    if (typeof value !== "string") return null;
    if (COMPOSITION_POSITIONS.includes(value)) return value;
    return COMPOSITION_ALIASES[value] || null;
};

const setCanvasDirty = () => {
    if (app.graph) {
        app.graph.setDirtyCanvas(true, true);
    }
};

const findNodeWidget = (node, name) => {
    return node.widgets ? node.widgets.find((widget) => widget.name === name) : null;
};

const COMPOSITION_GRID_MIN_SIZE = [330, 450];

const ensureCompositionGridSize = (node) => {
    if (!node || typeof node.setSize !== "function") return;

    const currentSize = Array.isArray(node.size) ? node.size : [];
    const width = Number.isFinite(Number(currentSize[0])) ? Number(currentSize[0]) : 0;
    const height = Number.isFinite(Number(currentSize[1])) ? Number(currentSize[1]) : 0;
    const nextWidth = Math.max(width, COMPOSITION_GRID_MIN_SIZE[0]);
    const nextHeight = Math.max(height, COMPOSITION_GRID_MIN_SIZE[1]);

    // Only grow undersized nodes. Larger user-resized nodes remain untouched.
    if (nextWidth !== width || nextHeight !== height) {
        node.setSize([nextWidth, nextHeight]);
    }
};

const setupCompositionGrid = (node) => {
    if (!node || node.comfyClass !== "SmartExpectedBox") return true;
    if (node._tlayoxCompositionGrid) return true;

    const compositionWidget = findNodeWidget(node, "composition");
    if (!compositionWidget) return false;

    // Keep the original combo usable on older ComfyUI frontend versions.
    if (typeof node.addDOMWidget !== "function" || typeof document === "undefined") return true;
    if (compositionWidget._tlHidden) return true;

    const initialComposition = normalizeComposition(compositionWidget.value);
    // Do not silently coerce arbitrary values. The backend combo remains the
    // fallback UI for a workflow value outside the approved contract.
    if (!initialComposition) return true;

    const element = document.createElement("div");
    element.className = "tlayox-composition-grid";
    element.role = "radiogroup";
    element.setAttribute("role", "radiogroup");
    element.setAttribute("aria-label", "Composition position");
    element.style.display = "grid";
    element.style.gridTemplateColumns = "repeat(3, minmax(24px, 1fr))";
    element.style.gap = "4px";
    element.style.padding = "4px 0";
    element.style.minHeight = "92px";

    const radioInputs = new Map();
    const cleanupListeners = [];
    const controller = typeof AbortController === "function" ? new AbortController() : null;

    const updateRadioState = (value) => {
        const canonical = normalizeComposition(value);
        if (!canonical) return false;
        for (const [position, radio] of radioInputs) {
            radio.checked = position === canonical;
        }
        return true;
    };

    const syncSerializedValue = (value, notify = true) => {
        const canonical = normalizeComposition(value);
        if (!canonical) return false;
        const changed = compositionWidget.value !== canonical;
        compositionWidget.value = canonical;
        updateRadioState(canonical);
        if (notify && changed && typeof compositionWidget.callback === "function") {
            compositionWidget.callback.call(compositionWidget, canonical);
        }
        setCanvasDirty();
        return true;
    };

    // Normalize legacy workflow values before the DOM widget is attached so
    // the hidden backend combo remains the single serialized source of truth.
    syncSerializedValue(initialComposition, false);

    const radioName = `tlayox-composition-${node.id || "node"}`;
    for (const position of COMPOSITION_POSITIONS) {
        const label = document.createElement("label");
        const radio = document.createElement("input");
        const labelText = document.createElement("span");
        const readableLabel = COMPOSITION_LABELS[position];

        radio.type = "radio";
        radio.name = radioName;
        radio.value = position;
        radio.checked = position === initialComposition;
        radio.setAttribute("aria-label", readableLabel);
        labelText.textContent = readableLabel;
        labelText.style.fontFamily = "sans-serif";
        labelText.style.fontSize = "12px";
        labelText.style.lineHeight = "1.2";
        labelText.style.flex = "1 1 0";
        labelText.style.minWidth = "0";
        labelText.style.whiteSpace = "normal";
        labelText.style.overflowWrap = "anywhere";
        labelText.style.textAlign = "left";
        label.title = readableLabel;
        label.style.display = "flex";
        label.style.alignItems = "center";
        label.style.justifyContent = "flex-start";
        label.style.flexWrap = "wrap";
        label.style.gap = "4px";
        label.style.minHeight = "26px";
        label.style.cursor = "pointer";
        label.append(radio, labelText);
        element.append(label);
        radioInputs.set(position, radio);

        const onChange = () => {
            if (radio.checked) syncSerializedValue(position);
        };
        if (controller) {
            radio.addEventListener("change", onChange, { signal: controller.signal });
        } else {
            radio.addEventListener("change", onChange);
            cleanupListeners.push(() => radio.removeEventListener("change", onChange));
        }
    }

    let domWidget;
    try {
        domWidget = node.addDOMWidget("composition_grid", "radio_grid", element, {
            hideOnZoom: true,
            getValue: () => normalizeComposition(compositionWidget.value) || compositionWidget.value,
            setValue: (value) => syncSerializedValue(value, false),
        });
    } catch (error) {
        // Leave the backend combo visible if a host exposes a different API.
        for (const cleanup of cleanupListeners) cleanup();
        return true;
    }

    if (!domWidget) {
        for (const cleanup of cleanupListeners) cleanup();
        return true;
    }

    ensureCompositionGridSize(node);

    // The hidden backend combo, not this visual-only widget, owns workflow and
    // prompt persistence.
    domWidget.serialize = false;
    if (domWidget.options) domWidget.options.serialize = false;

    compositionWidget._tlHidden = true;
    compositionWidget._tlOrigComputeSize = compositionWidget.computeSize;
    compositionWidget._tlOrigDraw = compositionWidget.draw;
    compositionWidget.computeSize = () => [0, -4];
    compositionWidget.draw = () => {};
    if (compositionWidget.inputEl) {
        compositionWidget._tlOrigInputDisplay = compositionWidget.inputEl.style.display;
        compositionWidget.inputEl.style.display = "none";
    }
    if (compositionWidget.labelEl) {
        compositionWidget._tlOrigLabelDisplay = compositionWidget.labelEl.style.display;
        compositionWidget.labelEl.style.display = "none";
    }
    if (compositionWidget.element && compositionWidget.element !== compositionWidget.inputEl) {
        compositionWidget._tlOrigElementDisplay = compositionWidget.element.style.display;
        compositionWidget.element.style.display = "none";
    }

    const originalCompositionCallback = compositionWidget.callback;
    compositionWidget.callback = function () {
        if (originalCompositionCallback) {
            originalCompositionCallback.apply(this, arguments);
        }
        const canonical = normalizeComposition(this.value);
        if (canonical) {
            if (this.value !== canonical) this.value = canonical;
            updateRadioState(canonical);
        }
    };

    const originalOnRemove = domWidget.onRemove;
    domWidget.onRemove = function () {
        if (originalOnRemove) originalOnRemove.call(this);
        if (controller) controller.abort();
        for (const cleanup of cleanupListeners) cleanup();
        compositionWidget._tlHidden = false;
        compositionWidget.computeSize = compositionWidget._tlOrigComputeSize;
        compositionWidget.draw = compositionWidget._tlOrigDraw;
        if (compositionWidget.inputEl) {
            compositionWidget.inputEl.style.display = compositionWidget._tlOrigInputDisplay || "";
        }
        if (compositionWidget.labelEl) {
            compositionWidget.labelEl.style.display = compositionWidget._tlOrigLabelDisplay || "";
        }
        if (compositionWidget.element && compositionWidget.element !== compositionWidget.inputEl) {
            compositionWidget.element.style.display = compositionWidget._tlOrigElementDisplay || "";
        }
        compositionWidget.callback = originalCompositionCallback;
        node._tlayoxCompositionGrid = null;
    };

    node._tlayoxCompositionGrid = { element, domWidget, compositionWidget };
    setCanvasDirty();
    return true;
};

const scheduleCompositionGrid = (node) => {
    if (!node || node.comfyClass !== "SmartExpectedBox") return;
    if (node._tlayoxCompositionGrid || node._tlayoxCompositionGridSetupTimer) return;
    if (setupCompositionGrid(node)) return;

    node._tlayoxCompositionGridSetupTimer = setTimeout(() => {
        node._tlayoxCompositionGridSetupTimer = null;
        setupCompositionGrid(node);
    }, 50);
};

app.registerExtension({
    name: "Tlayox.Dynamic",

    async afterConfigureGraph() {
        const graph = app.graph;
        if (!graph) return;
        const nodes = graph._nodes || graph.nodes || [];
        for (const node of nodes) {
            scheduleCompositionGrid(node);
            if (node.comfyClass !== "PromptBuilder") continue;
            if (!node.widgets) continue;
            for (const w of node.widgets) {
                const cleanName = LABEL_MAP[w.name];
                if (cleanName) {
                    w.label = cleanName;
                }
            }
        }
        graph.setDirtyCanvas(true, true);
    },

    async nodeCreated(node) {
        if (node.comfyClass === "SmartExpectedBox") {
            scheduleCompositionGrid(node);
            return;
        }
        if (node.comfyClass !== "PromptBuilder") return;

        const WIDGET_DEFAULTS = {
            Type_Photography: "Macro",
            Atmosphere_Tlayox: "1- Tlayox",
            Atmosphere_Altepetl: "Ambar",
            Atmosphere_Otra: "",
        };

        const findWidget = (name) => {
            return node.widgets ? node.widgets.find(w => w.name === name) : null;
        };

        const applyLabels = () => {
            if (!node.widgets) return;
            for (const w of node.widgets) {
                const cleanName = LABEL_MAP[w.name];
                if (cleanName) {
                    w.label = cleanName;
                }
            }
            if (app.graph) {
                app.graph.setDirtyCanvas(true, true);
            }
        };

        const hideWidget = (w) => {
            if (!w || w._tlHidden) return;
            w._tlHidden = true;

            w._tlOrigComputeSize = w.computeSize;
            w._tlOrigDraw = w.draw;

            w.computeSize = () => [0, -4];
            w.draw = () => {};

            // Hide associated DOM elements (null-safe)
            if (w.inputEl) {
                w._tlOrigInputDisplay = w.inputEl.style.display;
                w.inputEl.style.display = "none";
            }
            if (w.labelEl) {
                w._tlOrigLabelDisplay = w.labelEl.style.display;
                w.labelEl.style.display = "none";
            }
            if (w.element && w.element !== w.inputEl) {
                w._tlOrigElementDisplay = w.element.style.display;
                w.element.style.display = "none";
            }
        };

        const showWidget = (w) => {
            if (!w || !w._tlHidden) return;
            w._tlHidden = false;

            w.computeSize = w._tlOrigComputeSize;
            w.draw = w._tlOrigDraw;

            if (w.inputEl) {
                w.inputEl.style.display = w._tlOrigInputDisplay || "";
            }
            if (w.labelEl) {
                w.labelEl.style.display = w._tlOrigLabelDisplay || "";
            }
            if (w.element && w.element !== w.inputEl) {
                w.element.style.display = w._tlOrigElementDisplay || "";
            }
        };

        const MARGIN = 4;
        const HEADER_H = 30;
        const WIDGET_H = 26;
        const PAD = 16;

        const recomputeSize = () => {
            const visWidgets = node.widgets.filter(w => !w._tlHidden);

            let contentH = 0;
            for (const w of visWidgets) {
                let h = WIDGET_H;
                if (w.type === "text" || w.type === "customtext" || (w.options && w.options.multiline)) {
                    const lines = ((w.value || "") + "").split("\n").length;
                    h = Math.max(60, Math.min(lines, 8) * 18 + 8);
                }
                contentH += h + MARGIN;
            }

            const neededH = HEADER_H + contentH + PAD;
            const newW = Math.max(node.size[0], 300);
            const newH = Math.max(node.size[1], neededH);

            if (newH !== node.size[1] || newW !== node.size[0]) {
                node.setSize([newW, newH]);
            }
        };

        const updateVisibility = () => {
            if (!node.widgets) return;

            const baseWidget = findWidget("Base_Format");
            const brandWidget = findWidget("Brand");
            if (!baseWidget || !brandWidget) return;

            const typePhotography = findWidget("Type_Photography");
            if (baseWidget.value === "Screenshot") {
                hideWidget(typePhotography);
            } else {
                showWidget(typePhotography);
            }

            const atmosTlayox = findWidget("Atmosphere_Tlayox");
            const atmosAltepetl = findWidget("Atmosphere_Altepetl");
            const atmosOtra = findWidget("Atmosphere_Otra");

            if (brandWidget.value === "Tlayox") {
                showWidget(atmosTlayox);
                hideWidget(atmosAltepetl);
                hideWidget(atmosOtra);
            } else if (brandWidget.value === "Altepetl") {
                hideWidget(atmosTlayox);
                showWidget(atmosAltepetl);
                hideWidget(atmosOtra);
            } else {
                hideWidget(atmosTlayox);
                hideWidget(atmosAltepetl);
                showWidget(atmosOtra);
            }

            recomputeSize();
            if (app.graph) {
                app.graph.setDirtyCanvas(true, true);
            }
        };

        const setupNode = () => {
            if (!node.widgets || node.widgets.length === 0) {
                setTimeout(setupNode, 50);
                return;
            }

            for (const wName of ["Base_Format", "Brand"]) {
                const w = findWidget(wName);
                if (w) {
                    const origCallback = w.callback;
                    w.callback = function () {
                        if (origCallback) origCallback.apply(this, arguments);
                        updateVisibility();
                    };
                }
            }

            applyLabels();
            updateVisibility();
        };

        setupNode();
    },
});
