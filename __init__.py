"""ComfyUI-Tlayox-Nodes — Custom nodes by Tlayox."""

from .nodes.center_align_calculator import CenterAlignCalculator
from .nodes.fit_size_calculator import FitSizeCalculator
from .nodes.instagram_preset_size import InstagramPresetSize

NODE_CLASS_MAPPINGS = {
    "InstagramPresetSize": InstagramPresetSize,
    "FitSizeCalculator": FitSizeCalculator,
    "CenterAlignCalculator": CenterAlignCalculator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InstagramPresetSize": "📐 Instagram Preset Size",
    "FitSizeCalculator": "📏 Fit Size Calculator",
    "CenterAlignCalculator": "🎯 Center Align Calculator",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

