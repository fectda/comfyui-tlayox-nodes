"""Hostless static contract checks for the ComfyUI frontend extension."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = REPOSITORY_ROOT / "web/js/tlayox_dynamic.js"
SMART_EXPECTED_BOX_PATH = REPOSITORY_ROOT / "nodes/smart_expected_box.py"
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


def test_frontend_contract_does_not_install_smart_expected_box_radio_grid():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert "app.registerExtension({" in source
    assert "SmartExpectedBox" not in source
    assert "addDOMWidget" not in source
    assert "tlayoxCompositionGrid" not in source
    assert 'radio.type = "radio"' not in source
    assert 'role = "radiogroup"' not in source


def test_frontend_contract_preserves_native_composition_combo():
    frontend_source = FRONTEND_PATH.read_text(encoding="utf-8")
    node_source = SMART_EXPECTED_BOX_PATH.read_text(encoding="utf-8")

    for position in CANONICAL_POSITIONS:
        assert f'"{position}"' in node_source

    assert '"composition": (list(_COMPOSITION_ANCHORS), {"default": "center"}),' in node_source
    assert '"Center": "center"' in node_source
    assert '"Left": "center_left"' in node_source
    assert '"Right": "center_right"' in node_source
    assert '"composition"' not in frontend_source


def test_frontend_contract_preserves_prompt_builder_registration_and_lifecycle():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert 'name: "Tlayox.Dynamic"' in source
    assert "afterConfigureGraph()" in source
    assert "nodeCreated(node)" in source
    assert 'if (node.comfyClass !== "PromptBuilder") continue;' in source
    assert 'if (node.comfyClass !== "PromptBuilder") return;' in source


def test_frontend_contract_preserves_prompt_builder_visibility_and_resize_behavior():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert "const hideWidget = (w) =>" in source
    assert "const showWidget = (w) =>" in source
    assert "const updateVisibility = () =>" in source
    assert "const recomputeSize = () =>" in source
    assert "Math.max(node.size[0], 300)" in source
    assert "Math.max(node.size[1], neededH)" in source
    assert 'for (const wName of ["Base_Format", "Brand"])' in source
    assert "updateVisibility();" in source


def test_frontend_contract_preserves_prompt_builder_label_behavior():
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    for field, label in (
        ("Visual_Prompt", "Visual Prompt"),
        ("Atmosphere_Otra", "Atmosphere"),
        ("Atmosphere_Tlayox", "Atmosphere"),
        ("Atmosphere_Altepetl", "Atmosphere"),
        ("Base_Format", "Base Format"),
        ("Type_Photography", "Type"),
    ):
        assert f'"{field}": "{label}"' in source

    assert "w.label = cleanName;" in source
    assert "applyLabels();" in source
