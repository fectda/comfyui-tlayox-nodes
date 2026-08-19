from nodes.smart_expected_box import SmartExpectedBox


def test_smart_expected_box_basic():
    node = SmartExpectedBox()
    # orig: 1000x1000, target: 1080x1920 (9:16)
    # crop_box: x1=400, y1=400, x2=600, y2=600 (w=200, h=200, center=500,500)
    # margin: 0.2 -> safe_w = 240, safe_h = 240 (safe_ar = 1.0)
    # target_ar = 9/16 = 0.5625
    # safe_ar > target_ar -> exp_w = 240, exp_h = 240 / (9/16) = 426.66 -> 427
    # exp_left = 500 - 120 = 380, exp_right = 380 + 240 = 620
    # exp_top = 500 - 213.5 -> 286, exp_bottom = 286 + 427 = 713
    # crop_left = 380, pad_left = 0
    # crop_right = 1000 - 620 = 380, pad_right = 0
    # crop_top = 286, pad_top = 0
    # crop_bottom = 1000 - 713 = 287, pad_bottom = 0

    cl, cr, ct, cb, pl, pr, pt, pb, box_data = node.calculate(
        orig_w=1000, orig_h=1000, target_w=1080, target_h=1920, crop_box=[400, 400, 600, 600], margin=0.2
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
    assert box_data["safe_box"] == [380, 380, 240, 240]
    assert box_data["expected_box"] == [380, 286, 240, 427]


def test_smart_expected_box_needs_padding():
    node = SmartExpectedBox()
    # orig: 200x200, target: 1920x1080 (16:9)
    # crop_box: x1=50, y1=50, x2=150, y2=150 (w=100, h=100, center=100,100)
    # margin: 0.5 -> safe_w = 150, safe_h = 150
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
        orig_w=200, orig_h=200, target_w=1920, target_h=1080, crop_box=[50, 50, 150, 150], margin=0.5
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
