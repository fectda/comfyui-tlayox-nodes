"""Hostless diagnostic matrix and edge-case tests for SmartExpectedBox."""

import pytest

from nodes.smart_expected_box import SmartExpectedBox
from tests.smart_expected_box_case_matrix import MATRIX_CASES


def _case_id(case):
    return case.case_id


def _box_edges(box):
    left, top, width, height = box
    return left, top, left + width, top + height


def _route(case):
    original_width, original_height = case.original_size
    target_width, target_height = case.target_size
    return SmartExpectedBox().calculate(
        orig_w=original_width,
        orig_h=original_height,
        target_w=target_width,
        target_h=target_height,
        crop_box=case.crop_box,
        safety_padding_px=case.safety_padding_px,
        composition=case.composition,
    )


@pytest.mark.parametrize("case", MATRIX_CASES, ids=_case_id)
def test_smart_expected_box_matrix_preserves_all_geometry_invariants(case):
    """Every matrix combination must produce a safe, integer, routable rectangle."""
    crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom, box_data = _route(case)
    original_width, original_height = case.original_size
    target_width, target_height = case.target_size

    directions = (crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom)
    assert all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in directions)

    expected_left, expected_top, expected_width, expected_height = box_data["expected_box"]
    safe_left, safe_top, safe_width, safe_height = box_data["safe_box"]
    expected_right = expected_left + expected_width
    expected_bottom = expected_top + expected_height
    safe_right = safe_left + safe_width
    safe_bottom = safe_top + safe_height

    assert expected_width > 0
    assert expected_height > 0
    assert expected_left <= safe_left <= safe_right <= expected_right
    assert expected_top <= safe_top <= safe_bottom <= expected_bottom

    actual_ratio = expected_width / expected_height
    target_ratio = target_width / target_height
    relative_ratio_error = abs(actual_ratio / target_ratio - 1.0)
    rounding_tolerance = 1.0 / max(1, min(expected_width, expected_height) - 1)
    assert relative_ratio_error <= rounding_tolerance + 1e-12
    assert box_data["output_aspect_ratio"] == pytest.approx(actual_ratio)
    assert box_data["aspect_ratio_relative_error"] == pytest.approx(relative_ratio_error)
    assert box_data["aspect_ratio_tolerance"] == pytest.approx(rounding_tolerance)

    subject_x1, subject_y1, subject_x2, subject_y2 = case.crop_box
    subject_center_x = (subject_x1 + subject_x2) / 2.0
    subject_center_y = (subject_y1 + subject_y2) / 2.0
    realized_anchor_x = (subject_center_x - expected_left) / expected_width
    realized_anchor_y = (subject_center_y - expected_top) / expected_height
    assert abs(realized_anchor_x - box_data["composition_anchor_x"]) <= 0.5 / expected_width + 1e-12
    assert abs(realized_anchor_y - box_data["composition_anchor_y"]) <= 0.5 / expected_height + 1e-12
    assert box_data["realized_anchor_x"] == pytest.approx(realized_anchor_x)
    assert box_data["realized_anchor_y"] == pytest.approx(realized_anchor_y)
    assert box_data["anchor_error_x"] == pytest.approx(realized_anchor_x - box_data["requested_anchor_x"])
    assert box_data["anchor_error_y"] == pytest.approx(realized_anchor_y - box_data["requested_anchor_y"])

    assert not (crop_left and pad_left)
    assert not (crop_right and pad_right)
    assert not (crop_top and pad_top)
    assert not (crop_bottom and pad_bottom)

    assert original_width - crop_left - crop_right + pad_left + pad_right == expected_width
    assert original_height - crop_top - crop_bottom + pad_top + pad_bottom == expected_height
    assert box_data["output_size"] == [expected_width, expected_height]
    assert box_data["operations"] == {
        "crop": {"left": crop_left, "right": crop_right, "top": crop_top, "bottom": crop_bottom},
        "pad": {"left": pad_left, "right": pad_right, "top": pad_top, "bottom": pad_bottom},
    }

    retained_left = crop_left
    retained_top = crop_top
    retained_right = original_width - crop_right
    retained_bottom = original_height - crop_bottom
    assert retained_left <= max(0, safe_left)
    assert retained_top <= max(0, safe_top)
    assert retained_right >= min(original_width, safe_right)
    assert retained_bottom >= min(original_height, safe_bottom)

    expected_overflow = box_data["expected_box_overflow"]
    assert expected_overflow == {
        "left": pad_left,
        "right": pad_right,
        "top": pad_top,
        "bottom": pad_bottom,
    }
    assert box_data["requires_outpaint"] == any((pad_left, pad_right, pad_top, pad_bottom))


def test_smart_expected_box_matrix_has_the_required_dimensions():
    """Keep the diagnostic matrix broad enough to catch category regressions."""
    assert len(MATRIX_CASES) == 3 * 3 * 3 * 9 * 9 * 3 * 2


def test_smart_expected_box_matrix_exercises_all_canonical_composition_positions():
    """The audit must exercise every canonical 3x3 composition position."""
    assert {case.composition for case in MATRIX_CASES} == {
        "top_left",
        "top_center",
        "top_right",
        "center_left",
        "center",
        "center_right",
        "bottom_left",
        "bottom_center",
        "bottom_right",
    }


def test_smart_expected_box_matrix_exercises_all_crop_and_pad_directions():
    crop_directions = set()
    pad_directions = set()
    mixed_cases = 0

    for case in MATRIX_CASES:
        result = _route(case)
        direction_names = (
            "crop_left",
            "crop_right",
            "crop_top",
            "crop_bottom",
            "pad_left",
            "pad_right",
            "pad_top",
            "pad_bottom",
        )
        values = dict(zip(direction_names, result[:8]))
        crop_directions.update(name for name in direction_names[:4] if values[name])
        pad_directions.update(name for name in direction_names[4:] if values[name])
        if any(values[name] for name in direction_names[:4]) and any(values[name] for name in direction_names[4:]):
            mixed_cases += 1

    assert crop_directions == {"crop_left", "crop_right", "crop_top", "crop_bottom"}
    assert pad_directions == {"pad_left", "pad_right", "pad_top", "pad_bottom"}
    assert mixed_cases > 0


def test_smart_expected_box_reports_expansion_and_outpaint_separately():
    result = SmartExpectedBox().calculate(
        orig_w=1000,
        orig_h=800,
        target_w=1,
        target_h=1,
        crop_box=[417, 233, 568, 386],
        safety_padding_px=17,
        composition="center_left",
    )
    box_data = result[-1]

    assert box_data["expected_box_expanded"] is True
    assert box_data["expected_box_expansion"]["width"] > 0
    assert box_data["base_expected_box"] != box_data["expected_box"]
    assert box_data["requires_outpaint"] is False
    assert box_data["expected_box_overflow"] == {"left": 0, "right": 0, "top": 0, "bottom": 0}
    assert box_data["realized_anchor_x"] == pytest.approx(
        box_data["composition_anchor_x"], abs=0.5 / box_data["expected_box"][2] + 1e-12
    )


def test_smart_expected_box_reports_outpaint_without_confusing_it_with_expansion():
    result = SmartExpectedBox().calculate(
        orig_w=200,
        orig_h=200,
        target_w=16,
        target_h=9,
        crop_box=[50, 50, 150, 150],
        safety_padding_px=25,
        composition="center",
    )
    box_data = result[-1]

    assert box_data["expected_box_expanded"] is False
    assert box_data["expected_box_expansion"] == {"width": 0, "height": 0}
    assert box_data["requires_outpaint"] is True
    assert box_data["expected_box_overflow"] == {"left": 34, "right": 33, "top": 0, "bottom": 0}


@pytest.mark.parametrize(
    "composition, crop_box, overflow_side",
    [
        ("top_center", [80, 1, 120, 21], "top"),
        ("bottom_center", [80, 179, 120, 199], "bottom"),
    ],
)
def test_smart_expected_box_routes_vertical_overflow_to_top_or_bottom_padding(composition, crop_box, overflow_side):
    result = SmartExpectedBox().calculate(
        orig_w=200,
        orig_h=200,
        target_w=1,
        target_h=2,
        crop_box=crop_box,
        safety_padding_px=10,
        composition=composition,
    )
    box_data = result[-1]

    assert box_data["expected_box_overflow"][overflow_side] > 0
    assert box_data["requires_outpaint"] is True
    assert result[6 if overflow_side == "top" else 7] == box_data["expected_box_overflow"][overflow_side]


@pytest.mark.parametrize(
    "crop_box",
    [
        [0.25, 0.25, 0.75, 0.75],
        [0.5, 0.5, 1.5, 1.5],
        [50.5, 49.5, 151.5, 150.5],
    ],
)
def test_smart_expected_box_rasterizes_tiny_fractional_boxes_outward(crop_box):
    result = SmartExpectedBox().calculate(
        orig_w=200,
        orig_h=200,
        target_w=1,
        target_h=1,
        crop_box=crop_box,
        safety_padding_px=0,
    )
    box_data = result[-1]
    safe_left, safe_top, safe_width, safe_height = box_data["safe_box"]
    safe_right = safe_left + safe_width
    safe_bottom = safe_top + safe_height

    assert safe_width >= 1
    assert safe_height >= 1
    assert safe_left <= crop_box[0]
    assert safe_top <= crop_box[1]
    assert safe_right >= crop_box[2]
    assert safe_bottom >= crop_box[3]


@pytest.mark.parametrize("target_size", [(1, 8192), (8192, 1), (7, 1000), (1000, 7)])
def test_smart_expected_box_handles_extreme_target_aspects(target_size):
    target_width, target_height = target_size
    result = SmartExpectedBox().calculate(
        orig_w=101,
        orig_h=137,
        target_w=target_width,
        target_h=target_height,
        crop_box=[49.5, 66.5, 50.5, 67.5],
        safety_padding_px=0,
        composition="center",
    )
    expected_width, expected_height = result[-1]["output_size"]
    relative_ratio_error = abs((expected_width / expected_height) / (target_width / target_height) - 1.0)
    tolerance = 1.0 / max(1, min(expected_width, expected_height) - 1)

    assert expected_width > 0
    assert expected_height > 0
    assert relative_ratio_error <= tolerance + 1e-12


def test_smart_expected_box_is_deterministic_and_does_not_mutate_fractional_input():
    crop_box = [10.5, 20.25, 80.75, 91.5]
    original_crop_box = crop_box.copy()
    node = SmartExpectedBox()

    first = node.calculate(137, 137, 16, 9, crop_box, 7, "center_right")
    second = node.calculate(137, 137, 16, 9, crop_box, 7, "center_right")

    assert first == second
    assert crop_box == original_crop_box


@pytest.mark.parametrize(
    "overrides",
    [
        {"orig_w": 0},
        {"orig_h": 0},
        {"target_w": 0},
        {"target_h": 0},
        {"orig_w": -1},
        {"orig_h": -1},
        {"target_w": -1},
        {"target_h": -1},
        {"orig_w": True},
        {"target_h": False},
        {"orig_w": 1.5},
        {"target_h": 1.5},
        {"target_w": 10**400},
        {"safety_padding_px": -1},
        {"safety_padding_px": 1.5},
        {"safety_padding_px": True},
        {"crop_box": []},
        {"crop_box": [0, 0, 0, 0]},
        {"crop_box": [100, 20, 10, 30]},
        {"crop_box": [10, 30, 10, 40]},
        {"crop_box": [-0.01, 20, 10, 30]},
        {"crop_box": [10, -0.01, 20, 30]},
        {"crop_box": [10, 20, 200.01, 30]},
        {"crop_box": [10, 20, 20, 200.01]},
        {"crop_box": [0, 0, float("nan"), 10]},
        {"crop_box": [0, 0, float("inf"), 10]},
        {"crop_box": [True, 0, 10, 10]},
        {"crop_box": None},
        {"crop_box": [0, 0, "10", 10]},
        {"composition": "centerish"},
        {"composition": None},
    ],
)
def test_smart_expected_box_rejects_invalid_inputs(overrides):
    inputs = {
        "orig_w": 200,
        "orig_h": 200,
        "target_w": 16,
        "target_h": 9,
        "crop_box": [50, 50, 150, 150],
        "safety_padding_px": 25,
        "composition": "center",
    }
    inputs.update(overrides)

    with pytest.raises(ValueError):
        SmartExpectedBox().calculate(**inputs)


def test_smart_expected_box_accepts_large_padding_and_routes_all_overflow_as_pad():
    result = SmartExpectedBox().calculate(
        orig_w=31,
        orig_h=29,
        target_w=9,
        target_h=16,
        crop_box=[10, 9, 21, 20],
        safety_padding_px=10000,
        composition="center_right",
    )
    values = result[:8]
    box_data = result[-1]

    assert all(isinstance(value, int) and value >= 0 for value in values)
    assert box_data["requires_outpaint"] is True
    assert sum(values[:4]) == 0
    assert any(values[4:])


def test_smart_expected_box_rejects_padding_that_cannot_be_represented_finitely():
    with pytest.raises(ValueError, match="too large"):
        SmartExpectedBox().calculate(
            orig_w=31,
            orig_h=29,
            target_w=9,
            target_h=16,
            crop_box=[10, 9, 21, 20],
            safety_padding_px=10**400,
        )
