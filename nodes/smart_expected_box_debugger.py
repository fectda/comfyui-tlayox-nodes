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
        # image is a torch Tensor of shape (B, H, W, C) usually, or (H, W, C)
        # We need to process each batch item

        result_images = []
        for i in range(image.shape[0]):
            # Convert to PIL
            img_np = (image[i].cpu().numpy() * 255.0).astype(np.uint8)
            img_pil = Image.fromarray(img_np)
            draw = ImageDraw.Draw(img_pil)

            safe_box = BOX_DATA.get("safe_box", [0, 0, 0, 0])
            expected_box = BOX_DATA.get("expected_box", [0, 0, 0, 0])

            # Draw Safe Box (Red)
            sx, sy, sw, sh = safe_box
            draw.rectangle([sx, sy, sx + sw, sy + sh], outline="red", width=5)

            # Draw Expected Box (Green)
            ex, ey, ew, eh = expected_box
            draw.rectangle([ex, ey, ex + ew, ey + eh], outline="green", width=5)

            # Convert back to tensor
            img_tensor = torch.from_numpy(np.array(img_pil).astype(np.float32) / 255.0)
            result_images.append(img_tensor)

        result_batch = torch.stack(result_images)
        return (result_batch,)
