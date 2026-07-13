class TextCombiner8Views:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True}),
                "joiner": (["-", "_", " ", ", ", "."], {"default": "_"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "top_view",
        "45_left_view",
        "front_view",
        "45_right_view",
        "90_right_view",
        "90_left_view",
        "back_view",
        "bottom_view",
    )
    FUNCTION = "combine"
    CATEGORY = "Tlayox"

    def combine(self, text_input, joiner):
        suffixes = [
            "top_view",
            "45_left_view",
            "front_view",
            "45_right_view",
            "90_right_view",
            "90_left_view",
            "back_view",
            "bottom_view",
        ]

        # If input is empty, maybe don't add joiner?
        # The logic is just text_input + joiner + suffix
        if text_input.strip() == "":
            return tuple(suffix for suffix in suffixes)

        return tuple(f"{text_input}{joiner}{suffix}" for suffix in suffixes)
