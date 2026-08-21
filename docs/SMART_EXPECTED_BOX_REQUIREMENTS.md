# Resume the SmartExpectedBox Crop/Pad Routing Project

This document is the English requirements baseline for the SmartExpectedBox development slice. It separates confirmed evidence from inference and unresolved decisions so geometry inspection, pixel preparation, and later model stages remain independently reviewable.

> **Current status:** The routing node, `SmartCropExtend` pixel-preparation executor, visual debugger, node registration, deterministic workflow generator, generated UI-style workflow artifact, accessible frontend 3x3 radio grid, and the deterministic 13,122-case geometry/executor audit are owned by this independent repository. The parent ComfyUI checkout remains a read-only UI-format reference and is not modified.

## Quick resume path

1. Read the router contract in `nodes/smart_expected_box.py`, the executor contract in `nodes/smart_crop_extend.py`, the debugger contract in `nodes/smart_expected_box_debugger.py`, and the frontend contract in `web/js/tlayox_dynamic.js`.
2. Run the focused hostless tests with the repository's `--confcutdir=tests` configuration.
3. Regenerate `workflows/smart_expected_box_debug_workflow.json` with `python3 workflows/make_smart_expected_box_debug_workflow.py` when the graph source changes.
4. Run `tests/test_workflow_graph.py` to verify both the generator/artifact identity and every serialized graph link.
5. Import the artifact directly through the ComfyUI host UI; do not copy it into the parent checkout's workflow directory.
6. Add the later model outpaint, optional upscale, and style stages only after the prepared canvas and debugger branch have been visually authorized.
7. Keep the router math-only and keep the development debugger branch available while the later executor stages are integrated.

## 1. Provenance and project status

### Evidence labels

| Label | Meaning |
|---|---|
| **Confirmed from Engram** | A prior project record explicitly states the design intent. It is historical evidence, not proof that the current files still implement every detail. |
| **Confirmed from current code/tests** | The inspected source, tests, workflow, or planning artifact directly shows the fact. |
| **Inferred** | A conclusion derived from current evidence. It must not be presented as an original requirement. |
| **Open decision** | The inspected evidence does not settle the behavior. The next implementation pass must decide and test it. |

### Confirmed baseline

- **Confirmed from Engram:** Engram #1569 records the decision to separate crop/pad routing mathematics from pixel editing, calculate a forced target aspect ratio over the original canvas, return eight mutually exclusive directional values, and use strict TDD as the intended development method.
- **Confirmed from Engram:** Engram #1650 records the isolated, non-destructive visual debugger for validating the safe-box/expected-box geometry before crop or outpaint is applied.
- **Confirmed from current code/tests:** `SmartExpectedBox` exists, accepts original dimensions, target dimensions, `crop_box`, and fixed-pixel `safety_padding_px`, and returns eight integer routing outputs plus `BOX_DATA`.
- **Confirmed from current code/tests:** `SmartExpectedBoxDebugger` exists, draws detected/safe/expected boxes on ComfyUI image tensors, and processes the batch dimension.
- **Confirmed from current code/tests:** `SmartCropExtend` consumes the eight directional outputs, preserves source pixels without resizing, and returns a prepared `IMAGE` plus a `[B, H, W]` outpaint mask.
- **Confirmed from current code/tests:** `SmartExpectedBox`, `SmartCropExtend`, and `SmartExpectedBoxDebugger` are imported and registered in `__init__.py`.
- **Confirmed from current code/tests:** Focused tests cover router validation and output metadata, crop/extend direction mapping and mask polarity, debugger colors and immutability, registration, and optional workflow-graph validation.
- **Confirmed from current repository evidence:** `workflows/make_smart_expected_box_debug_workflow.py` is the authoritative generator and `workflows/smart_expected_box_debug_workflow.json` is its deterministic UI-style artifact.
- **Confirmed from the read-only host reference:** The external UI graph links `GetImageSizeAndCount` output slot `1` to the original width input and slot `2` to the original height input, `RMBG` output slot `1` to the mask detector, and `LayerMask: MaskBoxDetect` output slot `7` to the crop-box input. The reference exposes these facts through link records while leaving external `outputs` arrays empty; the child artifact therefore preserves slot positions without inventing external output names.
- **Confirmed from current repository tests:** The workflow contract test loads only the child-owned artifact, checks the proven external slots, checks all eight routing links, checks both debugger inputs, and checks prepared-image and mask-preview paths.
- **Confirmed from project boundary:** The parent ComfyUI workflow is read-only format evidence only. The artifact is imported by selecting its child-repository path in the host UI; no parent workflow file needs to be edited or copied.

### Repository hygiene note

Direct `git status --short --untracked-files=all` showed that the repository is non-clean because the approved SmartExpectedBox implementation and this documentation/test slice are user-owned working changes. This requirements document does not classify or alter unrelated changes.

## 2. Problem statement and goals

### Problem

Crop, pad, and outpaint decisions require geometry that respects a detected subject or safe region, the original image canvas, and a requested target aspect ratio. The historical design separated that decision from pixel editing because coupling the two makes edge cases harder to test and can introduce aspect-ratio distortion.

### Goals

1. Produce a deterministic expected rectangle shaped by the requested target aspect ratio and positioned with the selected two-axis 3x3 composition anchor.
2. Convert the expected rectangle into non-negative, integer crop/pad routing values relative to the original canvas.
3. Make crop and pad mutually exclusive on every side.
4. Preserve enough geometry in `BOX_DATA` for a human-readable visual check.
5. Keep routing free of image mutation, pixel generation, crop execution, pad execution, and model outpaint execution.
6. Make the `SmartCropExtend` executor contract explicit without silently resizing source pixels.
7. Preserve a development-only debugger branch so a human can authorize geometry before model outpaint, upscale, or style integration.

## 3. Coordinate vocabulary and box semantics

The coordinate distinction below is mandatory for every resumed implementation and test.

| Value | Current representation | Meaning |
|---|---|---|
| `crop_box` input | `[x1, y1, x2, y2]` | Two corner coordinates supplied to the router. The current code calculates `width = x2 - x1`, `height = y2 - y1`, and derives the center from those corners. |
| `safe_box` in `BOX_DATA` | `[left, top, width, height]` | Fixed-pixel padded box around the input crop box. Fractional edges are rasterized outward so the integer safe box cannot lose detected source pixels. |
| `expected_box` in `BOX_DATA` | `[left, top, width, height]` | Target-aspect-ratio box positioned so the detected subject center maps to the selected x/y anchors. It may extend outside the original canvas. |
| Original canvas | Dimensions `orig_w` by `orig_h` | The boundary against which expected-box overflow and in-canvas distances are routed. |
| Directional outputs | Eight scalar integers | Four crop values followed by four pad values, in the exact order documented in Section 4. |

The debugger passes box coordinates directly to `PIL.ImageDraw.rectangle`. This is consistent with a top-left image-coordinate convention. `SmartCropExtend` consumes directional distances rather than box coordinates and realizes the geometry by retaining a source slice and placing it on a zero-filled canvas. The router's crop/pad outputs are mutually exclusive per side; the executor still accepts independent direct-call distances, including mixed crop and pad values, because it has no `BOX_DATA` context to reinterpret.

## 4. Input/output contract and invariants

### 4.1 Router inputs

| Input | Current code contract | Requirement status |
|---|---|---|
| `orig_w` | `INT`; UI metadata default `1024`, minimum `1`, maximum `8192` | **Confirmed from current code/tests**. Runtime validation requires a positive integer. |
| `orig_h` | `INT`; UI metadata default `1024`, minimum `1`, maximum `8192` | **Confirmed from current code/tests**. Runtime validation requires a positive integer. |
| `target_w` | `INT`; UI metadata default `1080`, minimum `1`, maximum `8192` | **Confirmed from current code/tests**. Runtime validation requires a positive integer. |
| `target_h` | `INT`; UI metadata default `1920`, minimum `1`, maximum `8192` | **Confirmed from current code/tests**. Runtime validation requires a positive integer. |
| `crop_box` | `BOX`; exactly four finite numeric values as `[x1, y1, x2, y2]`, ordered and inside the original canvas | **Confirmed from current code/tests** |
| `safety_padding_px` | `INT`; fixed non-negative padding in source pixels, UI metadata default `20`, minimum `0`, maximum `8192` | **Confirmed from current code/tests**. The router expands both safe-box dimensions by `2 * safety_padding_px`. |
| `composition` | Canonical 3x3 radio-grid values in row-major order; UI and direct-call default `center` | **Confirmed from approved contract/current code/tests**. Legacy `Center`, `Left`, and `Right` aliases normalize to `center`, `center_left`, and `center_right`; arbitrary values are rejected. |

The canonical values and coordinates are:

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

### 4.2 Router outputs

The output order is a stable interface. The node currently declares eight `INT` outputs and one `DICT` output:

| Slot | Name | Current meaning |
|---:|---|---|
| 0 | `crop_left` | `max(0, exp_left)` |
| 1 | `crop_right` | `max(0, orig_w - exp_right)` |
| 2 | `crop_top` | `max(0, exp_top)` |
| 3 | `crop_bottom` | `max(0, orig_h - exp_bottom)` |
| 4 | `pad_left` | `max(0, -exp_left)` |
| 5 | `pad_right` | `max(0, exp_right - orig_w)` |
| 6 | `pad_top` | `max(0, -exp_top)` |
| 7 | `pad_bottom` | `max(0, exp_bottom - orig_h)` |
| 8 | `BOX_DATA` | Diagnostic-only dictionary containing detected, safe, expected, base-expected, size, aspect-ratio, operation, composition, realized-anchor, expansion, overflow, and outpaint metadata. |

The current formulas show that the crop values are side distances associated with the expected rectangle when it is inside the canvas, while the pad values are the expected rectangle's overflow when it extends outside the canvas. `SmartCropExtend` consumes these values in the documented order. It crops the source slice first, then adds zero-filled pixels for each pad distance; it does not resize or invoke a model.

### 4.3 Geometry calculation

For valid positive dimensions and a valid ordered crop box, the current calculation is:

```text
subject_width  = x2 - x1
subject_height = y2 - y1
center_x       = x1 + subject_width / 2
center_y       = y1 + subject_height / 2

continuous_safe_width  = subject_width  + 2 * safety_padding_px
continuous_safe_height = subject_height + 2 * safety_padding_px
integer_safe_edges = outward floor/ceiling rasterization of the padded edges

target_aspect_ratio = target_w / target_h
composition_anchor_x = 1/3, 1/2, or 2/3
composition_anchor_y = 1/3, 1/2, or 2/3
```

The expected rectangle uses the target aspect ratio while retaining the safe-box width or height:

- The continuous safe-box edges are rasterized as `floor(x1 - padding)`, `floor(y1 - padding)`, `ceil(x2 + padding)`, and `ceil(y2 + padding)`. This is an outward integer rasterization, not a nearest-edge rounding policy.
- If the integer `safe_width / safe_height > target_aspect_ratio`, the base expected width is the integer `safe_width` and the base expected height is the positive ceiling of `safe_width / target_aspect_ratio`.
- Otherwise, the base expected height is the integer `safe_height` and the base expected width is the positive ceiling of `safe_height * target_aspect_ratio`.
- For any non-centered x/y anchor, the expected rectangle is enlarged only when its integer placement would fail safe-box containment. The placements are `expected_left = round(center_x - composition_anchor_x * expected_width)` and `expected_top = round(center_y - composition_anchor_y * expected_height)`.
- The containment search uses exponential bracketing followed by binary search, so large padding and extreme aspect ratios do not trigger a pixel-by-pixel growth loop.
- Integer origin rounding allows x/y anchor error up to `0.5 / expected_width` and `0.5 / expected_height`; `BOX_DATA` exposes requested, realized, and error values for both axes.
- Integer aspect-ratio tolerance is documented as a relative error of at most `1 / max(1, min(output_width, output_height) - 1)`. This is the conservative one-pixel ceiling-rounding bound; exact rational ratios are not required for very small integer rectangles.

`BOX_DATA` distinguishes the two different boundary outcomes. `base_expected_box`, `expected_box_expanded`, and `expected_box_expansion` describe enlargement needed to contain the safe box at the selected x/y anchor. `expected_box_overflow` and `requires_outpaint` describe expected-box overflow beyond the original canvas and the resulting `SmartCropExtend` mask requirement. `requested_anchor_x`/`requested_anchor_y`, `realized_anchor_x`/`realized_anchor_y`, and `anchor_error_x`/`anchor_error_y` expose integer-placement rounding rather than hiding it. `output_aspect_ratio`, `aspect_ratio_relative_error`, and `aspect_ratio_tolerance` make the integer ratio decision inspectable.

### 4.4 Required invariants

| ID | Invariant | Status |
|---|---|---|
| INV-001 | The continuous safe region SHALL be centered on the center derived from `crop_box` and SHALL expand both continuous dimensions by exactly `2 * safety_padding_px`; its integer rasterization SHALL enclose that region. | **Confirmed from Engram; confirmed from current code/tests** |
| INV-002 | The expected box SHALL map the detected subject center to `composition_anchor_x * expected_width` and `composition_anchor_y * expected_height`, with x/y errors at most `0.5 / expected_width` and `0.5 / expected_height`. | **Confirmed from approved contract/current code/tests** |
| INV-003 | Before integer rounding, the expected box SHALL use `target_w / target_h` as its aspect ratio. | **Confirmed from current code/tests** |
| INV-004 | Safe-box edges SHALL use outward floor/ceiling rasterization; expected dimensions SHALL be positive integers produced by the documented ceiling policy; expected origins SHALL use deterministic nearest-integer placement. | **Confirmed from current code/tests** |
| INV-005 | For each side, crop and pad SHALL be mutually exclusive: at most one of `(crop_left, pad_left)`, `(crop_right, pad_right)`, `(crop_top, pad_top)`, and `(crop_bottom, pad_bottom)` may be non-zero. | **Confirmed from current code/tests** and the Engram design intent. |
| INV-006 | Under the normal integer input contract, all eight directional outputs SHALL be non-negative integers. | **Confirmed from current code/tests**; invalid geometry raises `ValueError`. |
| INV-007 | `BOX_DATA` SHALL preserve the current `[left, top, width, height]` representation for both `safe_box` and `expected_box`. | **Confirmed from current code/tests**. |
| INV-008 | The router SHALL not edit, resize, crop, pad, outpaint, or generate image pixels. | **Confirmed from Engram; confirmed from current code/tests**. |
| INV-009 | `SmartCropExtend` SHALL realize routed geometry by crop and zero-filled extension without stretching source pixels. Direct executor calls may combine crop and pad values on the same side; router output never does. | **Confirmed from current code/tests**. |
| INV-010 | The `SmartCropExtend` mask SHALL have shape `[B, H, W]`, dtype `float32`, value `0.0` for retained source pixels, and value `1.0` for newly padded regions. | **Confirmed from current code/tests**. |
| INV-011 | The development debugger branch SHALL retain the original image and `BOX_DATA`, and SHALL remain separate from model outpaint, upscale, and style stages. | **Confirmed from current code/tests and this development contract**. |
| INV-012 | The selected composition SHALL be one of the nine canonical 3x3 values with x/y anchors in `{1/3, 1/2, 2/3}`; the padded safe box SHALL remain fully contained by the expected box for every mode. Legacy `Center`, `Left`, and `Right` aliases SHALL normalize only to their center-row canonical values. | **Confirmed from approved contract/current code/tests** |

## 5. Functional requirements

The following requirements are the implementation baseline. A status label identifies the evidence level; it does not imply that every requirement is complete.

| ID | Requirement | Provenance/status |
|---|---|---|
| FR-001 | `SmartExpectedBox` SHALL accept original canvas width and height, target width and height, a four-value `crop_box`, fixed-pixel `safety_padding_px`, and one canonical 3x3 composition choice. | **Confirmed from approved contract/current code/tests** |
| FR-002 | The router SHALL derive the subject width, subject height, and subject center from `crop_box` before calculating the safe box. | **Confirmed from current code/tests** |
| FR-003 | The router SHALL expand the continuous subject width and height by `2 * safety_padding_px` around the subject center and SHALL rasterize the resulting safe edges outward for pixel routing. | **Confirmed from Engram; confirmed from current code/tests** |
| FR-004 | The router SHALL calculate an expected box whose unrounded aspect ratio is `target_w / target_h` and whose retained dimension is sufficient to contain the safe box. | **Confirmed from Engram; confirmed from current code/tests** |
| FR-005 | The router SHALL position the expected box so the subject center maps near the selected x/y anchors and enlarge the box when required to contain the padded safe box on both axes. | **Confirmed from approved contract/current code/tests** |
| FR-006 | The router SHALL return exactly eight directional values in this order: `crop_left`, `crop_right`, `crop_top`, `crop_bottom`, `pad_left`, `pad_right`, `pad_top`, `pad_bottom`. | **Confirmed from current code/tests** |
| FR-007 | For every side, the router SHALL return either a crop distance or a pad distance, never positive values for both on the same side. | **Confirmed from Engram; confirmed from current code/tests** |
| FR-008 | The router SHALL retain diagnostic-only `BOX_DATA` with `safe_box` and `expected_box`, both encoded as `[left, top, width, height]`, for the development debugger branch. | **Confirmed from current code/tests** |
| FR-009 | The router SHALL be deterministic for the same valid inputs. | **Confirmed from current code/tests** |
| FR-010 | The router SHALL remain independent of image tensors and pixel-editing libraries. | **Confirmed from current code/tests** |
| FR-011 | `SmartExpectedBox`, `SmartCropExtend`, and `SmartExpectedBoxDebugger` SHALL remain registered under those exact keys in `NODE_CLASS_MAPPINGS`. | **Confirmed from current code/tests** |
| FR-012 | `SmartCropExtend` SHALL preserve source pixels and realize the routed target geometry without resizing; its mask SHALL identify newly padded regions for a later model outpaint stage. | **Confirmed from current code/tests** |
| FR-013 | The development workflow SHALL expose the `SmartExpectedBoxDebugger` branch, crop-only `SmartCropExtend`, one `ImagePadForOutpaint` operation, the feathered green preview, the resized model IMAGE path, the diagnostic MASK, and the existing square-outpaint/upscale branches. | **Confirmed from the child-owned generator, artifact, and workflow test** |
| FR-014 | `BOX_DATA` SHALL include the canonical `composition`, requested/realized x/y anchor metadata, x/y anchor errors, safe-box-preserving expansion metadata, overflow/outpaint metadata, and numeric `composition_anchor_x`/`composition_anchor_y` while preserving all existing diagnostic keys and output slots. | **Confirmed from approved contract/current code/tests** |

## 6. Crop and pad behavior with existing examples

The executable assertions in the current tests are the source of truth for these examples. Some nearby test comments contain a one-pixel arithmetic discrepancy in the padding example; that discrepancy is called out below rather than silently normalized.

### Example A: Expected box fully inside the original canvas

Source: `tests/test_smart_expected_box.py`, `test_smart_expected_box_basic`.

| Input | Value |
|---|---|
| Original canvas | `1000 x 1000` |
| Target | `1080 x 1920` (`9:16`) |
| `crop_box` | `[400, 400, 600, 600]` |
| `safety_padding_px` | `20` |
| `BOX_DATA["safe_box"]` | `[380, 380, 240, 240]` |
| `BOX_DATA["expected_box"]` | `[380, 286, 240, 427]` |
| Crop outputs | `crop_left=380`, `crop_right=380`, `crop_top=286`, `crop_bottom=287` |
| Pad outputs | `pad_left=0`, `pad_right=0`, `pad_top=0`, `pad_bottom=0` |

This demonstrates a fully in-canvas expected box: every pad value is zero and the crop values describe the distances around the expected rectangle.

### Example B: Expected box requires horizontal padding

Source: `tests/test_smart_expected_box.py`, `test_smart_expected_box_needs_padding`.

| Input | Value |
|---|---|
| Original canvas | `200 x 200` |
| Target | `1920 x 1080` (`16:9`) |
| `crop_box` | `[50, 50, 150, 150]` |
| `safety_padding_px` | `25` |
| `BOX_DATA["safe_box"]` | `[25, 25, 150, 150]` |
| `BOX_DATA["expected_box"]` | `[-34, 25, 267, 150]` |
| Crop outputs | `crop_left=0`, `crop_right=0`, `crop_top=25`, `crop_bottom=25` |
| Pad outputs | `pad_left=34`, `pad_right=33`, `pad_top=0`, `pad_bottom=0` |

The executable assertions use `expected_box.left = -34`, `expected_box.right = 233`, `pad_left = 34`, and `pad_right = 33`. The comments immediately above those assertions describe `-33` and `234`; the implementation and assertions agree with the values listed here. The difference comes from Python's integer rounding strategy and is part of the current tested contract.

## 7. Visual debugger requirements

`SmartExpectedBoxDebugger` is a development-only diagnostic node. It must make the geometry visible without becoming an image-editing or model executor.

| ID | Requirement | Provenance/status |
|---|---|---|
| DBG-001 | The debugger SHALL accept an `IMAGE` tensor and a `DICT` named `BOX_DATA`, then return an `IMAGE` tensor. | **Confirmed from current code/tests** |
| DBG-002 | The debugger SHALL read `safe_box` and `expected_box` from `BOX_DATA` using `[left, top, width, height]` semantics. | **Confirmed from current code/tests** |
| DBG-003 | The debugger SHALL draw `detected_box` with a blue outline, `safe_box` with a red outline, `expected_box` with a green outline, the selected x anchor as a yellow vertical guide, and the selected y anchor as a cyan horizontal guide when that metadata is present. | **Confirmed from current code/tests** |
| DBG-004 | The current visual convention SHALL use a five-pixel outline width unless a replacement convention is explicitly approved and tested. | **Confirmed from current code** |
| DBG-005 | The debugger SHALL process each item in a batched ComfyUI image tensor and return a stacked batch with the same batch, height, width, and channel shape. | **Confirmed from current code/tests** for the existing batch-shaped input. |
| DBG-006 | The debugger SHALL create a new output tensor and SHALL NOT mutate the input image tensor. | **Confirmed from current code/tests** |
| DBG-007 | Behavior for an unbatched `(H, W, C)` tensor, missing box keys, malformed boxes, and channel values outside the normal `[0, 1]` range SHALL be defined and tested. | **Open decision** |

The current implementation converts each batch item from a normalized tensor to an 8-bit NumPy array, draws with `PIL.ImageDraw`, converts back to a normalized `float32` tensor, and stacks the results. Focused tests verify the blue/red/green pixels, batch handling, and input immutability. Unbatched tensors and malformed `BOX_DATA` remain outside the current contract.

### SmartCropExtend pixel-preparation requirements

`SmartCropExtend` remains the crop-only executor for this slice. It is deliberately not a model outpaint node; `ImagePadForOutpaint` owns the single padding operation and the existing square-outpaint block owns model inference.

| ID | Requirement | Provenance/status |
|---|---|---|
| EXT-001 | The executor SHALL consume `crop_left`, `crop_right`, `crop_top`, `crop_bottom`, `pad_left`, `pad_right`, `pad_top`, and `pad_bottom` in that exact order. | **Confirmed from current code/tests** |
| EXT-002 | The executor SHALL accept batched `IMAGE` tensors in `[B, H, W, C]` format and SHALL preserve batch, dtype, device, and source pixel values. | **Confirmed from current code/tests** |
| EXT-003 | The executor SHALL crop the source slice, place it on a zero-filled canvas, and SHALL NOT resize or stretch it. | **Confirmed from current code/tests** |
| EXT-004 | The executor SHALL return an `outpaint_mask` with shape `[B, H, W]`; `0.0` marks retained source pixels and `1.0` marks newly padded pixels. | **Confirmed from current code/tests** |
| EXT-005 | The executor SHALL not call or claim a model outpaint, upscale, or style-integration stage; those stages remain separate workflow nodes. | **Confirmed from current code and this slice boundary** |

## 8. Registration and workflow integration

### Registration

`__init__.py` currently:

- imports `SmartExpectedBox`, `SmartCropExtend`, and `SmartExpectedBoxDebugger`;
- registers all three under their exact class keys; and
- provides display names for all three nodes.

This is **Confirmed from current code/tests**. Registration itself is not a missing implementation task. A registration regression test remains useful.

`README.md` lists the three nodes and documents the implemented crop/extend/debugger boundary. It also identifies the child-owned workflow generator and artifact, the direct host-UI import path, the standard `MaskToImage` dependency, and the parent-repository boundary.

### Frontend composition widget

`web/js/tlayox_dynamic.js` keeps the backend `composition` combo as the canonical serialized widget and adds a visual-only 3x3 radio grid with `node.addDOMWidget` when that public API is available. The DOM widget is excluded from workflow and prompt serialization, while clicks and keyboard changes write canonical values back to the hidden combo. Loaded `Center`, `Left`, and `Right` values are normalized to their approved center-row aliases. If the host does not expose `addDOMWidget`, the extension leaves the original combo visible rather than risking workflow execution. The hostless checks verify this contract and JavaScript syntax; they do not claim browser or ComfyUI runtime validation.

### Diagnostic workflow

The intended development graph for this slice is:

```text
LoadImage
  ├─> existing image-size node ───────────────┐
  ├─> RMBG -> mask -> MaskBoxDetect ───────────┼─> SmartExpectedBox
  └───────────────────────────────────────────┘       │
                                                     ├─> crop/pad 0..7 -> SmartCropExtend
InstagramPresetSize ─────────────────────────────────┘

LoadImage + SmartExpectedBox BOX_DATA -> SmartExpectedBoxDebugger -> geometry PreviewImage
SmartCropExtend (crop-only) -> ImagePadForOutpaint (router pads, feathering=40)
ImagePadForOutpaint IMAGE + MASK -> DrawMaskOnImage (green preview)
DrawMaskOnImage IMAGE -> ImageScaleToTotalPixels (approximately 1 MP) -> Square Outpaint
ImagePadForOutpaint MASK -> MaskToImage -> diagnostic mask PreviewImage
```

The router inputs SHALL be wired as follows:

- the existing size node supplies `orig_w` and `orig_h` from its proven output slots `1` and `2`;
- the existing detection path supplies `crop_box` through `RMBG` output slot `1` and `LayerMask: MaskBoxDetect` output slot `7`;
- `InstagramPresetSize` supplies `target_w` and `target_h`;
- `safety_padding_px` remains the current fixed-pixel router input;
- router output slots 0 through 3 supply the four crop inputs on `SmartCropExtend`, whose four pad widgets remain zero;
- router output slots 4 through 7 supply `ImagePadForOutpaint` inputs `left`, `right`, `top`, and `bottom` in the host node's `left`, `top`, `right`, `bottom` order;
- router output slot 8 (`BOX_DATA`) and the original image supply the debugger; and
- the debugger, green preview, resized prepared `IMAGE`, model output, optional upscale output, and diagnostic MASK output points remain visible together; and
- only the resized green `IMAGE` is connected to the existing square-outpaint block; the feathered `MASK` is retained for preview/diagnostics only.

### Workflow artifact availability

The independent repository owns the workflow source and generated artifact:

| Candidate | Current evidence |
|---|---|
| `workflows/make_smart_expected_box_debug_workflow.py` | Authoritative deterministic generator. |
| `workflows/smart_expected_box_debug_workflow.json` | Generated UI-style artifact beside the generator. |
| `tests/test_workflow_graph.py` | Hostless parser and serialized graph contract, including generator/artifact identity. |
| `MaskToImage` | Standard host node required for the mask-to-preview branch. |

The generator writes only its sibling JSON. The authorized parent `visual_debugger_workflow.json` may be synchronized from that generated artifact after hostless graph tests pass; `story_o_reel-ajustar_tamano.json` remains untouched. The artifact embeds the existing square-outpaint subgraph and uses only existing host upscale nodes for the optional `RealESRGAN_x4plus.pth` branch.

## 9. Testing and acceptance criteria

### 9.1 Current coverage

| Area | Existing evidence | Coverage status |
|---|---|---|
| Composition-aware router | `test_smart_expected_box.py` checks all nine canonical positions, legacy aliases, x/y anchors, safe-box containment after off-center enlargement, ratio/crop-pad invariants, direct-call compatibility, metadata, and invalid composition values. | **Confirmed from current tests** |
| Systematic geometry matrix | `test_smart_expected_box_audit.py` runs 13,122 deterministic cases: 3 source aspects × 3 detected-box aspects × 3 target aspects × 9 compositions × 9 placements × 3 safety levels × 2 coordinate modes. It verifies dimensions, containment, x/y anchor rounding, ratio tolerance, routing arithmetic, crop/pad exclusivity, source retention, overflow metadata, and deterministic behavior. | **Confirmed from current tests** |
| Fully in-canvas expected box | `test_smart_expected_box_basic` checks all eight directional outputs, fixed padding, and `BOX_DATA`. | **Confirmed from current tests** |
| Out-of-canvas expected box | `test_smart_expected_box_needs_padding` checks horizontal padding, vertical crop values, and both boxes. | **Confirmed from current tests** |
| SmartCropExtend output | `test_smart_crop_extend.py` checks all 256 binary directional combinations, all 13,122 matrix-derived routes, mixed crop/pad behavior, batch behavior, non-stretching, mask shape/polarity, dtype/device, input immutability, and invalid executor inputs. | **Confirmed from current tests** |
| Debugger output | `test_smart_expected_box_debugger.py` checks blue/red/green placement, both selected x/y guide lines, batch output shape, legacy `BOX_DATA` compatibility, and input immutability. | **Confirmed from current tests** |
| Frontend contract | `test_frontend_contract.py` checks extension registration, `addDOMWidget`, native radio semantics, canonical/legacy values, hidden-widget persistence, cleanup, reconfiguration guards, and the API fallback. | **Confirmed from current tests** |
| Registration | `test_node_registration.py` checks the current class keys, display name, and fixed-pixel input without loading the host runtime. | **Confirmed from current tests** |
| Workflow graph | `test_workflow_graph.py` parses the child-owned UI JSON, compares it with the generator output, and checks external slots, all eight executor links, debugger inputs, and three preview paths. | **Confirmed from current tests** |

### 9.2 Verification snapshot from this inspection

- The repository test configuration uses `--confcutdir=tests`; focused tests are hostless and do not require the parent ComfyUI runtime.
- The workflow generator writes only `workflows/smart_expected_box_debug_workflow.json`; the test loads only that child-owned path and never searches the parent checkout.
- The UI graph follows the read-only reference's proven external source slots: size slots `1`/`2`, RMBG mask slot `1`, and MaskBoxDetect crop-box slot `7`. Because the reference leaves external `outputs` arrays empty, these slot positions are the explicit integration assumption under test.
- The current router validates positive integer dimensions, non-negative integer fixed padding, ordered in-bounds crop coordinates, finite numeric coordinates, and representable geometry; invalid inputs raise `ValueError` instead of being clamped. Fractional boxes are rasterized outward and very large but representable padding remains routable; padding beyond finite numeric geometry raises.
- The current executor validates batched image shape, non-negative integer directions, and non-empty retained source dimensions while preserving direct-call mixed crop/pad combinations.

### 9.3 Remaining test boundary

The geometry and pixel-preparation audit is complete for the current contract. The following remain intentionally outside this task:

- debugger behavior for malformed or incomplete `BOX_DATA` and unbatched input, because the current debugger contract accepts only valid batched ComfyUI `IMAGE` tensors and valid diagnostic boxes;
- visual or host-runtime validation in ComfyUI; this audit is deterministic and hostless only;
- model outpaint, upscale, and style integration tests after those stages are implemented.

### 9.4 Acceptance checklist

- [x] The hostless test harness imports the focused package consistently with the repository's pytest configuration.
- [x] Router tests cover inside-canvas crop routing, horizontal padding, fixed-pixel input, and invalid geometry.
- [x] Router tests cover all nine canonical positions, legacy Center/Left/Right aliases, invalid composition values, x/y safe-box containment after off-center enlargement, and direct-call compatibility.
- [x] Every valid router result has eight non-negative integer directional outputs.
- [x] Every side satisfies crop/pad mutual exclusion.
- [x] The 13,122-case matrix covers square/landscape/portrait source, detected, and target aspects; all nine canonical compositions; center, edge, and corner placements; zero/moderate/large padding; odd dimensions; and fractional coordinates.
- [x] Expected dimensions remain within the documented ceiling-rounding aspect-ratio tolerance for all matrix cases and extreme target aspects.
- [x] `safe_box` and `expected_box` use `[left, top, width, height]`; the input `crop_box` remains `[x1, y1, x2, y2]`.
- [x] Outward fractional rasterization, half-value rounding, and deterministic repeated routing are covered by executable examples.
- [x] Invalid-input behavior is explicit, tested, and does not silently generate invalid geometry.
- [x] `BOX_DATA` distinguishes expected-box expansion from expected-box overflow and exposes requested versus realized anchor values.
- [x] Debugger visuals follow blue detected, red safe, and green expected conventions and preserve batch shape.
- [x] Debugger visuals expose selected numeric x/y anchors without removing the detected, safe, or expected boxes.
- [x] Debugger output is non-destructive with respect to the input tensor.
- [x] `SmartCropExtend` consumes all eight routing outputs and returns a non-stretched prepared image plus a `[B, H, W]` mask with documented polarity.
- [x] `SmartCropExtend` preserves source pixels, dtype, device, batch behavior, and input immutability for every matrix-derived route and every binary directional combination.
- [x] The deterministic child-owned generator writes the serialized UI-style development workflow beside itself.
- [x] The serialized development workflow verifies every required graph link, including the proven external size/detection slots, all eight executor links, the `BOX_DATA` debugger link, the prepared-image preview, and the `MaskToImage` mask-preview path.
- [x] The workflow passes only the approximately 1 MP prepared `IMAGE` to the existing square-outpaint block and retains the feathered `MASK` for diagnostics.
- [x] The workflow exposes an optional post-outpaint `RealESRGAN_x4plus.pth` branch through existing host nodes; no model is downloaded by this repository.
- [x] `README.md` and this document explain child generation, authorized debugger-workflow synchronization, and the protected story workflow boundary.
- [x] `README.md` and this document explain the rule-of-thirds anchor contract and state that gaze/movement direction is not inferred by the current detector.

## 10. Explicit non-goals

The following are outside the router's responsibility:

- `SmartExpectedBox` does **not** perform a crop.
- `SmartExpectedBox` does **not** perform padding or outpainting.
- `SmartExpectedBox` does **not** generate pixels, masks, fills, or model output.
- `SmartExpectedBox` does **not** mutate image tensors; it has no image input in the current contract.
- `SmartCropExtend` performs only deterministic crop and zero-filled extension; it does **not** pad, resize, invoke a model outpaint, upscale, or apply style integration.
- `SmartExpectedBoxDebugger` is development-only; it does **not** apply crop, pad, or outpaint and only returns a visualization tensor.
- The system SHALL NOT silently distort an image to force a target aspect ratio.
- A visual debugger pass SHALL NOT be treated as proof that the actual crop/pad/outpaint executor is correct.
- The router does not perform model outpaint or upscale; those operations are represented only by separate existing workflow nodes.
- This document does not authorize changes to unrelated ComfyUI workflows, custom nodes, models, or repository configuration.

## 11. Open decisions and resumption backlog

### Open decisions

| ID | Decision needed | Why it is open |
|---|---|---|
| OD-003 | Select and implement the model outpaint stage that consumes the prepared image and mask. | **Resolved**: embed the existing square-outpaint block and connect only the resized prepared `IMAGE`; retain the feathered `MASK` for diagnostics. |
| OD-004 | Select optional upscale behavior and its placement after model outpaint. | **Resolved**: use the installed `RealESRGAN_x4plus.pth` through existing `UpscaleModelLoader` and `ImageUpscaleWithModel` nodes. |
| OD-005 | Define style integration inputs and ordering after geometry approval and model stages. | No style node is implemented or claimed in this slice. |
| OD-006 | Decide whether to support unbatched tensors and malformed `BOX_DATA` in the debugger. | The current debugger contract supports batched images and valid diagnostic boxes only. |

### Ordered next steps

1. **Authorize the integrated graph visually.** Import the child-owned artifact through the host UI and inspect geometry, green preview, diagnostic MASK, model output, and optional upscale branches.
2. **Keep style integration separate.** Do not change the fixed-pixel/router contract while adding any future style stage.

## 12. Composition research boundary

The selector is a photographic composition aid, not an inference system. Rule-of-thirds guidance commonly places important subjects near one-third lines, while the rule of space recommends leaving negative space in a subject's gaze or movement direction. This node implements only the manual two-axis 3x3 placement choice. The existing `RMBG` → `MaskBoxDetect` detector supplies a box; it does not analyze gaze, pose, or motion, so it cannot choose a horizontal or vertical position automatically. Vertical overflow is routing metadata, not movement-direction inference.

References:

- [Adobe: Rule of thirds](https://www.adobe.com/creativecloud/photography/technique/rule-of-thirds.html)
- [Digital Photography School: The rule of space in photography](https://digital-photography-school.com/rule-of-space-in-photography/)

## 13. Source index

### Current repository evidence

| Exact path | Evidence used |
|---|---|
| `nodes/smart_expected_box.py` | Fixed-pixel router inputs, outward rasterization, bounded containment search, eight output names, `BOX_DATA`, and math-only behavior. |
| `nodes/smart_crop_extend.py` | Non-stretching crop/zero-extension executor, batch handling, and outpaint mask polarity/shape. |
| `nodes/smart_expected_box_debugger.py` | Tensor conversion, batch loop, blue/red/green PIL drawing, x/y composition guides, output reconstruction, and debugger contract. |
| `web/js/tlayox_dynamic.js` | PromptBuilder labels plus the accessible SmartExpectedBox 3x3 radio grid, hidden combo synchronization, cleanup, and fallback behavior. |
| `tests/test_smart_expected_box.py` | Fully inside crop example, horizontal/vertical overflow, fixed-pixel input, all nine composition anchors, legacy aliases, safe-box containment, ratio/crop-pad invariants, metadata, direct-call compatibility, and invalid geometry assertions. |
| `tests/smart_expected_box_case_matrix.py` | Deterministic 13,122-case matrix spanning source/detected/target aspects, all nine compositions, placement, safety padding, and integer/fractional coordinates. |
| `tests/test_smart_expected_box_audit.py` | Matrix invariants, overflow/expansion diagnostics, outward fractional rasterization, extreme aspects, deterministic routing, and invalid input coverage. |
| `tests/test_smart_crop_extend.py` | All binary directional combinations, matrix-derived routes, source-pixel preservation, mask shape/polarity, batch/dtype/device handling, immutability, and invalid directions. |
| `tests/test_smart_expected_box_debugger.py` | Debugger color placement, x/y composition guides, legacy metadata compatibility, batch shape, and input immutability coverage. |
| `tests/test_frontend_contract.py` | Hostless static checks for the frontend radio-grid contract and safe API fallback. |
| `tests/test_node_registration.py` | Hostless registered class keys, display name, and fixed-pixel input coverage. |
| `tests/test_workflow_graph.py` | Hostless API/UI graph parser, deterministic generator/artifact identity check, proven external-slot checks, full link contract, and preview-path checks. |
| `__init__.py` | Imports, node class mappings, display names, and registration evidence. |
| `README.md` | Current node catalog, implemented slice behavior, generator/artifact import path, and parent workflow boundary. |
| `pyproject.toml` | Focused Ruff and pytest configuration for the independent repository. |
| `nodes/__init__.py` | Nodes subpackage marker. |
| `workflows/make_smart_expected_box_debug_workflow.py` | Authoritative deterministic UI-style graph generator; writes only its sibling JSON. |
| `workflows/smart_expected_box_debug_workflow.json` | Child-owned generated workflow artifact with positions, links, geometry preview, prepared-image preview, and mask preview. |

### Persistent project evidence

| Engram ID | Evidence preserved |
|---:|---|
| **#1569** | Prior architecture record: separate expected-box crop/pad routing mathematics from pixel editing, project the forced target aspect ratio over the original canvas, return eight mutually exclusive values, and use strict TDD as intended. |
| **#1650** | Prior debugger record: use an isolated, non-destructive `PIL.ImageDraw` visualization over ComfyUI tensors to validate safe-box/expected-box geometry before crop or outpaint. |

The durable implementation boundary is therefore: **route geometry first, inspect geometry second, prepare pixels without stretching third, and add model outpaint/upscale/style stages only as separately specified later work**.
