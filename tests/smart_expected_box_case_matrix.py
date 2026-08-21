"""Deterministic SmartExpectedBox geometry cases shared by audit tests."""

from dataclasses import dataclass

SOURCE_CANVASES = {
    "square": (101, 101),
    "landscape": (137, 83),
    "portrait": (83, 137),
}

BOX_ASPECTS = {
    "horizontal": (3, 1),
    "square": (1, 1),
    "vertical": (1, 3),
}

TARGET_ASPECTS = {
    "square": (1, 1),
    "landscape": (16, 9),
    "portrait": (9, 16),
}

COMPOSITIONS = (
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)
PLACEMENTS = (
    "center",
    "left_edge",
    "right_edge",
    "top_edge",
    "bottom_edge",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
SAFETY_PADDINGS = ("zero", "moderate", "large")
COORDINATE_MODES = ("integer", "fractional")


@dataclass(frozen=True)
class GeometryCase:
    """One deterministic combination from the router diagnostic matrix."""

    source_name: str
    box_name: str
    target_name: str
    composition: str
    placement: str
    safety_name: str
    coordinate_mode: str

    @property
    def original_size(self):
        return SOURCE_CANVASES[self.source_name]

    @property
    def target_size(self):
        return TARGET_ASPECTS[self.target_name]

    @property
    def crop_box(self):
        original_width, original_height = self.original_size
        box_width, box_height = _box_size(self.original_size, self.box_name)
        left = _axis_origin(original_width, box_width, self.placement, horizontal=True)
        top = _axis_origin(original_height, box_height, self.placement, horizontal=False)

        if self.coordinate_mode == "fractional":
            left, top = _fractionalize(
                left,
                top,
                original_width,
                original_height,
                box_width,
                box_height,
            )

        return [left, top, left + box_width, top + box_height]

    @property
    def safety_padding_px(self):
        original_width, original_height = self.original_size
        if self.safety_name == "zero":
            return 0
        if self.safety_name == "moderate":
            return max(1, min(original_width, original_height) // 16)
        return max(1, min(original_width, original_height) // 2)

    @property
    def case_id(self):
        return "-".join(
            (
                self.source_name,
                self.box_name,
                self.target_name,
                self.composition.lower(),
                self.placement,
                self.safety_name,
                self.coordinate_mode,
            )
        )


def _box_size(original_size, box_name):
    span = min(original_size)
    if box_name == "horizontal":
        return max(3, span // 3), max(2, span // 10)
    if box_name == "vertical":
        return max(2, span // 10), max(3, span // 3)
    return max(3, span // 4), max(3, span // 4)


def _axis_origin(canvas_length, box_length, placement, *, horizontal):
    if horizontal:
        if placement in {"left_edge", "top_left", "bottom_left"}:
            return 0.0
        if placement in {"right_edge", "top_right", "bottom_right"}:
            return float(canvas_length - box_length)
        return (canvas_length - box_length) / 2.0

    if placement in {"top_edge", "top_left", "top_right"}:
        return 0.0
    if placement in {"bottom_edge", "bottom_left", "bottom_right"}:
        return float(canvas_length - box_length)
    return (canvas_length - box_length) / 2.0


def _fractionalize(left, top, original_width, original_height, box_width, box_height):
    """Move each edge by a quarter pixel while keeping the box in-bounds."""
    fractional_left = left + 0.25 if left == 0 else left - 0.25 if left + box_width == original_width else left + 0.25
    fractional_top = top + 0.25 if top == 0 else top - 0.25 if top + box_height == original_height else top + 0.25
    return fractional_left, fractional_top


MATRIX_CASES = tuple(
    GeometryCase(source_name, box_name, target_name, composition, placement, safety_name, coordinate_mode)
    for source_name in SOURCE_CANVASES
    for box_name in BOX_ASPECTS
    for target_name in TARGET_ASPECTS
    for composition in COMPOSITIONS
    for placement in PLACEMENTS
    for safety_name in SAFETY_PADDINGS
    for coordinate_mode in COORDINATE_MODES
)
