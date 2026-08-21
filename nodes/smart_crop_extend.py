"""Crop and extend an IMAGE tensor using SmartExpectedBox routing values."""

from numbers import Integral

import torch

_DIRECTION_NAMES = (
    "crop_left",
    "crop_right",
    "crop_top",
    "crop_bottom",
    "pad_left",
    "pad_right",
    "pad_top",
    "pad_bottom",
)


def _validate_direction(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return int(value)


class SmartCropExtend:
    """Apply crop/extend distances without resizing source pixels.

    The output uses ComfyUI's batched IMAGE convention ``[B, H, W, C]``.
    The returned MASK uses ``[B, H, W]`` with ``1.0`` for newly padded
    outpaint regions and ``0.0`` for retained source pixels.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "crop_left": ("INT", {"default": 0, "min": 0}),
                "crop_right": ("INT", {"default": 0, "min": 0}),
                "crop_top": ("INT", {"default": 0, "min": 0}),
                "crop_bottom": ("INT", {"default": 0, "min": 0}),
                "pad_left": ("INT", {"default": 0, "min": 0}),
                "pad_right": ("INT", {"default": 0, "min": 0}),
                "pad_top": ("INT", {"default": 0, "min": 0}),
                "pad_bottom": ("INT", {"default": 0, "min": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "outpaint_mask")
    FUNCTION = "execute"
    CATEGORY = "Tlayox/Image"

    def execute(
        self,
        image,
        crop_left,
        crop_right,
        crop_top,
        crop_bottom,
        pad_left,
        pad_right,
        pad_top,
        pad_bottom,
    ):
        """Return a new canvas and mask for the supplied directional values."""
        if not isinstance(image, torch.Tensor) or image.ndim != 4:
            raise ValueError("image must be a batched IMAGE tensor with shape [B, H, W, C]")
        if any(size < 1 for size in image.shape):
            raise ValueError("image must have non-zero batch, height, width, and channel dimensions")

        directions = {
            name: _validate_direction(value, name)
            for name, value in zip(
                _DIRECTION_NAMES,
                (
                    crop_left,
                    crop_right,
                    crop_top,
                    crop_bottom,
                    pad_left,
                    pad_right,
                    pad_top,
                    pad_bottom,
                ),
            )
        }

        batch, height, width, channels = image.shape
        if directions["crop_left"] + directions["crop_right"] >= width:
            raise ValueError("crop distances must leave at least one source column")
        if directions["crop_top"] + directions["crop_bottom"] >= height:
            raise ValueError("crop distances must leave at least one source row")

        source = image[
            :,
            directions["crop_top"] : height - directions["crop_bottom"],
            directions["crop_left"] : width - directions["crop_right"],
            :,
        ]
        source_height, source_width = source.shape[1:3]
        output_height = source_height + directions["pad_top"] + directions["pad_bottom"]
        output_width = source_width + directions["pad_left"] + directions["pad_right"]

        output = torch.zeros(
            (batch, output_height, output_width, channels),
            dtype=image.dtype,
            device=image.device,
        )
        output[
            :,
            directions["pad_top"] : directions["pad_top"] + source_height,
            directions["pad_left"] : directions["pad_left"] + source_width,
            :,
        ] = source

        outpaint_mask = torch.ones(
            (batch, output_height, output_width),
            dtype=torch.float32,
            device=image.device,
        )
        outpaint_mask[
            :,
            directions["pad_top"] : directions["pad_top"] + source_height,
            directions["pad_left"] : directions["pad_left"] + source_width,
        ] = 0.0

        return output, outpaint_mask
