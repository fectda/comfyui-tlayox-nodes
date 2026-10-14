const { app } = window.comfyAPI.app;

const BRAND_WIDGET_NAME = "Brand";
const BACKGROUND_COLOR_WIDGET_NAME = "Background_Color_Otra";

const findWidget = (node, name) => {
    return node.widgets ? node.widgets.find(w => w.name === name) : null;
};

const hideWidget = (widget) => {
    if (!widget || widget._tlHidden) return;
    widget._tlHidden = true;

    widget._tlOrigComputeSize = widget.computeSize;
    widget._tlOrigDraw = widget.draw;
    widget.computeSize = () => [0, -4];
    widget.draw = () => {};

    if (widget.inputEl) {
        widget._tlOrigInputDisplay = widget.inputEl.style.display;
        widget.inputEl.style.display = "none";
    }
    if (widget.labelEl) {
        widget._tlOrigLabelDisplay = widget.labelEl.style.display;
        widget.labelEl.style.display = "none";
    }
    if (widget.element && widget.element !== widget.inputEl) {
        widget._tlOrigElementDisplay = widget.element.style.display;
        widget.element.style.display = "none";
    }
};

const showWidget = (widget) => {
    if (!widget || !widget._tlHidden) return;
    widget._tlHidden = false;

    widget.computeSize = widget._tlOrigComputeSize;
    widget.draw = widget._tlOrigDraw;

    if (widget.inputEl) {
        widget.inputEl.style.display = widget._tlOrigInputDisplay || "";
    }
    if (widget.labelEl) {
        widget.labelEl.style.display = widget._tlOrigLabelDisplay || "";
    }
    if (widget.element && widget.element !== widget.inputEl) {
        widget.element.style.display = widget._tlOrigElementDisplay || "";
    }
};

const recomputeNodeSize = (node) => {
    if (!node.widgets || !node.size || !node.setSize) return;

    const visibleWidgets = node.widgets.filter(w => !w._tlHidden);
    let contentHeight = 0;
    for (const widget of visibleWidgets) {
        let height = 26;
        if (widget.type === "text" || widget.type === "customtext" || (widget.options && widget.options.multiline)) {
            const lines = ((widget.value || "") + "").split("\n").length;
            height = Math.max(60, Math.min(lines, 8) * 18 + 8);
        }
        contentHeight += height + 4;
    }

    const neededHeight = 30 + contentHeight + 16;
    const newWidth = Math.max(node.size[0], 300);
    const newHeight = Math.max(node.size[1], neededHeight);
    if (newHeight !== node.size[1] || newWidth !== node.size[0]) {
        node.setSize([newWidth, newHeight]);
    }
};

const setupNode = (node) => {
    if (!node.widgets || node.widgets.length === 0) {
        setTimeout(() => setupNode(node), 50);
        return;
    }

    const brandWidget = findWidget(node, BRAND_WIDGET_NAME);
    const backgroundColorWidget = findWidget(node, BACKGROUND_COLOR_WIDGET_NAME);
    if (!brandWidget || !backgroundColorWidget) return;

    backgroundColorWidget.label = "Background Color";

    const updateVisibility = () => {
        if (brandWidget.value === "Otra") {
            showWidget(backgroundColorWidget);
        } else {
            hideWidget(backgroundColorWidget);
        }

        recomputeNodeSize(node);
        if (app.graph) {
            app.graph.setDirtyCanvas(true, true);
        }
    };

    if (!brandWidget._tlBackgroundColorCallbackInstalled) {
        const originalCallback = brandWidget.callback;
        brandWidget.callback = function () {
            if (originalCallback) originalCallback.apply(this, arguments);
            updateVisibility();
        };
        brandWidget._tlBackgroundColorCallbackInstalled = true;
    }

    updateVisibility();
};

app.registerExtension({
    name: "Tlayox.PromptBuilderBackgroundColor",

    async afterConfigureGraph() {
        const graph = app.graph;
        if (!graph) return;

        const nodes = graph._nodes || graph.nodes || [];
        for (const node of nodes) {
            if (node.comfyClass !== "PromptBuilder") continue;
            setupNode(node);
        }
    },

    async nodeCreated(node) {
        if (node.comfyClass !== "PromptBuilder") return;
        setupNode(node);
    },
});
