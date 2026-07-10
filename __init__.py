"""ComfyUI-Tlayox-Nodes — Custom nodes by Tlayox."""

from .nodes.center_align_calculator import CenterAlignCalculator
from .nodes.fit_size_calculator import FitSizeCalculator
from .nodes.instagram_preset_size import InstagramPresetSize
from .nodes.max_side import MaxSide
from .nodes.megapixel_calculator import MegapixelCalculator

from .nodes.text_switch_4 import TextSwitch4

NODE_CLASS_MAPPINGS = {
    "InstagramPresetSize": InstagramPresetSize,
    "FitSizeCalculator": FitSizeCalculator,
    "CenterAlignCalculator": CenterAlignCalculator,
    "MegapixelCalculator": MegapixelCalculator,
    "MaxSide": MaxSide,
    "TextSwitch4": TextSwitch4,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InstagramPresetSize": "📐 Instagram Preset Size",
    "FitSizeCalculator": "📏 Fit Size Calculator",
    "CenterAlignCalculator": "🎯 Center Align Calculator",
    "MegapixelCalculator": "🔢 Megapixel Calculator",
    "MaxSide": "📊 Max Side",
    "TextSwitch4": "🎨 Tlayox Styles Selector",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]



