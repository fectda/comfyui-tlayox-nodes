"""ComfyUI-Tlayox-Nodes — Custom nodes by Tlayox."""

from .nodes.instagram_preset_size import InstagramPresetSize

NODE_CLASS_MAPPINGS = {
    "InstagramPresetSize": InstagramPresetSize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "InstagramPresetSize": "📐 Instagram Preset Size",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
