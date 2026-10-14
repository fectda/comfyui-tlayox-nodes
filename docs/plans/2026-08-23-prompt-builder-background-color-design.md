# PromptBuilder Background Color Design

## Goal

Add a second `COLORCODE` output to `PromptBuilder` whose payload is the
background-color hexadecimal string associated with the selected brand, while
keeping the existing prompt output unchanged.

## Behavior

- `Altepetl` returns `#050505` (obsidian black).
- `Tlayox` returns `#FDFEFE` (Tlayox interface white).
- `Otra` displays a custom hexadecimal input and returns its normalized value.
- The custom input is visible only for `Otra`, matching the existing
  `Atmosphere_Otra` visibility behavior.
- Empty or invalid custom values fall back to `#FFFFFF`.

## Scope and isolation

- Add the backend input, output, and resolution logic to `nodes/prompt_builder.py`.
- Add a separate frontend extension for the new widget so the concurrently
  modified `web/js/tlayox_dynamic.js` remains untouched.
- Add focused regression coverage in a new test file so the concurrently
  modified `tests/test_frontend_contract.py` remains untouched.
- Do not change prompt assembly, existing inputs, workflow files, or unrelated
  frontend behavior.

## Verification

Run the focused PromptBuilder tests, the new frontend contract tests, Python
syntax checks, and JavaScript syntax checks. Confirm the final diff contains
only the approved design artifact and background-color implementation files;
preserve all pre-existing concurrent worktree modifications.
