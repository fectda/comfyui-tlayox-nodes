const { app } = window.comfyAPI.app;

const LABEL_MAP = {
    "Visual_Prompt": "Visual Prompt",
    "Atmosphere_Otra": "Atmosphere",
    "Atmosphere_Tlayox": "Atmosphere",
    "Atmosphere_Altepetl": "Atmosphere",
    "Base_Format": "Base Format",
    "Type_Photography": "Type",
};

app.registerExtension({
    name: "Tlayox.Dynamic",

    async afterConfigureGraph() {
        const graph = app.graph;
        if (!graph) return;
        const nodes = graph._nodes || graph.nodes || [];
        for (const node of nodes) {
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
