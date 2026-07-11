import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Tlayox.Dynamic",
    async nodeCreated(node) {
        if (node.comfyClass === "TextSwitchDynamic") {
            
            const addTitleToWidget = (w, title) => {
                if (w._hasTitle) return;
                w._hasTitle = true;
                w._origDraw = w.draw;
                w._origComputeSize = w.computeSize;
                
                w.computeSize = function(width) {
                    let size = w._origComputeSize ? w._origComputeSize.call(this, width) : [width, 40];
                    return [size[0], size[1] + 24]; // Add 24px for the title
                };
                
                w.draw = function(ctx, node, widget_width, y, widget_height) {
                    // Draw label
                    ctx.save();
                    ctx.fillStyle = "#A0A0A0";
                    ctx.font = "bold 14px sans-serif";
                    ctx.fillText(title, 15, y + 16);
                    ctx.restore();
                    
                    // Draw original widget shifted down
                    if (w._origDraw) {
                        w._origDraw.call(this, ctx, node, widget_width, y + 24, widget_height - 24);
                    }
                };
            };

            const setupDynamicBehavior = () => {
                // Add Labels
                const labels = {
                    "1_Tlayox": "📝 1- Tlayox",
                    "2_Memories": "📝 2- Memories",
                    "3_Woodworkers": "📝 3- Woodworkers",
                    "4_Cookie_Cuters": "📝 4- Cookie Cuters",
                    "Ambar": "📝 Ambar",
                    "Turquesa": "📝 Turquesa",
                    "Rojo": "📝 Rojo"
                };
                
                for (const [name, title] of Object.entries(labels)) {
                    const w = node.widgets.find(x => x.name === name);
                    if (w) addTitleToWidget(w, title);
                }

                // Visibility logic
                const updateVisibility = () => {
                    const catWidget = node.widgets.find(w => w.name === "Categoria");
                    if (!catWidget) return;
                    
                    const isTlayox = catWidget.value === "Tlayox";
                    
                    const showWidgets = (names) => {
                        for (const name of names) {
                            const w = node.widgets.find(x => x.name === name);
                            if (w) {
                                if (w.origType !== undefined) {
                                    w.type = w.origType;
                                    w.origType = undefined;
                                }
                                if (w.origComputeSize !== undefined) {
                                    w.computeSize = w.origComputeSize;
                                    w.origComputeSize = undefined;
                                }
                            }
                        }
                    };
                    
                    const hideWidgets = (names) => {
                        for (const name of names) {
                            const w = node.widgets.find(x => x.name === name);
                            if (w && w.type !== "hidden") {
                                w.origType = w.type;
                                w.origComputeSize = w.computeSize;
                                w.type = "hidden";
                                w.computeSize = () => [0, -4];
                            }
                        }
                    };

                    if (isTlayox) {
                        showWidgets(["Estilo_Tlayox", "1_Tlayox", "2_Memories", "3_Woodworkers", "4_Cookie_Cuters"]);
                        hideWidgets(["Estilo_Altepetl", "Ambar", "Turquesa", "Rojo"]);
                    } else {
                        hideWidgets(["Estilo_Tlayox", "1_Tlayox", "2_Memories", "3_Woodworkers", "4_Cookie_Cuters"]);
                        showWidgets(["Estilo_Altepetl", "Ambar", "Turquesa", "Rojo"]);
                    }

                    if (node.setSize) {
                        node.setSize(node.computeSize());
                    }
                    app.graph.setDirtyCanvas(true, true);
                };

                // Hook callback
                const catWidget = node.widgets.find(w => w.name === "Categoria");
                if (catWidget) {
                    const origCallback = catWidget.callback;
                    catWidget.callback = function() {
                        if (origCallback) origCallback.apply(this, arguments);
                        updateVisibility();
                    };
                    updateVisibility();
                }
            };

            const ensureSetup = () => {
                if (node.widgets && node.widgets.find(w => w.name === "Rojo")) {
                    setupDynamicBehavior();
                } else {
                    setTimeout(ensureSetup, 50);
                }
            };
            ensureSetup();
        }
    }
});
