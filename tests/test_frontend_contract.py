"""Hostless static contract checks for the ComfyUI frontend extension."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = REPOSITORY_ROOT / "web/js/tlayox_dynamic.js"
CANONICAL_POSITIONS = (
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)


def test_frontend_contract_uses_registered_dom_radio_grid_with_hidden_serialized_widget():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert "app.registerExtension({" in source
    assert "node.addDOMWidget(" in source
    assert 'radio.type = "radio"' in source
    assert 'role = "radiogroup"' in source
    assert "compositionWidget._tlHidden" in source
    assert "domWidget.serialize = false" in source
    assert "domWidget.options.serialize = false" in source
    assert "domWidget.onRemove" in source


def test_frontend_contract_declares_canonical_positions_and_legacy_aliases():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    for position in CANONICAL_POSITIONS:
        assert f'"{position}"' in source

    assert '"Center": "center"' in source
    assert '"Left": "center_left"' in source
    assert '"Right": "center_right"' in source
    assert '"SmartExpectedBox"' in source
    assert '"PromptBuilder"' in source


def test_frontend_contract_has_reconfiguration_guard_and_api_fallback():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert "node._tlayoxCompositionGrid" in source
    assert 'typeof node.addDOMWidget !== "function"' in source
    assert "afterConfigureGraph()" in source
    assert "nodeCreated(node)" in source


def test_frontend_contract_reserves_grid_height_without_shrinking_user_sized_nodes():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert "const COMPOSITION_GRID_MIN_SIZE = [330, 450];" in source
    assert "const ensureCompositionGridSize = (node) =>" in source
    assert "Math.max(width, COMPOSITION_GRID_MIN_SIZE[0])" in source
    assert "Math.max(height, COMPOSITION_GRID_MIN_SIZE[1])" in source
    assert "ensureCompositionGridSize(node);" in source


def test_frontend_contract_renders_visible_composition_labels_with_readable_layout():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    for label in (
        "Top left",
        "Top center",
        "Top right",
        "Center left",
        "Center",
        "Center right",
        "Bottom left",
        "Bottom center",
        "Bottom right",
    ):
        assert f'"{label}"' in source

    assert 'const labelText = document.createElement("span");' in source
    assert "labelText.textContent = readableLabel;" in source
    assert "label.append(radio, labelText);" in source
    assert 'labelText.style.fontFamily = "sans-serif";' in source
    assert 'labelText.style.fontSize = "12px";' in source
    assert 'labelText.style.lineHeight = "1.2";' in source
    assert 'labelText.style.flex = "1 1 0";' in source
    assert 'labelText.style.whiteSpace = "normal";' in source
    assert 'labelText.style.overflowWrap = "anywhere";' in source
    assert 'labelText.textContent = "●"' not in source
