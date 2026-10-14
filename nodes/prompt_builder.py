import os
import re

_BACKGROUND_COLOR_PATTERN = re.compile(r"^#?([0-9a-fA-F]{6})$")
_DEFAULT_BACKGROUND_COLOR = "#FFFFFF"


class PromptBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Base_Format": (
                    ["Photography", "Screenshot"],
                    {"default": "Photography"},
                ),
                "Type_Photography": (
                    ["Macro", "Context", "Conceptual"],
                    {"default": "Macro"},
                ),
                "Brand": (["Tlayox", "Altepetl", "Otra"], {"default": "Tlayox"}),
                "Atmosphere_Tlayox": (
                    ["1- Tlayox", "2- Memories", "3- Woodworkers", "4- Cookie Cuters"],
                    {"default": "1- Tlayox"},
                ),
                "Atmosphere_Altepetl": (
                    ["Ambar", "Turquoise", "Red"],
                    {"default": "Ambar"},
                ),
                "Atmosphere_Otra": ("STRING", {"multiline": True, "default": ""}),
                "Visual_Prompt": ("STRING", {"multiline": True, "default": ""}),
                "Background_Color_Otra": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "COLORCODE")
    RETURN_NAMES = ("text", "background_color")
    FUNCTION = "build_prompt"
    CATEGORY = "Tlayox"

    def read_prompt_file(self, *path_parts):
        node_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        file_path = os.path.join(node_dir, "prompts", *path_parts)

        try:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("")

            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"[PromptBuilder] Error reading/creating {file_path}: {e}")
        return ""

    def build_prompt(
        self,
        Base_Format,
        Type_Photography,
        Brand,
        Atmosphere_Tlayox,
        Atmosphere_Altepetl,
        Atmosphere_Otra,
        Visual_Prompt,
        Background_Color_Otra="",
        **kwargs,
    ):
        # Fallback validation for Base_Format
        if Base_Format not in ["Photography", "Screenshot"]:
            Base_Format = "Photography"

        # Fallback validation for Brand
        if Brand not in ["Tlayox", "Altepetl", "Otra"]:
            Brand = "Tlayox"

        # 1. Base
        base_file = "photography.md" if Base_Format == "Photography" else "screenshot.md"
        base_text = self.read_prompt_file("base", base_file)

        # 2. Type
        if Base_Format == "Photography":
            type_map = {
                "Macro": "macro.md",
                "Context": "context.md",
                "Conceptual": "conceptual.md",
            }
            if Type_Photography not in type_map:
                Type_Photography = "Macro"
            type_file = type_map[Type_Photography]
        else:
            type_file = "screenshot.md"

        type_text = self.read_prompt_file("type", type_file)

        # 3 & 4. Atmosphere
        if Brand == "Tlayox":
            atmos_map = {
                "1- Tlayox": "1_tlayox.md",
                "2- Memories": "2_memories.md",
                "3- Woodworkers": "3_woodworkers.md",
                "4- Cookie Cuters": "4_cookie_cuters.md",
            }
            if Atmosphere_Tlayox not in atmos_map:
                Atmosphere_Tlayox = "1- Tlayox"
            atmos_file = atmos_map[Atmosphere_Tlayox]
            atmos_text = self.read_prompt_file("atmosphere", "tlayox", atmos_file)
        elif Brand == "Altepetl":
            atmos_map = {
                "Ambar": "ambar.md",
                "Turquoise": "turquoise.md",
                "Red": "red.md",
            }
            if Atmosphere_Altepetl not in atmos_map:
                Atmosphere_Altepetl = "Ambar"
            atmos_file = atmos_map[Atmosphere_Altepetl]
            atmos_text = self.read_prompt_file("atmosphere", "altepetl", atmos_file)
        else:
            # Brand == "Otra" -> Use string directly
            atmos_text = Atmosphere_Otra.strip() if Atmosphere_Otra else ""

        # 5. Quality (always read from quality.md)
        quality_text = self.read_prompt_file("quality", "quality.md")

        # Build final string
        visual_cleaned = Visual_Prompt.strip() if Visual_Prompt else ""
        parts = [base_text, type_text, visual_cleaned, atmos_text, quality_text]
        final_prompt = " ".join([p for p in parts if p])
        background_color = self._resolve_background_color(Brand, Background_Color_Otra)

        return (final_prompt, background_color)

    @staticmethod
    def _normalize_background_color(value):
        if not isinstance(value, str):
            return _DEFAULT_BACKGROUND_COLOR

        match = _BACKGROUND_COLOR_PATTERN.fullmatch(value.strip())
        if not match:
            return _DEFAULT_BACKGROUND_COLOR

        return f"#{match.group(1).upper()}"

    def _resolve_background_color(self, brand, custom_color):
        if brand == "Altepetl":
            return "#050505"
        if brand == "Otra":
            return self._normalize_background_color(custom_color)
        return "#FDFEFE"
