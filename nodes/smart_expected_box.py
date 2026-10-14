"""Calculate aspect-ratio crop and extend routing around a detected box.

Routed output geometry is bounded to 16,000,000 pixels and 16,384 pixels per
axis before downstream image nodes can allocate it.
"""

import math
from numbers import Integral, Real

_COMPOSITION_ANCHORS = {
    "top_left": (1.0 / 3.0, 1.0 / 3.0),
    "top_center": (1.0 / 2.0, 1.0 / 3.0),
    "top_right": (2.0 / 3.0, 1.0 / 3.0),
    "center_left": (1.0 / 3.0, 1.0 / 2.0),
    "center": (1.0 / 2.0, 1.0 / 2.0),
    "center_right": (2.0 / 3.0, 1.0 / 2.0),
    "bottom_left": (1.0 / 3.0, 2.0 / 3.0),
    "bottom_center": (1.0 / 2.0, 2.0 / 3.0),
    "bottom_right": (2.0 / 3.0, 2.0 / 3.0),
}

_COMPOSITION_ALIASES = {
    "Center": "center",
    "Left": "center_left",
    "Right": "center_right",
}
_MAX_CONTAINMENT_SEARCH_EXPANSIONS = 1024
# Bound routed output geometry before downstream image nodes can allocate it.
MAX_OUTPUT_PIXELS = 16_000_000
MAX_OUTPUT_DIMENSION = 16_384


def _validate_positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _validate_non_negative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return int(value)


def _parse_crop_box(crop_box, orig_w, orig_h):
    try:
        values = list(crop_box)
    except TypeError as error:
        raise ValueError("crop_box must contain four numeric coordinates") from error

    if len(values) != 4:
        raise ValueError("crop_box must contain exactly four coordinates")
    if any(isinstance(value, bool) or not isinstance(value, Real) for value in values):
        raise ValueError("crop_box coordinates must be finite numbers")

    x1, y1, x2, y2 = (float(value) for value in values)
    if not all(math.isfinite(value) for value in (x1, y1, x2, y2)):
        raise ValueError("crop_box coordinates must be finite numbers")
    if x1 < 0 or y1 < 0 or x2 > orig_w or y2 > orig_h:
        raise ValueError("crop_box must be inside the original image")
    if x2 <= x1 or y2 <= y1:
        raise ValueError("crop_box must have positive width and height")
    return x1, y1, x2, y2


def _ceil_positive(value, name):
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be finite") from error
    if not finite:
        raise ValueError(f"{name} must be finite")
    rounded = int(math.ceil(value))
    if rounded < 1:
        raise ValueError(f"{name} must round to at least one pixel")
    return rounded


def _parse_composition(composition):
    if not isinstance(composition, str):
        allowed = ", ".join(_COMPOSITION_ANCHORS)
        raise ValueError(f"composition must be one of: {allowed}")
    canonical = _COMPOSITION_ALIASES.get(composition, composition)
    if canonical not in _COMPOSITION_ANCHORS:
        allowed = ", ".join(_COMPOSITION_ANCHORS)
        raise ValueError(f"composition must be one of: {allowed}")
    anchor_x, anchor_y = _COMPOSITION_ANCHORS[canonical]
    return canonical, anchor_x, anchor_y


class SmartExpectedBox:
    """Return crop/extend distances for a requested output aspect ratio.

    The requested dimensions contribute only their aspect ratio. The node does
    not force the image to target pixel dimensions and does not edit pixels.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "orig_w": ("INT", {"default": 1024, "min": 1, "max": 8192}),
                "orig_h": ("INT", {"default": 1024, "min": 1, "max": 8192}),
                "target_w": ("INT", {"default": 1080, "min": 1, "max": 8192}),
                "target_h": ("INT", {"default": 1920, "min": 1, "max": 8192}),
                "crop_box": ("BOX",),
                "safety_padding_px": ("INT", {"default": 20, "min": 0, "max": 8192}),
                "composition": (list(_COMPOSITION_ANCHORS), {"default": "center"}),
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

    def calculate(self, orig_w, orig_h, target_w, target_h, crop_box, safety_padding_px, composition="center"):
        """Calculate deterministic crop and padding distances.

        Coordinates use a top-left image origin. ``crop_box`` is ``[x1, y1,
        x2, y2]``. Diagnostic boxes use ``[left, top, width, height]``.
        ``composition`` selects the subject's two-axis output anchor. Legacy
        ``Center``, ``Left``, and ``Right`` values are normalized to their
        canonical center-row positions.
        """
        orig_w = _validate_positive_integer(orig_w, "orig_w")
        orig_h = _validate_positive_integer(orig_h, "orig_h")
        target_w = _validate_positive_integer(target_w, "target_w")
        target_h = _validate_positive_integer(target_h, "target_h")
        safety_padding_px = _validate_non_negative_integer(safety_padding_px, "safety_padding_px")
        composition, composition_anchor_x, composition_anchor_y = _parse_composition(composition)
        x1, y1, x2, y2 = _parse_crop_box(crop_box, orig_w, orig_h)

        sw = x2 - x1
        sh = y2 - y1
        cx = x1 + sw / 2.0
        cy = y1 + sh / 2.0

        # Rasterize the continuous input box outward. Rounding each edge in
        # the safe direction prevents a tiny or fractional detected box from
        # becoming zero-sized or losing source pixels at a half-pixel boundary.
        try:
            safe_left = math.floor(x1 - safety_padding_px)
            safe_top = math.floor(y1 - safety_padding_px)
            safe_right = math.ceil(x2 + safety_padding_px)
            safe_bottom = math.ceil(y2 + safety_padding_px)
        except OverflowError as error:
            raise ValueError("safety_padding_px is too large for finite geometry") from error
        safe_w_int = safe_right - safe_left
        safe_h_int = safe_bottom - safe_top

        try:
            target_ar = target_w / target_h
        except OverflowError as error:
            raise ValueError("target dimensions are too large") from error
        if not math.isfinite(target_ar) or target_ar <= 0:
            raise ValueError("target dimensions must produce a finite aspect ratio")

        try:
            safe_ar = safe_w_int / safe_h_int
        except OverflowError as error:
            raise ValueError("safe-box dimensions are too large") from error
        if safe_ar > target_ar:
            base_exp_w = safe_w_int
            try:
                base_exp_h = _ceil_positive(base_exp_w / target_ar, "expected height")
            except OverflowError as error:
                raise ValueError("expected dimensions are too large") from error
        else:
            base_exp_h = safe_h_int
            try:
                base_exp_w = _ceil_positive(base_exp_h * target_ar, "expected width")
            except OverflowError as error:
                raise ValueError("expected dimensions are too large") from error

        def dimensions_for_width(width):
            if width == base_exp_w:
                return base_exp_w, base_exp_h
            try:
                height = _ceil_positive(width / target_ar, "expected height")
            except OverflowError as error:
                raise ValueError("expected dimensions are too large") from error
            return width, max(base_exp_h, height)

        def positioned_box(width):
            width, height = dimensions_for_width(width)
            try:
                left = int(round(cx - composition_anchor_x * width))
                top = int(round(cy - composition_anchor_y * height))
            except OverflowError as error:
                raise ValueError("expected dimensions are too large") from error
            return left, top, width, height, left + width, top + height

        def contains_safe_box(width):
            left, top, _, _, right, bottom = positioned_box(width)
            return left <= safe_left and top <= safe_top and right >= safe_right and bottom >= safe_bottom

        # Containment is monotonic as the expected width grows. Exponential
        # search followed by binary search avoids a pixel-by-pixel loop when a
        # very large safe box or extreme aspect ratio requires expansion.
        lower_width = base_exp_w
        upper_width = lower_width
        for _ in range(_MAX_CONTAINMENT_SEARCH_EXPANSIONS):
            if contains_safe_box(upper_width):
                break
            upper_width *= 2
        else:
            raise ValueError("expected-box containment search exceeded safety bound")

        while lower_width < upper_width:
            candidate_width = (lower_width + upper_width) // 2
            if contains_safe_box(candidate_width):
                upper_width = candidate_width
            else:
                lower_width = candidate_width + 1

        exp_left, exp_top, exp_w_int, exp_h_int, exp_right, exp_bottom = positioned_box(lower_width)
        if exp_w_int > MAX_OUTPUT_DIMENSION or exp_h_int > MAX_OUTPUT_DIMENSION:
            raise ValueError(
                "SmartExpectedBox output dimension exceeds safe limit of "
                f"{MAX_OUTPUT_DIMENSION:,} pixels (MAX_OUTPUT_DIMENSION={MAX_OUTPUT_DIMENSION})"
            )
        output_pixels = exp_w_int * exp_h_int
        if output_pixels > MAX_OUTPUT_PIXELS:
            raise ValueError(
                "SmartExpectedBox output pixel count exceeds safe limit of "
                f"{MAX_OUTPUT_PIXELS:,} pixels (MAX_OUTPUT_PIXELS={MAX_OUTPUT_PIXELS})"
            )
        base_exp_left, base_exp_top, _, _, _, _ = positioned_box(base_exp_w)

        detected_left = math.floor(x1)
        detected_top = math.floor(y1)
        detected_right = math.ceil(x2)
        detected_bottom = math.ceil(y2)

        crop_left = max(0, exp_left)
        pad_left = max(0, -exp_left)

        crop_right = max(0, orig_w - exp_right)
        pad_right = max(0, exp_right - orig_w)

        crop_top = max(0, exp_top)
        pad_top = max(0, -exp_top)

        crop_bottom = max(0, orig_h - exp_bottom)
        pad_bottom = max(0, exp_bottom - orig_h)

        expected_box_expanded = exp_w_int != base_exp_w or exp_h_int != base_exp_h
        realized_anchor_x = (cx - exp_left) / exp_w_int
        realized_anchor_y = (cy - exp_top) / exp_h_int
        expected_box_overflow = {
            "left": pad_left,
            "right": pad_right,
            "top": pad_top,
            "bottom": pad_bottom,
        }
        try:
            output_aspect_ratio = exp_w_int / exp_h_int
        except OverflowError as error:
            raise ValueError("output dimensions are too large") from error
        aspect_ratio_relative_error = abs(output_aspect_ratio / target_ar - 1.0)
        aspect_ratio_tolerance = 1.0 / max(1, min(exp_w_int, exp_h_int) - 1)

        box_data = {
            "detected_box": [
                detected_left,
                detected_top,
                detected_right - detected_left,
                detected_bottom - detected_top,
            ],
            "detected_box_float": [x1, y1, sw, sh],
            "safe_box": [safe_left, safe_top, safe_w_int, safe_h_int],
            "expected_box": [exp_left, exp_top, exp_w_int, exp_h_int],
            "base_expected_box": [base_exp_left, base_exp_top, base_exp_w, base_exp_h],
            "original_size": [orig_w, orig_h],
            "target_aspect_ratio": target_ar,
            "output_aspect_ratio": output_aspect_ratio,
            "aspect_ratio_relative_error": aspect_ratio_relative_error,
            "aspect_ratio_tolerance": aspect_ratio_tolerance,
            "safety_padding_px": safety_padding_px,
            "composition": composition,
            "composition_anchor_x": composition_anchor_x,
            "composition_anchor_y": composition_anchor_y,
            "requested_anchor_x": composition_anchor_x,
            "requested_anchor_y": composition_anchor_y,
            "realized_anchor_x": realized_anchor_x,
            "realized_anchor_y": realized_anchor_y,
            "anchor_error_x": realized_anchor_x - composition_anchor_x,
            "anchor_error_y": realized_anchor_y - composition_anchor_y,
            "requested_anchor": {"x": composition_anchor_x, "y": composition_anchor_y},
            "realized_anchor": {
                "x": realized_anchor_x,
                "y": realized_anchor_y,
            },
            "anchor_error": {
                "x": realized_anchor_x - composition_anchor_x,
                "y": realized_anchor_y - composition_anchor_y,
            },
            "expected_box_expanded": expected_box_expanded,
            "expected_box_expansion": {
                "width": exp_w_int - base_exp_w,
                "height": exp_h_int - base_exp_h,
            },
            "expected_box_overflow": expected_box_overflow,
            "requires_outpaint": any(expected_box_overflow.values()),
            "output_size": [exp_w_int, exp_h_int],
            "operations": {
                "crop": {
                    "left": crop_left,
                    "right": crop_right,
                    "top": crop_top,
                    "bottom": crop_bottom,
                },
                "pad": {
                    "left": pad_left,
                    "right": pad_right,
                    "top": pad_top,
                    "bottom": pad_bottom,
                },
            },
        }

        return (crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom, box_data)
