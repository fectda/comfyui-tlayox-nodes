# ComfyUI-Tlayox-Nodes

Custom nodes for ComfyUI by Tlayox.

## Nodes

| Node | Category | Description |
|------|----------|-------------|
| 📐 Instagram Preset Size | Tlayox/Utils | Dropdown with Instagram aspect ratio presets. Outputs `width` and `height` as INT. |
| 📏 Fit Size Calculator | Tlayox/Utils | Calculates how to fit an image or layer within a specific bounding size. |
| 🎯 Center Align Calculator | Tlayox/Utils | Calculates the X and Y coordinates to center an object inside a background. |
| 🔢 Megapixel Calculator | Tlayox/Utils | Scales image dimensions to match a target megapixel count. |
| 📊 Max Side | Tlayox/Utils | Proportionally scales width and height so the maximum side matches a target value. |
| 📝 Tlayox 8 Views Text | Tlayox | Text combiner designed to merge multiple viewpoints into a unified prompt. |
| 🏗️ Tlayox Prompt Builder | Tlayox | Dynamically constructs prompts based on Brand, Atmosphere, Format, and Type from `.md` files. |

## Presets

| Preset | Width | Height | Ratio |
|--------|-------|--------|-------|
| Stories & Reels | 1080 | 1920 | 9:16 |
| Feed Vertical | 1080 | 1350 | 4:5 |
| Feed Cuadrado | 1080 | 1080 | 1:1 |
| Feed Horizontal | 1080 | 566 | 1.91:1 |
| Foto de Perfil | 320 | 320 | 1:1 |

## Installation

Clone into `custom_nodes/` and restart ComfyUI.

```bash
cd custom_nodes
git clone <repo-url> ComfyUI-Tlayox-Nodes
```
