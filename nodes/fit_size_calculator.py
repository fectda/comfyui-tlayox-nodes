"""Fit Size Calculator — computes the longest side after aspect-ratio-preserving fit."""


class FitSizeCalculator:
    """Returns the longest side of an image scaled to fit within target dimensions."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "img_width": ("INT", {"default": 1024, "min": 1}),
                "img_height": ("INT", {"default": 1024, "min": 1}),
                "new_width": ("INT", {"default": 1080, "min": 1}),
                "new_height": ("INT", {"default": 1920, "min": 1}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("fit_size",)
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Utils"

    def calculate(self, img_width, img_height, new_width, new_height):
        fit_size = int(
            max(img_width, img_height)
            * min(new_height / img_height, new_width / img_width)
        )
        return (fit_size,)
