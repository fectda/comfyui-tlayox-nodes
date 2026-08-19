class SmartExpectedBox:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "orig_w": ("INT", {"default": 1024, "min": 1, "max": 8192}),
                "orig_h": ("INT", {"default": 1024, "min": 1, "max": 8192}),
                "target_w": ("INT", {"default": 1080, "min": 1, "max": 8192}),
                "target_h": ("INT", {"default": 1920, "min": 1, "max": 8192}),
                "crop_box": ("BOX",),
                "margin": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 10.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "DICT")
    RETURN_NAMES = (
        "crop_left",
        "crop_right",
        "crop_top",
        "crop_bottom",
        "pad_left",
        "pad_right",
        "pad_top",
        "pad_bottom",
        "BOX_DATA",
    )
    FUNCTION = "calculate"
    CATEGORY = "Tlayox/Math"

    def calculate(self, orig_w, orig_h, target_w, target_h, crop_box, margin):
        x1, y1, x2, y2 = crop_box

        sw = x2 - x1
        sh = y2 - y1
        cx = x1 + sw / 2.0
        cy = y1 + sh / 2.0

        safe_w = sw * (1 + margin)
        safe_h = sh * (1 + margin)
        safe_ar = safe_w / safe_h

        target_ar = target_w / target_h

        if safe_ar > target_ar:
            exp_w = safe_w
            exp_h = exp_w / target_ar
        else:
            exp_h = safe_h
            exp_w = exp_h * target_ar

        exp_w_int = int(round(exp_w))
        exp_h_int = int(round(exp_h))

        exp_left = int(round(cx - exp_w_int / 2.0))
        exp_right = exp_left + exp_w_int
        exp_top = int(round(cy - exp_h_int / 2.0))
        exp_bottom = exp_top + exp_h_int

        crop_left = max(0, exp_left)
        pad_left = max(0, -exp_left)

        crop_right = max(0, orig_w - exp_right)
        pad_right = max(0, exp_right - orig_w)

        crop_top = max(0, exp_top)
        pad_top = max(0, -exp_top)

        crop_bottom = max(0, orig_h - exp_bottom)
        pad_bottom = max(0, exp_bottom - orig_h)

        safe_left = int(round(cx - safe_w / 2.0))
        safe_top = int(round(cy - safe_h / 2.0))

        box_data = {
            "safe_box": [safe_left, safe_top, int(round(safe_w)), int(round(safe_h))],
            "expected_box": [exp_left, exp_top, exp_w_int, exp_h_int],
        }

        return (crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom, box_data)
