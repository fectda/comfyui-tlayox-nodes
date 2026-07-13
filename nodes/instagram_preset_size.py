"""Instagram Preset Size node — dropdown selector for Instagram dimensions."""

PRESETS = {
    "Stories & Reels (1080x1920 - 9:16)": (1080, 1920),
    "Feed Vertical (1080x1350 - 4:5)": (1080, 1350),
    "Feed Cuadrado (1080x1080 - 1:1)": (1080, 1080),
    "Feed Horizontal (1080x566 - 1.91:1)": (1080, 566),
    "Foto de Perfil (320x320 - 1:1)": (320, 320),
}


class InstagramPresetSize:
    """Outputs width and height based on the selected Instagram preset."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset": (list(PRESETS.keys()),),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_size"
    CATEGORY = "Tlayox/Utils"

    def get_size(self, preset):
        width, height = PRESETS[preset]
        return (width, height)
