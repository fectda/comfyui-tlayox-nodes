# Contributing

This repository contains the Tlayox custom nodes and their prompt assets as an independent Git project. ComfyUI is the runtime host, not the repository being changed.

## Quick path

Run these commands from `/home/fectda/code/comfyui/custom_nodes/ComfyUI-Tlayox-Nodes` or another clone of this repository:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_smart_expected_box.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_smart_expected_box_debugger.py
ruff check .
ruff format --check .
```

The default test command uses the repository's pytest boundary and should pass without collecting the root package as a test module.

## Repository boundary

- Run Git commands from this child repository, never from the parent ComfyUI checkout.
- Keep the parent checkout as the runtime host; do not copy these files into it or mix its Git history with this repository.
- Use the ComfyUI installation's existing Python environment and runtime dependencies. This repository does not define a separate package-installation contract.
- The Ruff configuration targets Python 3.10 syntax; that tooling setting is not a claim about a separate package distribution.

## Quality gates

Ruff checks are non-destructive:

- `ruff check .` checks lint rules without `--fix`.
- `ruff format --check .` checks formatting without rewriting files.
- `pre-commit install` is optional. Its configured gates select staged Python, PYI, and notebook files and run check-only Ruff hooks; they do not format, autofix, or stage files.

## Node and prompt changes

- Keep node behavior, inputs, outputs, and runtime assumptions explicit. Add or update focused tests when deterministic behavior changes.
- Keep prompt edits scoped to the intended asset and preserve the format expected by the prompt builder. Update the node catalog or verification notes when user-visible behavior changes.
- If a change depends on a specific ComfyUI version, host node, optional dependency, or custom runtime feature, report that dependency as an unsupported runtime assumption instead of silently treating it as portable.
- The `Frame` prompt contract is out of scope for this repository baseline. Do not document or claim Frame support without a separate approved contract.

## Reporting

When reporting a problem, include the child-repository commit, ComfyUI/runtime version, Python version, focused command, and the smallest reproducible node or prompt input. State any unsupported runtime assumptions explicitly.
