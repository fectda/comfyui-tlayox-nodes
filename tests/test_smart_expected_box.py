import pytest

from nodes.smart_expected_box import SmartExpectedBox


def test_smart_expected_box_basic():
    node = SmartExpectedBox()
    # orig: 1000x1000, target: 1080x1920 (9:16)
    # crop_box: x1=400, y1=400, x2=600, y2=600 (w=200, h=200, center=500,500)
    # safety_padding_px: 20 -> safe_w = 240, safe_h = 240 (safe_ar = 1.0)
    # target_ar = 9/16 = 0.5625
    # safe_ar > target_ar -> exp_w = 240, exp_h = 240 / (9/16) = 426.66 -> 427
    # exp_left = 500 - 120 = 380, exp_right = 380 + 240 = 620
    # exp_top = 500 - 213.5 -> 286, exp_bottom = 286 + 427 = 713
    # crop_left = 380, pad_left = 0
    # crop_right = 1000 - 620 = 380, pad_right = 0
    # crop_top = 286, pad_top = 0
    # crop_bottom = 1000 - 713 = 287, pad_bottom = 0

    cl, cr, ct, cb, pl, pr, pt, pb, box_data = node.calculate(
        orig_w=1000,
        orig_h=1000,
        target_w=1080,
        target_h=1920,
        crop_box=[400, 400, 600, 600],
        safety_padding_px=20,
    )

    assert cl == 380
    assert cr == 380
    assert ct == 286
    assert cb == 287
    assert pl == 0
    assert pr == 0
    assert pt == 0
    assert pb == 0

    assert "safe_box" in box_data
    assert "expected_box" in box_data
    assert box_data["detected_box"] == [400, 400, 200, 200]
    assert box_data["safe_box"] == [380, 380, 240, 240]
    assert box_data["expected_box"] == [380, 286, 240, 427]
    assert box_data["safety_padding_px"] == 20
    assert box_data["output_size"] == [240, 427]
    assert box_data["target_aspect_ratio"] == pytest.approx(9 / 16)
    assert box_data["composition"] == "center"
    assert box_data["requested_anchor_x"] == pytest.approx(0.5)
    assert box_data["requested_anchor_y"] == pytest.approx(0.5)
    assert box_data["operations"] == {
        "crop": {"left": 380, "right": 380, "top": 286, "bottom": 287},
        "pad": {"left": 0, "right": 0, "top": 0, "bottom": 0},
    }


def test_smart_expected_box_needs_padding():
    node = SmartExpectedBox()
    # orig: 200x200, target: 1920x1080 (16:9)
    # crop_box: x1=50, y1=50, x2=150, y2=150 (w=100, h=100, center=100,100)
    # safety_padding_px: 25 -> safe_w = 150, safe_h = 150
    # target_ar = 16/9 = 1.777...
    # safe_ar = 1.0 < target_ar -> exp_h = 150, exp_w = 150 * (16/9) = 266.66 -> 267
    # exp_left = 100 - 133.5 -> -33
    # exp_right = -33 + 267 = 234
    # exp_top = 100 - 75 = 25
    # exp_bottom = 25 + 150 = 175
    # crop_left = 0, pad_left = 33
    # crop_right = 0, pad_right = 34
    # crop_top = 25, pad_top = 0
    # crop_bottom = 200 - 175 = 25, pad_bottom = 0

    cl, cr, ct, cb, pl, pr, pt, pb, box_data = node.calculate(
        orig_w=200,
        orig_h=200,
        target_w=1920,
        target_h=1080,
        crop_box=[50, 50, 150, 150],
        safety_padding_px=25,
    )

    assert cl == 0
    assert pl == 34
    assert cr == 0
    assert pr == 33
    assert ct == 25
    assert pt == 0
    assert cb == 25
    assert pb == 0

    assert box_data["safe_box"] == [25, 25, 150, 150]
    assert box_data["expected_box"] == [-34, 25, 267, 150]


def test_smart_expected_box_exposes_fixed_padding_input():
    required = SmartExpectedBox.INPUT_TYPES()["required"]

    assert "margin" not in required
    assert required["safety_padding_px"] == ("INT", {"default": 20, "min": 0, "max": 8192})
    assert required["composition"] == (
        [
            "top_left",
            "top_center",
            "top_right",
            "center_left",
            "center",
            "center_right",
            "bottom_left",
            "bottom_center",
            "bottom_right",
        ],
        {"default": "center"},
    )


def _box_edges(box):
    left, top, width, height = box
    return left, top, left + width, top + height


def test_smart_expected_box_default_composition_preserves_center_behavior():
    node = SmartExpectedBox()
    inputs = {
        "orig_w": 1000,
        "orig_h": 1000,
        "target_w": 1080,
        "target_h": 1920,
        "crop_box": [400, 400, 600, 600],
        "safety_padding_px": 20,
    }

    legacy_result = node.calculate(**inputs)
    explicit_center_result = node.calculate(**inputs, composition="center")

    assert legacy_result == explicit_center_result
    assert legacy_result[-1]["composition"] == "center"
    assert legacy_result[-1]["composition_anchor_x"] == pytest.approx(0.5)
    assert legacy_result[-1]["composition_anchor_y"] == pytest.approx(0.5)


def test_smart_expected_box_box_data_exposes_two_axis_diagnostics():
    box_data = SmartExpectedBox().calculate(
        orig_w=200,
        orig_h=200,
        target_w=16,
        target_h=9,
        crop_box=[50, 50, 150, 150],
        safety_padding_px=25,
        composition="bottom_right",
    )[-1]

    assert {
        "composition",
        "requested_anchor_x",
        "requested_anchor_y",
        "realized_anchor_x",
        "realized_anchor_y",
        "anchor_error_x",
        "anchor_error_y",
        "expected_box_expanded",
        "expected_box_expansion",
        "expected_box_overflow",
        "requires_outpaint",
    } <= box_data.keys()
    assert box_data["composition"] == "bottom_right"
    assert box_data["expected_box_expansion"]["width"] >= 0
    assert box_data["expected_box_expansion"]["height"] >= 0


@pytest.mark.parametrize(
    "composition, expected_anchor_x, expected_anchor_y",
    [
        ("top_left", 1 / 3, 1 / 3),
        ("top_center", 1 / 2, 1 / 3),
        ("top_right", 2 / 3, 1 / 3),
        ("center_left", 1 / 3, 1 / 2),
        ("center", 1 / 2, 1 / 2),
        ("center_right", 2 / 3, 1 / 2),
        ("bottom_left", 1 / 3, 2 / 3),
        ("bottom_center", 1 / 2, 2 / 3),
        ("bottom_right", 2 / 3, 2 / 3),
    ],
)
def test_smart_expected_box_uses_fixed_3x3_composition_anchors(composition, expected_anchor_x, expected_anchor_y):
    node = SmartExpectedBox()
    crop_box = [417, 233, 568, 386]
    result = node.calculate(
        orig_w=1000,
        orig_h=800,
        target_w=1,
        target_h=1,
        crop_box=crop_box,
        safety_padding_px=17,
        composition=composition,
    )
    expected_box = result[-1]["expected_box"]
    subject_center_x = (crop_box[0] + crop_box[2]) / 2
    subject_center_y = (crop_box[1] + crop_box[3]) / 2
    actual_anchor_x = (subject_center_x - expected_box[0]) / expected_box[2]
    actual_anchor_y = (subject_center_y - expected_box[1]) / expected_box[3]

    assert actual_anchor_x == pytest.approx(expected_anchor_x, abs=0.01)
    assert actual_anchor_y == pytest.approx(expected_anchor_y, abs=0.01)
    assert result[-1]["composition"] == composition
    assert result[-1]["composition_anchor_x"] == pytest.approx(expected_anchor_x)
    assert result[-1]["composition_anchor_y"] == pytest.approx(expected_anchor_y)


@pytest.mark.parametrize(
    "legacy, canonical",
    [("Center", "center"), ("Left", "center_left"), ("Right", "center_right")],
)
def test_smart_expected_box_normalizes_legacy_composition_aliases(legacy, canonical):
    node = SmartExpectedBox()
    inputs = {
        "orig_w": 1000,
        "orig_h": 800,
        "target_w": 16,
        "target_h": 9,
        "crop_box": [417, 233, 568, 386],
        "safety_padding_px": 17,
    }

    legacy_result = node.calculate(**inputs, composition=legacy)
    canonical_result = node.calculate(**inputs, composition=canonical)

    assert legacy_result == canonical_result
    assert legacy_result[-1]["composition"] == canonical


def test_smart_expected_box_expands_vertically_for_off_center_anchor():
    node = SmartExpectedBox()
    inputs = {
        "orig_w": 1000,
        "orig_h": 800,
        "target_w": 1,
        "target_h": 1,
        "crop_box": [417, 233, 568, 386],
        "safety_padding_px": 17,
    }

    center_data = node.calculate(**inputs, composition="center")[-1]
    top_left_data = node.calculate(**inputs, composition="top_left")[-1]

    assert top_left_data["expected_box"][3] > center_data["expected_box"][3]
    assert top_left_data["expected_box_expansion"]["height"] > 0
    assert top_left_data["realized_anchor_y"] == pytest.approx(
        top_left_data["requested_anchor_y"], abs=0.5 / top_left_data["expected_box"][3] + 1e-12
    )


@pytest.mark.parametrize(
    "composition",
    [
        "top_left",
        "top_center",
        "top_right",
        "center_left",
        "center",
        "center_right",
        "bottom_left",
        "bottom_center",
        "bottom_right",
    ],
)
def test_smart_expected_box_contains_safe_box_after_anchor_positioning(composition):
    node = SmartExpectedBox()
    result = node.calculate(
        orig_w=1000,
        orig_h=800,
        target_w=1,
        target_h=1,
        crop_box=[417, 233, 568, 386],
        safety_padding_px=17,
        composition=composition,
    )
    safe_box = result[-1]["safe_box"]
    expected_box = result[-1]["expected_box"]

    expected_left, expected_top, expected_right, expected_bottom = _box_edges(expected_box)
    safe_left, safe_top, safe_right, safe_bottom = _box_edges(safe_box)
    assert expected_left <= safe_left
    assert expected_top <= safe_top
    assert expected_right >= safe_right
    assert expected_bottom >= safe_bottom


def test_smart_expected_box_enlarges_off_center_expected_box_to_protect_safe_box():
    node = SmartExpectedBox()
    common_inputs = {
        "orig_w": 1000,
        "orig_h": 800,
        "target_w": 1,
        "target_h": 1,
        "crop_box": [417, 233, 568, 386],
        "safety_padding_px": 17,
    }

    center_box = node.calculate(**common_inputs, composition="center")[-1]["expected_box"]
    left_box = node.calculate(**common_inputs, composition="center_left")[-1]["expected_box"]
    right_box = node.calculate(**common_inputs, composition="center_right")[-1]["expected_box"]

    assert left_box[2] > center_box[2]
    assert right_box[2] > center_box[2]


@pytest.mark.parametrize("composition", ["top_left", "center", "bottom_right"])
def test_smart_expected_box_preserves_ratio_and_crop_pad_exclusivity(composition):
    node = SmartExpectedBox()
    crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom, box_data = node.calculate(
        orig_w=200,
        orig_h=200,
        target_w=16,
        target_h=9,
        crop_box=[50, 50, 150, 150],
        safety_padding_px=25,
        composition=composition,
    )

    expected_width, expected_height = box_data["output_size"]
    assert expected_width / expected_height == pytest.approx(16 / 9, abs=0.01)
    assert all(value >= 0 and isinstance(value, int) for value in (crop_left, crop_right, crop_top, crop_bottom))
    assert all(value >= 0 and isinstance(value, int) for value in (pad_left, pad_right, pad_top, pad_bottom))
    assert not (crop_left and pad_left)
    assert not (crop_right and pad_right)
    assert not (crop_top and pad_top)
    assert not (crop_bottom and pad_bottom)


@pytest.mark.parametrize("composition", ["", "Centerish", "Top", "CENTER", "left", None, 0])
def test_smart_expected_box_rejects_invalid_composition(composition):
    node = SmartExpectedBox()

    with pytest.raises(ValueError, match="composition"):
        node.calculate(
            orig_w=200,
            orig_h=200,
            target_w=1920,
            target_h=1080,
            crop_box=[50, 50, 150, 150],
            safety_padding_px=25,
            composition=composition,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"orig_w": 0},
        {"orig_h": 0},
        {"target_w": 0},
        {"target_h": 0},
        {"safety_padding_px": -1},
        {"crop_box": [100, 20, 10, 30]},
        {"crop_box": [0, 0, 10]},
        {"crop_box": [0, 0, float("nan"), 10]},
    ],
)
def test_smart_expected_box_rejects_invalid_geometry_inputs(overrides):
    node = SmartExpectedBox()
    inputs = {
        "orig_w": 200,
        "orig_h": 200,
        "target_w": 1920,
        "target_h": 1080,
        "crop_box": [50, 50, 150, 150],
        "safety_padding_px": 25,
    }
    inputs.update(overrides)

    with pytest.raises(ValueError):
        node.calculate(**inputs)
