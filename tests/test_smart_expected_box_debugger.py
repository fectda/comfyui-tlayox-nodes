import torch

from nodes.smart_expected_box_debugger import SmartExpectedBoxDebugger


def test_smart_expected_box_debugger():
    node = SmartExpectedBoxDebugger()

    # Create a dummy image tensor (batch, height, width, channels)
    image = torch.zeros((1, 100, 100, 3))

    box_data = {
        "detected_box": [20, 20, 20, 20],
        "safe_box": [10, 10, 50, 50],
        "expected_box": [0, 0, 100, 100],
    }

    # Should return an image tensor
    (result,) = node.draw(image, box_data)

    assert result.shape == (1, 100, 100, 3)
    assert isinstance(result, torch.Tensor)


def test_smart_expected_box_debugger_draws_detected_safe_and_expected_boxes():
    node = SmartExpectedBoxDebugger()
    image = torch.zeros((2, 40, 40, 3), dtype=torch.float32)
    original = image.clone()
    box_data = {
        "detected_box": [8, 8, 8, 8],
        "safe_box": [2, 2, 24, 24],
        "expected_box": [0, 0, 40, 40],
    }

    (result,) = node.draw(image, box_data)

    assert result.shape == image.shape
    assert torch.equal(image, original)
    assert torch.equal(result[0, 8, 8], torch.tensor([0.0, 0.0, 1.0]))
    assert torch.equal(result[0, 6, 6], torch.tensor([1.0, 0.0, 0.0]))
    assert torch.equal(result[0, 0, 0], torch.tensor([0.0, 128.0 / 255.0, 0.0]))
    assert torch.equal(result[1], result[0])


def test_smart_expected_box_debugger_draws_selected_composition_guide_line():
    node = SmartExpectedBoxDebugger()
    image = torch.zeros((1, 40, 40, 3), dtype=torch.float32)
    box_data = {
        "detected_box": [8, 8, 8, 8],
        "safe_box": [2, 2, 24, 24],
        "expected_box": [0, 0, 30, 30],
        "composition": "center_left",
        "composition_anchor_x": 1 / 3,
    }

    (result,) = node.draw(image, box_data)

    assert torch.equal(result[0, 15, 10], torch.tensor([1.0, 1.0, 0.0]))


def test_smart_expected_box_debugger_draws_horizontal_and_vertical_guides():
    node = SmartExpectedBoxDebugger()
    image = torch.zeros((1, 40, 40, 3), dtype=torch.float32)
    box_data = {
        "detected_box": [8, 8, 8, 8],
        "safe_box": [2, 2, 24, 24],
        "expected_box": [0, 0, 30, 30],
        "composition": "bottom_right",
        "composition_anchor_x": 2 / 3,
        "composition_anchor_y": 2 / 3,
    }

    (result,) = node.draw(image, box_data)

    assert torch.equal(result[0, 15, 20], torch.tensor([1.0, 1.0, 0.0]))
    assert torch.equal(result[0, 20, 15], torch.tensor([0.0, 1.0, 1.0]))
