class TextSwitch4:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selection": (["1- Tlayox", "2- Memories", "3- Woodworkers", "4- Cookie Cuters"],),
                "1- Tlayox": ("STRING", {"multiline": True, "default": ""}),
                "2- Memories": ("STRING", {"multiline": True, "default": ""}),
                "3- Woodworkers": ("STRING", {"multiline": True, "default": ""}),
                "4- Cookie Cuters": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "switch"
    CATEGORY = "Tlayox"

    def switch(self, selection, **kwargs):
        return (kwargs.get(selection, ""),)
