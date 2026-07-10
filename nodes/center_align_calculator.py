"""Center Align Calculator — computes offsets to center an image within target dimensions."""


class CenterAlignCalculator:
    """Returns the x/y offsets needed to center an image within a target canvas."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "new_width": ("INT", {"default": 1080, "min": 1}),
                "new_height": ("INT", {"default": 1920, "min": 1}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width_align", "height_align")
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Utils"

    def calculate(self, image, new_width, new_height):
        # IMAGE tensor shape: [batch, height, width, channels]
        img_height = image.shape[1]
        img_width = image.shape[2]
        width_align = int((new_width - img_width) / 2)
        height_align = int((new_height - img_height) / 2)
        return (width_align, height_align)
