import torch

from nodes.smart_expected_box_debugger import SmartExpectedBoxDebugger


def test_smart_expected_box_debugger():
    node = SmartExpectedBoxDebugger()

    # Create a dummy image tensor (batch, height, width, channels)
    image = torch.zeros((1, 100, 100, 3))

    box_data = {"safe_box": [10, 10, 50, 50], "expected_box": [0, 0, 100, 100]}

    # Should return an image tensor
    (result,) = node.draw(image, box_data)

    assert result.shape == (1, 100, 100, 3)
    assert isinstance(result, torch.Tensor)
