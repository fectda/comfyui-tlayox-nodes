# SmartExpectedBox Outpaint Preparation Design

## Goal

Integrate the existing ComfyUI outpaint preparation pattern into the SmartExpectedBox workflow so all foreground subjects remain in the focus box, the generated extension is previewed as a feathered green region, the model input is resized to a usable image size, and the final output matches the selected preset dimensions exactly.

## Confirmed semantics

The mask is an intermediate compositing/visualization artifact. It is blurred by `ImagePadForOutpaint` through its feathering parameter and consumed by `DrawMaskOnImage` to blend the green preview into the source image. The outpaint model receives the prepared image only; the raw `MASK` is retained for diagnostics and must not be treated as a model input.

## Proposed data flow

```text
SmartExpectedBox geometry
  -> existing crop operation (using SmartExpectedBox crop distances)
  -> ImagePadForOutpaint (router pad values, feathering=40)
  -> prepared IMAGE + feathered MASK
  -> DrawMaskOnImage (green: 0,255,0)
  -> ImageScaleToTotalPixels (~1 MP)
  -> existing "extiende la imagen y ya sale cuadrada" block
  -> ImageResizeKJv2 (preset width/height, NVIDIA RTX VSR, CPU device)
  -> ImageResizeKJv2 (preset width/height, Lanczos, CPU device, exact correction)
```

The crop and pad responsibilities remain separate without introducing a new custom node. Prefer the installed host crop node with dynamic crop values. If this ComfyUI build cannot expose those values as links, reuse the existing `SmartCropExtend` node in crop-only mode by setting its pad inputs to zero, then let `ImagePadForOutpaint` perform the only padding operation. The workflow path must never apply the same padding twice.

## Focus-box policy

`LayerMask: MaskBoxDetect` must use `mask_area`, not `min_bounding_rect`. The latter selects only the largest connected contour and can discard separate foreground subjects. `mask_area` encloses every foreground pixel in the segmentation mask, preserving multi-subject compositions.

## Output-size policy

The deterministic resize to approximately 1 MP happens before the existing outpaint block. The outpaint result then passes through the installed KJNodes `ImageResizeKJv2` node with `width` and `height` linked directly to `InstagramPresetSize` slots 0 and 1, `upscale_method=nvidia_rtx_vsr`, `keep_proportion=stretch`, `divisible_by=1`, and `device=cpu`. The VSR backend rounds its internal output dimensions to multiples of 8, so a second `ImageResizeKJv2` using `upscale_method=lanczos`, the same direct preset links, `keep_proportion=stretch`, `divisible_by=1`, and `device=cpu` restores exact dimensions. `RealESRGAN_x4plus` is not part of the main output path.

### Exact-size correction validation

The VSR alignment check covers every `InstagramPresetSize` target:

| Preset dimensions | RTX VSR internal dimensions | Final correction |
| --- | --- | --- |
| `1080x1920` | `1080x1920` | `1080x1920` |
| `1080x1350` | `1080x1352` | `1080x1350` |
| `1080x1080` | `1080x1080` | `1080x1080` |
| `1080x566` | `1080x568` | `1080x566` |
| `320x320` | `320x320` | `320x320` |

The correction node is therefore intentional rather than a model upscale: it is required for the two presets whose height is not divisible by 8 and remains a no-op in dimensions for the other three presets.

## Frontend layout policy

The SmartExpectedBox node must reserve enough height for the nine-position DOM radio grid. The generated node size and the frontend DOM-widget setup both enforce a minimum layout height so the grid remains inside the node.

## Scope

- Use existing host nodes for cropping; do not add a new custom crop node.
- Set `MaskBoxDetect` to `mask_area` so disconnected foreground subjects share one focus box.
- Add `ImagePadForOutpaint` and `DrawMaskOnImage` to the generated workflow with feathering set to 40.
- Preserve the raw mask as a diagnostic output while sending only the prepared image to the outpaint block.
- Add the ~1 MP resize before the outpaint block.
- Add `ImageResizeKJv2` using the selected preset width/height, `nvidia_rtx_vsr`, and CPU device, followed by exact-size correction where VSR alignment requires it; do not use fixed-factor RealESRGAN as the main output scaler.
- Reserve enough node height for the frontend radio grid.
- Synchronize the parent workflow only after the child generator and graph tests are correct.

## Out of scope

- Replacing the current outpaint model with a mask-aware sampler.
- Changing SmartExpectedBox geometry, target-ratio semantics, or the existing `SmartCropExtend` contract.
- Downloading or wiring a model-based upscale into the main output before a baseline comparison.

## Validation

- Unit-test crop-only behavior and boundary cases.
- Assert graph presence, ordering, connections, feathering value, green preview configuration, and preservation of the diagnostic mask.
- Assert `MaskBoxDetect` uses `mask_area`.
- Assert the outpaint block receives the resized prepared image, not the raw source or raw mask.
- Assert `ImageResizeKJv2` receives width and height from `InstagramPresetSize`, uses `nvidia_rtx_vsr` and CPU, and that the final correction preserves exact preset dimensions.
- Assert the SmartExpectedBox node and DOM grid reserve sufficient height.
- Run the existing Python test suite, Ruff, workflow determinism checks, and `git diff --check`.
- Perform a live ComfyUI smoke test only after hostless validation passes.
