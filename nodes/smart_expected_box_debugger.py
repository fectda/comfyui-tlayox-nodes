import math

import numpy as np
import torch
from PIL import Image, ImageDraw


def _clip_rectangle(box, image_width, image_height):
    """Return an in-bounds PIL rectangle, or ``None`` when it is off-screen."""
    try:
        left, top, width, height = (int(value) for value in box)
    except (TypeError, ValueError, OverflowError):
        return None

    if width <= 0 or height <= 0 or image_width <= 0 or image_height <= 0:
        return None

    right = left + width
    bottom = top + height
    max_x = image_width - 1
    max_y = image_height - 1
    if right < 0 or bottom < 0 or left > max_x or top > max_y:
        return None

    return [max(0, left), max(0, top), min(max_x, right), min(max_y, bottom)]


def _guide_position(origin, size, anchor):
    """Calculate a guide coordinate without passing overflow values to PIL."""
    try:
        return int(round(origin + anchor * size))
    except (TypeError, ValueError, OverflowError):
        return None


def _clip_vertical_guide(x, top, bottom, image_width, image_height):
    """Clip a vertical guide to image bounds, or skip it when disjoint."""
    if x < 0 or x >= image_width:
        return None
    top, bottom = sorted((top, bottom))
    if bottom < 0 or top >= image_height:
        return None
    return [(x, max(0, top)), (x, min(image_height - 1, bottom))]


def _clip_horizontal_guide(left, right, y, image_width, image_height):
    """Clip a horizontal guide to image bounds, or skip it when disjoint."""
    if y < 0 or y >= image_height:
        return None
    left, right = sorted((left, right))
    if right < 0 or left >= image_width:
        return None
    return [(max(0, left), y), (min(image_width - 1, right), y)]


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
            image_width, image_height = img_pil.size

            detected_box = BOX_DATA.get("detected_box")
            safe_box = BOX_DATA.get("safe_box", [0, 0, 0, 0])
            expected_box = BOX_DATA.get("expected_box", [0, 0, 0, 0])

            # Draw detected box (Blue) first so the established red/green
            # safe/expected convention remains visible when boxes overlap.
            if detected_box is not None:
                clipped_detected_box = _clip_rectangle(detected_box, image_width, image_height)
                if clipped_detected_box is not None:
                    draw.rectangle(clipped_detected_box, outline="blue", width=5)

            # Draw Safe Box (Red)
            clipped_safe_box = _clip_rectangle(safe_box, image_width, image_height)
            if clipped_safe_box is not None:
                draw.rectangle(clipped_safe_box, outline="red", width=5)

            # Draw Expected Box (Green)
            ex, ey, ew, eh = expected_box
            clipped_expected_box = _clip_rectangle(expected_box, image_width, image_height)
            if clipped_expected_box is not None:
                draw.rectangle(clipped_expected_box, outline="green", width=5)

            # Draw the selected vertical composition guide (Yellow) when
            # present. Legacy BOX_DATA without anchor metadata remains valid.
            composition_anchor_x = BOX_DATA.get("composition_anchor_x")
            if (
                isinstance(composition_anchor_x, (int, float))
                and math.isfinite(composition_anchor_x)
                and 0.0 <= composition_anchor_x <= 1.0
            ):
                guide_x = _guide_position(ex, ew, composition_anchor_x)
                if guide_x is not None:
                    clipped_guide = _clip_vertical_guide(
                        guide_x,
                        ey,
                        ey + eh,
                        image_width,
                        image_height,
                    )
                    if clipped_guide is not None:
                        draw.line(clipped_guide, fill="yellow", width=2)

            # Draw the selected horizontal composition guide (Cyan) when
            # present. The distinct color makes the two-axis selection clear.
            composition_anchor_y = BOX_DATA.get("composition_anchor_y")
            if (
                isinstance(composition_anchor_y, (int, float))
                and math.isfinite(composition_anchor_y)
                and 0.0 <= composition_anchor_y <= 1.0
            ):
                guide_y = _guide_position(ey, eh, composition_anchor_y)
                if guide_y is not None:
                    clipped_guide = _clip_horizontal_guide(
                        ex,
                        ex + ew,
                        guide_y,
                        image_width,
                        image_height,
                    )
                    if clipped_guide is not None:
                        draw.line(clipped_guide, fill="cyan", width=2)

            # Convert back to tensor
            img_tensor = torch.from_numpy(np.array(img_pil).astype(np.float32) / 255.0)
            result_images.append(img_tensor)

        result_batch = torch.stack(result_images)
        return (result_batch,)
