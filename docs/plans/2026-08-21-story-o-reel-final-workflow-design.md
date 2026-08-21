# Story O Reel Final Workflow Design

The approved final workflow is a new, flattened workflow that preserves the parent force-style input and prompt contracts, prepares a clean square-ready image, applies the retained style subgraph, and produces an exact preset-sized file. Source workflows remain untouched. Final implementation must be delegated separately.

## Goal

Define the production graph for the final Story O Reel workflow without carrying forward the legacy outer wrapper, duplicate outpaint path, or diagnostic-only image overlay. The graph must keep the original image available for prompt generation while sending only the clean prepared image into the style path.

## Context

The parent inputs come from `/home/fectda/code/comfyui/user/default/workflows/story_o_reel-forzar_estilo .json`. Preserve the source image, primary seed, filename prefix, and `InstagramPresetSize`, with the initial preset set to `Feed Cuadrado (1080x1080)`. Preserve the prompt chain:

```text
Text Multiline -> TextGenerate (gemma4) -> PreviewAny -> PromptBuilder -> PreviewAny
```

The retained style implementation is the inner subgraph definition `12086ad5-61c4-4ee7-868a-12d3b4035c96`, named `extiende la imagen y ya sale cuadrada`.

## Non-goals

- Do not modify the parent source workflow or any existing source/child workflow.
- Do not retain the outer `New Subgraph` instance or definition.
- Do not copy the legacy `fd81eb59-7179-4535-bb32-3a6893b83b54` UUID; parent and child definitions conflict.
- Do not retain the legacy `fd81...` outpaint path, old background color, or secondary seed.
- Do not add an external `ImageScaleToTotalPixels` or `MegapixelCalculator`.
- Do not use the green diagnostic overlay as the production image input.

## Proposed data flow

The production preprocessing path is exactly:

```text
raw image
  -> GetImageSizeAndCount
  -> RMBG
  -> MaskBoxDetect
  -> SmartExpectedBox
  -> SmartCropExtend (crop-only; all pad widgets zero)
  -> ImagePadForOutpaint (feathering=40)
  -> retained style subgraph
  -> ImageResizeKJv2 (method=nvidia_rtx_vsr)
  -> ImageResizeKJv2 (method=lanczos)
  -> SaveImage
```

Only the clean `ImagePadForOutpaint` `IMAGE` output feeds the style subgraph. The prompt `STRING` still comes from the original-image `TextGenerate` chain; it must not be regenerated from the cropped or padded image. Both final resize nodes receive the exact width and height from `InstagramPresetSize`. The second Lanczos node is the exact-size correction for any VSR dimension rounding.

The style subgraph's single megapixels contract is `1.0`. Its internal path therefore owns the approximately 1 MP resize; no external megapixel calculation or total-pixel resize is permitted. `SmartCropExtend` performs cropping only, so `ImagePadForOutpaint` remains the sole padding operation and applies feathering at `40`.

## Node/subgraph ownership

| Owner | Responsibility |
| --- | --- |
| Parent contract | Original image, primary seed, filename prefix, `InstagramPresetSize`, and the original-image prompt chain. |
| Production preprocessing | `GetImageSizeAndCount`, `RMBG`, `MaskBoxDetect`, `SmartExpectedBox`, crop-only `SmartCropExtend`, and feathered `ImagePadForOutpaint`. |
| Retained style subgraph | Definition `12086ad5-61c4-4ee7-868a-12d3b4035c96`; consumes clean prepared `IMAGE`, original prompt `STRING`, and `megapixels=1.0`. |
| Final output | Two preset-driven `ImageResizeKJv2` nodes in VSR-then-Lanczos order, followed by `SaveImage`. |

The outer `New Subgraph` is removed rather than nested again. Legacy outpaint inputs, background configuration, and secondary seed are not recreated in the flattened graph.

## ID/UUID strategy

- Allocate new top-level node IDs `196–204`.
- Allocate new top-level link IDs `382–409`.
- Preserve the retained nested subgraph IDs and scopes exactly.
- Preserve the retained style UUID `12086ad5-61c4-4ee7-868a-12d3b4035c96`.
- Omit `fd81eb59-7179-4535-bb32-3a6893b83b54` entirely to prevent the parent/child definition collision.
- Do not renumber or mutate IDs belonging to the preserved parent prompt/input contract or the retained nested style definition.

## Runtime dependencies

The host must provide the existing preprocessing nodes, the retained style subgraph dependencies, and KJNodes `ImageResizeKJv2`. The `nvidia_rtx_vsr` resize additionally requires an available NVIDIA VSR/NVVFX backend (`nvvfx`) and compatible CUDA/GPU runtime. Lanczos remains the deterministic exact-dimension correction, but it does not remove the VSR prerequisite from the first resize stage.

## Validation criteria

- Confirm the source workflow files are unchanged and the final workflow is new.
- Confirm the initial preset is exactly `Feed Cuadrado (1080x1080)` and every preset's aspect ratio is preserved.
- Confirm the source image, primary seed, filename prefix, and complete original-image prompt chain remain connected.
- Confirm the production image connection is clean `ImagePadForOutpaint IMAGE -> style IMAGE`, not a green diagnostic overlay.
- Confirm `SmartCropExtend` has zero padding and `ImagePadForOutpaint` is the only padding node, with feathering `40`; there is no duplicate padding.
- Confirm no external `ImageScaleToTotalPixels` or `MegapixelCalculator` exists and the style subgraph receives `megapixels=1.0`.
- Confirm the outer `New Subgraph`, legacy `fd81...` path, old background color, and secondary seed are absent, with no UUID collision.
- Confirm top-level IDs are within `196–204`, links are within `382–409`, and nested IDs/scopes are preserved.
- Confirm both `ImageResizeKJv2` nodes receive the exact preset width and height, in `nvidia_rtx_vsr` then `lanczos` order.
- Confirm final dimensions exactly match the selected preset after VSR rounding, and verify VSR/NVVFX availability before runtime execution.

## Rollback/safety

Implement the workflow as a separate artifact derived from the parent inputs. If validation fails, discard or revert only that new final workflow; restore it from the untouched parent source rather than editing the source or retained child definitions. Do not proceed to implementation, source synchronization, or runtime changes as part of this design document; final implementation must be delegated separately.
