# ComfyUI-Tlayox-Nodes

Custom nodes for ComfyUI by Tlayox. This directory is an independent Git repository; ComfyUI is the runtime host, not the repository being developed here.

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
| 📦 Smart Expected Box | Tlayox/Math | Calculates a target-aspect expected box around a crop box and returns crop/pad routing values plus `BOX_DATA`. |
| 🐞 Smart Expected Box Debugger | Tlayox/Debug | Draws the safe-box and expected-box outlines on an `IMAGE` using `BOX_DATA`. |

## Presets

| Preset | Width | Height | Ratio |
|--------|-------|--------|-------|
| Stories & Reels | 1080 | 1920 | 9:16 |
| Feed Vertical | 1080 | 1350 | 4:5 |
| Feed Cuadrado | 1080 | 1080 | 1:1 |
| Feed Horizontal | 1080 | 566 | 1.91:1 |
| Foto de Perfil | 320 | 320 | 1:1 |

## Installation

Clone this repository directly into the `custom_nodes/` directory of the ComfyUI instance that will load it, then restart ComfyUI. The parent ComfyUI checkout remains the runtime host; this repository keeps its own history, branches, and remote.

```bash
cd /path/to/ComfyUI/custom_nodes
git clone git@github.com:fectda/comfyui-tlayox-nodes.git ComfyUI-Tlayox-Nodes
```

Do not copy these files into the parent ComfyUI Git repository or run repository Git commands from the parent directory.

## Verification

From this repository root, run the focused SmartExpectedBox tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider --confcutdir=tests tests/test_smart_expected_box.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider --confcutdir=tests tests/test_smart_expected_box_debugger.py
```

After restarting ComfyUI, confirm that the nodes appear under `Tlayox/Math` and `Tlayox/Debug`. `SmartExpectedBox` provides geometry and routing data; `SmartExpectedBoxDebugger` visualizes `BOX_DATA`. The current catalog does not include a crop, pad, or outpaint executor.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the standalone repository boundary and quality workflow.
