"""Megapixel Calculator — computes megapixels from width and height."""


class MegapixelCalculator:
    """Returns the megapixel count for given dimensions."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1080, "min": 1}),
                "height": ("INT", {"default": 1920, "min": 1}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("megapixels",)
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Utils"

    def calculate(self, width, height):
        megapixels = (width * height) / 1_000_000
        return (megapixels,)
