class TextSwitchDynamic:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Categoria": (["Tlayox", "Altepetl"], {"default": "Tlayox"}),
                
                "Estilo_Tlayox": (["1- Tlayox", "2- Memories", "3- Woodworkers", "4- Cookie Cuters"],),
                "1_Tlayox": ("STRING", {"multiline": True, "default": ""}),
                "2_Memories": ("STRING", {"multiline": True, "default": ""}),
                "3_Woodworkers": ("STRING", {"multiline": True, "default": ""}),
                "4_Cookie_Cuters": ("STRING", {"multiline": True, "default": ""}),

                "Estilo_Altepetl": (["Ambar", "Turquesa", "Rojo"],),
                "Ambar": ("STRING", {"multiline": True, "default": ""}),
                "Turquesa": ("STRING", {"multiline": True, "default": ""}),
                "Rojo": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "switch"
    CATEGORY = "Tlayox"

    def switch(self, Categoria, Estilo_Tlayox, Estilo_Altepetl, **kwargs):
        if Categoria == "Tlayox":
            mapping = {
                "1- Tlayox": "1_Tlayox",
                "2- Memories": "2_Memories",
                "3- Woodworkers": "3_Woodworkers",
                "4- Cookie Cuters": "4_Cookie_Cuters",
            }
            return (kwargs.get(mapping.get(Estilo_Tlayox, "1_Tlayox"), ""),)
        else:
            mapping = {
                "Ambar": "Ambar",
                "Turquesa": "Turquesa",
                "Rojo": "Rojo",
            }
            return (kwargs.get(mapping.get(Estilo_Altepetl, "Ambar"), ""),)
