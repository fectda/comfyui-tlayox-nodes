"""Max Side — returns the longest side of an image."""


class MaxSide:
    """Returns the longest side of an image as an integer."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("max_side",)
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Utils"

    def calculate(self, image):
        # IMAGE tensor shape: [batch, height, width, channels]
        img_height = image.shape[1]
        img_width = image.shape[2]
        return (max(img_width, img_height),)
