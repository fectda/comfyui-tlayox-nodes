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
| 📦 Smart Expected Box | Tlayox/Math | Calculates a target-aspect expected box around a crop box using fixed-pixel `safety_padding_px` and a canonical 3x3 composition anchor, then returns eight crop/pad values plus diagnostic `BOX_DATA`. |
| 🖼️ Smart Crop Extend | Tlayox/Image | Consumes the eight routing values, preserves source pixels without resizing, and returns a prepared `IMAGE` plus a `[B, H, W]` outpaint mask (`1.0` for padded regions, `0.0` for source pixels). |
| 🐞 Smart Expected Box Debugger | Tlayox/Debug | Development-only visualization that draws the detected box in blue, safe box in red, expected box in green, and selected 3x3 guide lines using `BOX_DATA`. |

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

Do not copy arbitrary files into the parent ComfyUI Git repository or run repository Git commands from the parent directory. The established workflow process permits synchronizing only the authorized `user/default/workflows/visual_debugger_workflow.json` artifact after its hostless checks pass; `story_o_reel-ajustar_tamano.json` remains protected.

## Verification

From this repository root, run the focused SmartExpectedBox tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider --confcutdir=tests tests/test_smart_expected_box.py tests/test_smart_expected_box_audit.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider --confcutdir=tests tests/test_smart_crop_extend.py tests/test_node_registration.py tests/test_workflow_graph.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider --confcutdir=tests tests/test_smart_expected_box_debugger.py
```

After restarting ComfyUI, confirm that the nodes appear under `Tlayox/Math`, `Tlayox/Image`, and `Tlayox/Debug`. `SmartExpectedBox` provides geometry and routing data; `SmartCropExtend` prepares the non-stretched canvas and mask; `SmartExpectedBoxDebugger` visualizes `BOX_DATA` for development review.

## SmartExpectedBox development workflow

This repository owns the authoritative workflow generator and its generated UI-style artifact:

- Generator: `workflows/make_smart_expected_box_debug_workflow.py`
- Artifact: `workflows/smart_expected_box_debug_workflow.json`

Regenerate the artifact from this repository root:

```bash
python3 workflows/make_smart_expected_box_debug_workflow.py
```

The generator is deterministic and writes only the JSON sibling beside itself. To import the workflow without modifying the parent ComfyUI checkout, open the ComfyUI host UI, choose its workflow **Load/Open** action, and select the artifact directly from this repository:

```text
/path/to/ComfyUI/custom_nodes/ComfyUI-Tlayox-Nodes/workflows/smart_expected_box_debug_workflow.json
```

Do not copy the artifact into arbitrary parent workflows, and do not run Git commands from the parent repository. After hostless checks pass, the established process may synchronize only the authorized `user/default/workflows/visual_debugger_workflow.json`; `story_o_reel-ajustar_tamano.json` must never be edited.

The graph is:

```text
LoadImage ──> existing image-size node ──> SmartExpectedBox (orig_w/orig_h)
    │
    └──> RMBG ──> MaskBoxDetect ──> SmartExpectedBox (crop_box)

InstagramPresetSize ──> SmartExpectedBox (target_w/target_h)

SmartExpectedBox crop 0..3 ──> SmartCropExtend (pad inputs = 0)
                                      │
                                      └──> ImagePadForOutpaint (pad 4..7, feathering=40)
                                                ├──> DrawMaskOnImage (green preview)
                                                │       └──> ImageScaleToTotalPixels (1 MP)
                                                │                 └──> Square Outpaint block
                                                └──> MASK ──> MaskToImage ──> PreviewImage
SmartExpectedBox BOX_DATA + original IMAGE ──> SmartExpectedBoxDebugger ──> PreviewImage
```

The artifact follows the inspected host reference for external output slots: `GetImageSizeAndCount` slots `1` and `2` feed `orig_w` and `orig_h`, `RMBG` slot `1` feeds the mask detector, and `LayerMask: MaskBoxDetect` slot `7` feeds `crop_box`. The standard built-in `MaskToImage` node is required for the mask preview branch.

`tests/test_workflow_graph.py` validates the generated artifact and also checks that it matches the deterministic generator. The workflow reuses the existing square-outpaint subgraph and exposes an optional `RealESRGAN_x4plus.pth` branch after model output. The feathered mask remains diagnostic-only; the model receives the resized prepared `IMAGE`.

## Composition alignment contract

`SmartExpectedBox` exposes a compact accessible 3x3 radio grid in the current ComfyUI frontend. The hidden backend combo remains the serialized source of truth and accepts exactly these canonical values:

| Position | x anchor | y anchor |
|---|---:|---:|
| `top_left` | `1/3` | `1/3` |
| `top_center` | `1/2` | `1/3` |
| `top_right` | `2/3` | `1/3` |
| `center_left` | `1/3` | `1/2` |
| `center` | `1/2` | `1/2` |
| `center_right` | `2/3` | `1/2` |
| `bottom_left` | `1/3` | `2/3` |
| `bottom_center` | `1/2` | `2/3` |
| `bottom_right` | `2/3` | `2/3` |

The legacy direct-call/workflow values `Center`, `Left`, and `Right` normalize to `center`, `center_left`, and `center_right`. Other arbitrary values are rejected; they are not silently interpreted.

The grid is implemented in `web/js/tlayox_dynamic.js` with `node.addDOMWidget`; the hidden `composition` combo remains the serialized workflow/API value. If the host frontend does not provide `addDOMWidget`, the original combo remains visible and workflow execution stays functional.

The detected subject remains the input to the existing `RMBG` → `MaskBoxDetect` path. Fixed-pixel `safety_padding_px` is applied around that detected box before aspect-ratio fitting. If any 3x3 anchor would otherwise push the padded safe box outside the expected box, the router enlarges the expected box while preserving the requested aspect ratio; it never crops the safe box because of the composition choice. If the realized expected box crosses the original canvas horizontally or vertically, the router reports that overflow as the corresponding left/right/top/bottom pad values for `SmartCropExtend` rather than clamping or silently losing pixels. `BOX_DATA` exposes requested and realized x/y anchors plus rounding errors, expansion, and overflow diagnostics. The eight directional outputs and `BOX_DATA` output order are unchanged.

## Geometry edge behavior and audit coverage

`SmartExpectedBox` uses a conservative integer rasterization policy:

- fractional safe-box edges are rounded outward with floor/ceiling, so tiny boxes remain at least one source pixel wide and high;
- invalid dimensions, empty/inverted/out-of-bounds boxes, non-finite coordinates, invalid compositions, and negative/non-integer padding raise `ValueError`;
- `BOX_DATA["expected_box_expanded"]` and `BOX_DATA["expected_box_expansion"]` identify enlargement needed to preserve safe-box containment;
- `BOX_DATA["expected_box_overflow"]` and `BOX_DATA["requires_outpaint"]` identify expected-canvas overflow that becomes a generated-region mask after `SmartCropExtend`;
- `BOX_DATA["output_aspect_ratio"]`, `BOX_DATA["aspect_ratio_relative_error"]`, and `BOX_DATA["aspect_ratio_tolerance"]` make integer rounding observable;
- integer placement permits at most `0.5 / expected_width` x-anchor error and `0.5 / expected_height` y-anchor error;
- integer expected dimensions are allowed a relative aspect-ratio error of `1 / max(1, min(output_width, output_height) - 1)`, the documented one-pixel ceiling-rounding tolerance.

The hostless diagnostic suite runs 13,122 router cases across square/landscape/portrait source, detected-box, and target aspects; all nine canonical anchors; centered, edge, and corner placements; zero/moderate/large fixed padding; odd dimensions; and integer/fractional coordinates. `SmartCropExtend` additionally covers every binary combination of its eight directional inputs and every matrix-derived route. This is a logical deterministic audit only; it is not a visual or ComfyUI host-runtime validation.

The 3x3 choices are manual composition controls for intentional subject placement and negative space. The current detector does **not** infer gaze direction, movement direction, pose, or the photographic rule of space, so these selections must not be interpreted as automatic gaze/movement placement. Vertical overflow is handled as `pad_top`/`pad_bottom` and is not a movement-direction inference.

The rule-of-thirds and negative-space guidance used for this contract is documented by [Adobe](https://www.adobe.com/creativecloud/photography/technique/rule-of-thirds.html) and [Digital Photography School](https://digital-photography-school.com/rule-of-space-in-photography/).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the standalone repository boundary and quality workflow.
