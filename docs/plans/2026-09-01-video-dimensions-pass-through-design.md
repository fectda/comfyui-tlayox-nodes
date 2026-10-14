# Video Dimensions Pass-Through Design

## Goal

Add a Tlayox utility node that receives ComfyUI's native `VIDEO` value,
passes that same value through unchanged, and exposes its pixel width and
height as integer outputs.

## Behavior

- The node accepts exactly one required `VIDEO` input.
- The first output is the original `VIDEO` object, unchanged.
- The second and third outputs are `width` and `height` as `INT` values.
- Execution reads the native video metadata only; it does not decode frames,
  resize, copy, re-encode, or write a file.
- Invalid or missing video values fail with a clear validation/runtime error.

## Scope and isolation

- Add the node in a dedicated module under `nodes/`.
- Register it in the package's existing node mappings and display-name map.
- Add focused tests that verify the native `VIDEO` input contract, dimensions,
  and object pass-through identity.
- Do not modify existing video loaders, image conversion nodes, workflows, or
  unrelated user worktree changes.

## Verification

Run the focused node tests, the package registration tests, Python syntax and
lint checks, and confirm the implementation does not call any frame-decoding
or encoding path.
