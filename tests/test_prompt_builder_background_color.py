"""Focused PromptBuilder background-color contract tests."""

from pathlib import Path

import pytest

from nodes.prompt_builder import PromptBuilder

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = REPOSITORY_ROOT / "web/js/prompt_builder_background_color.js"


@pytest.fixture
def builder():
    """Provide a fresh PromptBuilder instance for each test."""
    return PromptBuilder()


def _build_prompt(builder, *, brand="Tlayox", custom_color=""):
    return builder.build_prompt(
        Base_Format="Photography",
        Type_Photography="Macro",
        Brand=brand,
        Atmosphere_Tlayox="1- Tlayox",
        Atmosphere_Altepetl="Ambar",
        Atmosphere_Otra="",
        Visual_Prompt="",
        Background_Color_Otra=custom_color,
    )


def test_prompt_builder_exposes_background_color_input_and_output(builder):
    """The node exposes the custom input and named second output."""
    input_types = builder.INPUT_TYPES()["required"]

    assert input_types["Background_Color_Otra"] == ("STRING", {"default": ""})
    assert builder.RETURN_TYPES == ("STRING", "COLORCODE")
    assert builder.RETURN_NAMES == ("text", "background_color")


@pytest.mark.parametrize(
    ("brand", "expected"),
    [
        ("Altepetl", "#050505"),
        ("Tlayox", "#FDFEFE"),
    ],
)
def test_prompt_builder_returns_brand_background_color(builder, brand, expected):
    """Known brands return their fixed background colors."""
    result = _build_prompt(builder, brand=brand, custom_color="#abcdef")

    assert result[1] == expected


@pytest.mark.parametrize(
    ("custom_color", "expected"),
    [
        ("#abcdef", "#ABCDEF"),
        ("abcdef", "#ABCDEF"),
        ("  #a1b2c3  ", "#A1B2C3"),
    ],
)
def test_prompt_builder_normalizes_custom_background_color(builder, custom_color, expected):
    """Otra accepts six hexadecimal digits and normalizes the result."""
    result = _build_prompt(builder, brand="Otra", custom_color=custom_color)

    assert result[1] == expected


@pytest.mark.parametrize(
    "custom_color",
    ["", "   ", "#12345", "#1234567", "#GGGGGG", "red", None, 123456],
)
def test_prompt_builder_invalid_custom_background_color_uses_fallback(builder, custom_color):
    """Blank and invalid Otra values use the white fallback."""
    result = _build_prompt(builder, brand="Otra", custom_color=custom_color)

    assert result[1] == "#FFFFFF"


def test_prompt_builder_background_color_does_not_change_prompt_assembly(builder):
    """The original prompt output remains unchanged by the new output."""
    without_custom_color = _build_prompt(builder, brand="Tlayox")
    with_custom_color = _build_prompt(builder, brand="Tlayox", custom_color="#123456")

    assert with_custom_color[0] == without_custom_color[0]


def test_frontend_contract_hides_custom_input_unless_brand_is_otra():
    """The separate frontend extension follows the Atmosphere_Otra visibility rule."""
    source = FRONTEND_PATH.read_text(encoding="utf-8")

    assert 'name: "Tlayox.PromptBuilderBackgroundColor"' in source
    assert 'if (node.comfyClass !== "PromptBuilder") return;' in source
    assert 'const BACKGROUND_COLOR_WIDGET_NAME = "Background_Color_Otra";' in source
    assert 'if (brandWidget.value === "Otra")' in source
    assert "showWidget(backgroundColorWidget);" in source
    assert "hideWidget(backgroundColorWidget);" in source
    assert "async afterConfigureGraph()" in source
    assert "async nodeCreated(node)" in source
