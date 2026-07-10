"""Max Side — returns the larger of two dimensions."""


class MaxSide:
    """Returns the maximum of two integer values."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "new_width": ("INT", {"default": 1080, "min": 1}),
                "new_height": ("INT", {"default": 1920, "min": 1}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("max_side",)
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Utils"

    def calculate(self, new_width, new_height):
        return (max(new_width, new_height),)
