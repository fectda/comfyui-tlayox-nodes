import math

import numpy as np
import torch
from PIL import Image, ImageDraw


class SmartExpectedBoxDebugger:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "BOX_DATA": ("DICT",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "draw"
    CATEGORY = "Tlayox/Debug"

    def draw(self, image, BOX_DATA):
        """Draw diagnostic boxes and available two-axis composition guides without mutation."""
        # image is a torch Tensor of shape (B, H, W, C) usually, or (H, W, C)
        # We need to process each batch item

        result_images = []
        for i in range(image.shape[0]):
            # Convert to PIL
            img_np = (image[i].cpu().numpy() * 255.0).astype(np.uint8)
            img_pil = Image.fromarray(img_np)
            draw = ImageDraw.Draw(img_pil)

            detected_box = BOX_DATA.get("detected_box")
            safe_box = BOX_DATA.get("safe_box", [0, 0, 0, 0])
            expected_box = BOX_DATA.get("expected_box", [0, 0, 0, 0])

            # Draw detected box (Blue) first so the established red/green
            # safe/expected convention remains visible when boxes overlap.
            if detected_box is not None:
                dx, dy, dw, dh = detected_box
                draw.rectangle([dx, dy, dx + dw, dy + dh], outline="blue", width=5)

            # Draw Safe Box (Red)
            sx, sy, sw, sh = safe_box
            draw.rectangle([sx, sy, sx + sw, sy + sh], outline="red", width=5)

            # Draw Expected Box (Green)
            ex, ey, ew, eh = expected_box
            draw.rectangle([ex, ey, ex + ew, ey + eh], outline="green", width=5)

            # Draw the selected vertical composition guide (Yellow) when
            # present. Legacy BOX_DATA without anchor metadata remains valid.
            composition_anchor_x = BOX_DATA.get("composition_anchor_x")
            if (
                isinstance(composition_anchor_x, (int, float))
                and math.isfinite(composition_anchor_x)
                and 0.0 <= composition_anchor_x <= 1.0
            ):
                guide_x = int(round(ex + composition_anchor_x * ew))
                draw.line([(guide_x, ey), (guide_x, ey + eh)], fill="yellow", width=2)

            # Draw the selected horizontal composition guide (Cyan) when
            # present. The distinct color makes the two-axis selection clear.
            composition_anchor_y = BOX_DATA.get("composition_anchor_y")
            if (
                isinstance(composition_anchor_y, (int, float))
                and math.isfinite(composition_anchor_y)
                and 0.0 <= composition_anchor_y <= 1.0
            ):
                guide_y = int(round(ey + composition_anchor_y * eh))
                draw.line([(ex, guide_y), (ex + ew, guide_y)], fill="cyan", width=2)

            # Convert back to tensor
            img_tensor = torch.from_numpy(np.array(img_pil).astype(np.float32) / 255.0)
            result_images.append(img_tensor)

        result_batch = torch.stack(result_images)
        return (result_batch,)
