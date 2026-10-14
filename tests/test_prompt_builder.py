"""Child-owned PromptBuilder regression tests.

Covers exact photography options/default, valid selection preservation,
neutral invalid-type fallback, Macro asset resolution, prompt assembly,
and the established prompt/background-color tuple shape.

No parent test imports. No Frame input, alias, or fixture.
"""

import os

import pytest

from nodes.prompt_builder import PromptBuilder

# ---------------------------------------------------------------------------
# Local constants — child-owned, not imported from parent tests
# ---------------------------------------------------------------------------
EXPECTED_PHOTO_OPTIONS = ("Macro", "Context", "Conceptual")
DEFAULT_PHOTO_TYPE = "Macro"
NEUTRAL_INVALID_SENTINEL = "UnknownType"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def builder():
    """Provide a fresh PromptBuilder instance for each test."""
    return PromptBuilder()


# ---------------------------------------------------------------------------
# Phase 1: Canonical photography options and default
# ---------------------------------------------------------------------------
class TestPhotographyOptionsAndDefault:
    """Exact option set, ordering, and default for photography type."""

    def test_input_types_exposes_correct_structure(self, builder):
        """INPUT_TYPES returns the expected ComfyUI node contract shape."""
        types = builder.INPUT_TYPES()
        assert "required" in types
        assert "Type_Photography" in types["required"]

    def test_photo_options_exactly_match(self, builder):
        """Type_Photography options are exactly Macro, Context, Conceptual."""
        types = builder.INPUT_TYPES()
        options, metadata = types["required"]["Type_Photography"]
        assert tuple(options) == EXPECTED_PHOTO_OPTIONS

    def test_macro_is_first_in_order(self, builder):
        """Macro appears first — ordering matters for UI dropdown."""
        types = builder.INPUT_TYPES()
        options = types["required"]["Type_Photography"][0]
        assert options[0] == "Macro"

    def test_default_photo_type_is_macro(self, builder):
        """Default photography type is Macro, not Context or Conceptual."""
        types = builder.INPUT_TYPES()
        _, metadata = types["required"]["Type_Photography"]
        assert metadata["default"] == DEFAULT_PHOTO_TYPE

    def test_options_count_is_exactly_three(self, builder):
        """No fourth option (e.g. Frame) exists in the dropdown."""
        types = builder.INPUT_TYPES()
        options = types["required"]["Type_Photography"][0]
        assert len(options) == 3


# ---------------------------------------------------------------------------
# Phase 1: Valid Context / Conceptual selection preservation
# ---------------------------------------------------------------------------
class TestValidSelectionPreservation:
    """Valid non-Macro photography types are preserved through build."""

    def test_context_selection_preserved(self, builder):
        """When Context is selected, the prompt contains context.md content."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Context",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        # context.md contains "35mm lens" — if resolved correctly, it appears
        assert "35mm lens" in result[0]

    def test_conceptual_selection_preserved(self, builder):
        """When Conceptual is selected, the prompt contains conceptual.md content."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Conceptual",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        # conceptual.md contains "abstract composition" — resolved correctly
        assert "abstract composition" in result[0]


# ---------------------------------------------------------------------------
# Phase 1: Neutral invalid-type fallback to Macro
# ---------------------------------------------------------------------------
class TestNeutralInvalidFallback:
    """UnknownType and unsupported values fall back to Macro."""

    def test_unknown_type_falls_back_to_macro(self, builder):
        """UnknownType resolves to Macro — no Frame behavior invoked."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography=NEUTRAL_INVALID_SENTINEL,
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        # macro.md content includes "macro lens" — confirms Macro fallback
        assert "macro lens" in result[0]

    def test_empty_string_falls_back_to_macro(self, builder):
        """Empty string triggers Macro fallback."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        assert "macro lens" in result[0]

    def test_numeric_input_falls_back_to_macro(self, builder):
        """Non-string unexpected input triggers Macro fallback."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography=42,
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        assert "macro lens" in result[0]


# ---------------------------------------------------------------------------
# Phase 1: Macro asset resolution via prompts/type/macro.md
# ---------------------------------------------------------------------------
class TestMacroAssetResolution:
    """Macro prompt resolves prompts/type/macro.md content."""

    def test_macro_resolves_correct_asset(self, builder):
        """Macro build reads prompts/type/macro.md content."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert len(result) == 2
        # macro.md content: "Extreme forensic close-up, shot on 100mm macro lens"
        assert "Extreme forensic close-up" in result[0]
        assert "100mm macro lens" in result[0]

    def test_macro_type_text_differs_from_context(self, builder):
        """Macro produces different type text than Context."""
        macro_result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="test",
        )
        context_result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Context",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="test",
        )
        assert macro_result[0] != context_result[0]
        assert "macro lens" in macro_result[0]
        assert "35mm lens" in context_result[0]


# ---------------------------------------------------------------------------
# Phase 1: Deterministic prompt assembly and two-string tuple shape
# ---------------------------------------------------------------------------
class TestPromptAssemblyAndTupleShape:
    """Prompt assembly joins parts correctly; return is a two-string tuple."""

    def test_returns_prompt_and_background_color_tuple(self, builder):
        """build_prompt returns prompt and background color strings."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(value, str) for value in result)

    def test_visual_prompt_included_in_assembly(self, builder):
        """User Visual_Prompt is included in the assembled prompt."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="detailed close-up of gears",
        )
        assert "detailed close-up of gears" in result[0]

    def test_assembly_order_base_then_type(self, builder):
        """Base text appears before type text in assembled prompt."""
        result = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="",
        )
        prompt = result[0]
        # photography.md base content comes before macro.md type content
        base_pos = prompt.find("photography") if "photography" in prompt.lower() else 0
        type_pos = prompt.find("macro lens")
        assert type_pos > base_pos

    def test_whitespace_only_visual_prompt_excluded(self, builder):
        """Whitespace-only Visual_Prompt is stripped from the assembly."""
        result_with = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="specific_marker_xyz",
        )
        result_without = builder.build_prompt(
            Base_Format="Photography",
            Type_Photography="Macro",
            Brand="Tlayox",
            Atmosphere_Tlayox="1- Tlayox",
            Atmosphere_Altepetl="Ambar",
            Atmosphere_Otra="",
            Visual_Prompt="   ",
        )
        assert "specific_marker_xyz" in result_with[0]
        assert "specific_marker_xyz" not in result_without[0]

    def test_read_prompt_file_returns_stripped_content(self, builder):
        """read_prompt_file strips leading/trailing whitespace from file content."""
        # macro.md has content; verify it's read and stripped
        node_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        expected_path = os.path.join(node_dir, "prompts", "type", "macro.md")
        assert os.path.exists(expected_path)
        content = builder.read_prompt_file("type", "macro.md")
        assert content == content.strip()
        assert len(content) > 0


# ---------------------------------------------------------------------------
# Phase 3: Missing Macro asset auto-creation and empty-string return
# ---------------------------------------------------------------------------
class TestMissingMacroAssetBehavior:
    """Missing Markdown asset is auto-created empty and returns ''.

    Characterization test — documents the existing read_prompt_file contract
    for missing assets: the file is created as zero bytes and the method
    returns an empty string.  Uses isolated tmp_path to avoid touching the
    real prompts/ directory.
    """

    def test_missing_asset_creates_empty_file_and_returns_empty_string(self, builder, monkeypatch, tmp_path):
        """Missing asset in isolated location is created empty; return is ''."""
        fake_module_file = tmp_path / "nodes" / "prompt_builder.py"
        fake_module_file.parent.mkdir(parents=True)
        fake_module_file.write_text("# placeholder\n")
        monkeypatch.setattr("nodes.prompt_builder.__file__", str(fake_module_file))

        result = builder.read_prompt_file("type", "macro.md")

        asset_path = tmp_path / "prompts" / "type" / "macro.md"
        assert asset_path.exists(), "missing asset should be auto-created"
        assert asset_path.stat().st_size == 0, "auto-created file must be zero bytes"
        assert result == "", "missing asset must return empty string"

    def test_missing_asset_different_path_same_behavior(self, builder, monkeypatch, tmp_path):
        """Same auto-create-and-return-empty contract for a different path."""
        fake_module_file = tmp_path / "nodes" / "prompt_builder.py"
        fake_module_file.parent.mkdir(parents=True)
        fake_module_file.write_text("# placeholder\n")
        monkeypatch.setattr("nodes.prompt_builder.__file__", str(fake_module_file))

        result = builder.read_prompt_file("type", "nonexistent_type.md")

        asset_path = tmp_path / "prompts" / "type" / "nonexistent_type.md"
        assert asset_path.exists(), "missing asset should be auto-created"
        assert asset_path.stat().st_size == 0, "auto-created file must be zero bytes"
        assert result == "", "missing asset must return empty string"
