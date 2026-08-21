import pytest
import torch

from nodes.smart_crop_extend import SmartCropExtend
from nodes.smart_expected_box import SmartExpectedBox
from tests.smart_expected_box_case_matrix import MATRIX_CASES

DIRECTION_NAMES = (
    "crop_left",
    "crop_right",
    "crop_top",
    "crop_bottom",
    "pad_left",
    "pad_right",
    "pad_top",
    "pad_bottom",
)
DIRECTION_COMBINATIONS = tuple(
    tuple((value >> bit) & 1 for bit in range(len(DIRECTION_NAMES))) for value in range(2 ** len(DIRECTION_NAMES))
)


def _execute(node, image, **overrides):
    directions = {
        "crop_left": 0,
        "crop_right": 0,
        "crop_top": 0,
        "crop_bottom": 0,
        "pad_left": 0,
        "pad_right": 0,
        "pad_top": 0,
        "pad_bottom": 0,
    }
    directions.update(overrides)
    return node.execute(image=image, **directions)


def test_smart_crop_extend_maps_crop_and_pad_directions_without_resizing():
    node = SmartCropExtend()
    image = torch.arange(20, dtype=torch.float32).reshape(1, 4, 5, 1)

    output, mask = _execute(
        node,
        image,
        crop_left=1,
        crop_right=1,
        crop_top=1,
        crop_bottom=1,
        pad_left=2,
        pad_right=1,
        pad_top=1,
        pad_bottom=2,
    )

    assert output.shape == (1, 5, 6, 1)
    assert mask.shape == (1, 5, 6)
    assert torch.equal(output[0, 1:3, 2:5, 0], image[0, 1:3, 1:4, 0])
    assert torch.count_nonzero(output[0, :1]) == 0
    assert torch.count_nonzero(output[0, 3:]) == 0
    assert torch.count_nonzero(output[0, :, :2]) == 0
    assert torch.count_nonzero(output[0, :, 5:]) == 0

    assert mask.dtype == torch.float32
    assert torch.all(mask[:, 1:3, 2:5] == 0)
    assert torch.all(mask[:, :1] == 1)
    assert torch.all(mask[:, 3:] == 1)
    assert torch.all(mask[:, :, :2] == 1)
    assert torch.all(mask[:, :, 5:] == 1)


def test_smart_crop_extend_consumes_smart_expected_box_output_order():
    router = SmartExpectedBox()
    executor = SmartCropExtend()
    image = torch.arange(400, dtype=torch.float32).reshape(1, 20, 20, 1)
    routed = router.calculate(
        orig_w=20,
        orig_h=20,
        target_w=1,
        target_h=2,
        crop_box=[8, 8, 12, 12],
        safety_padding_px=2,
    )

    output, mask = executor.execute(image, *routed[:8])

    assert output.shape[2:4] == (routed[8]["output_size"][0], 1)
    assert output.shape[1] == routed[8]["output_size"][1]
    assert mask.shape == output.shape[:3]


def test_smart_crop_extend_is_batch_aware_and_does_not_mutate_input():
    node = SmartCropExtend()
    image = torch.stack(
        [
            torch.arange(12, dtype=torch.float32).reshape(3, 4, 1),
            torch.arange(12, 24, dtype=torch.float32).reshape(3, 4, 1),
        ]
    )
    original = image.clone()

    output, mask = _execute(node, image, crop_left=1, pad_right=2)

    assert output.shape == (2, 3, 5, 1)
    assert mask.shape == (2, 3, 5)
    assert torch.equal(output[:, :, :3], original[:, :, 1:])
    assert torch.all(output[:, :, 3:] == 0)
    assert torch.all(mask[:, :, :3] == 0)
    assert torch.all(mask[:, :, 3:] == 1)
    assert torch.equal(image, original)


@pytest.mark.parametrize("case", MATRIX_CASES, ids=lambda case: case.case_id)
def test_smart_crop_extend_realizes_every_matrix_router_result(case):
    router = SmartExpectedBox()
    executor = SmartCropExtend()
    original_width, original_height = case.original_size
    target_width, target_height = case.target_size
    routed = router.calculate(
        original_width,
        original_height,
        target_width,
        target_height,
        case.crop_box,
        case.safety_padding_px,
        case.composition,
    )
    image = torch.arange(2 * original_height * original_width * 2, dtype=torch.float32).reshape(
        2, original_height, original_width, 2
    )
    original = image.clone()

    output, mask = executor.execute(image, *routed[:8])
    crop_left, crop_right, crop_top, crop_bottom, pad_left, pad_right, pad_top, pad_bottom = routed[:8]
    expected_width, expected_height = routed[8]["output_size"]
    source = original[:, crop_top : original_height - crop_bottom, crop_left : original_width - crop_right, :]

    assert output.shape == (2, expected_height, expected_width, 2)
    assert mask.shape == (2, expected_height, expected_width)
    assert output.dtype == image.dtype
    assert output.device == image.device
    assert mask.dtype == torch.float32
    assert mask.device == image.device
    assert torch.equal(
        output[:, pad_top : pad_top + source.shape[1], pad_left : pad_left + source.shape[2], :],
        source,
    )

    expected_mask = torch.ones((2, expected_height, expected_width), dtype=torch.float32)
    expected_mask[:, pad_top : pad_top + source.shape[1], pad_left : pad_left + source.shape[2]] = 0.0
    assert torch.equal(mask, expected_mask)
    assert torch.equal(image, original)


@pytest.mark.parametrize("combination", DIRECTION_COMBINATIONS)
def test_smart_crop_extend_realizes_every_binary_direction_combination(combination):
    image = torch.arange(1 * 5 * 6 * 1, dtype=torch.float32).reshape(1, 5, 6, 1)
    directions = dict(zip(DIRECTION_NAMES, combination))
    output, mask = _execute(SmartCropExtend(), image, **directions)

    source = image[
        :,
        directions["crop_top"] : 5 - directions["crop_bottom"],
        directions["crop_left"] : 6 - directions["crop_right"],
        :,
    ]
    expected_height = source.shape[1] + directions["pad_top"] + directions["pad_bottom"]
    expected_width = source.shape[2] + directions["pad_left"] + directions["pad_right"]
    expected_mask = torch.ones((1, expected_height, expected_width), dtype=torch.float32)
    expected_mask[
        :,
        directions["pad_top"] : directions["pad_top"] + source.shape[1],
        directions["pad_left"] : directions["pad_left"] + source.shape[2],
    ] = 0.0

    assert output.shape == (1, expected_height, expected_width, 1)
    assert mask.shape == (1, expected_height, expected_width)
    assert torch.equal(
        output[
            :,
            directions["pad_top"] : directions["pad_top"] + source.shape[1],
            directions["pad_left"] : directions["pad_left"] + source.shape[2],
            :,
        ],
        source,
    )
    assert torch.equal(mask, expected_mask)


@pytest.mark.parametrize(
    "direction",
    [
        "crop_left",
        "crop_right",
        "crop_top",
        "crop_bottom",
        "pad_left",
        "pad_right",
        "pad_top",
        "pad_bottom",
    ],
)
def test_smart_crop_extend_supports_each_individual_direction(direction):
    image = torch.arange(1 * 5 * 6 * 1, dtype=torch.float32).reshape(1, 5, 6, 1)
    distance = 1

    output, mask = _execute(SmartCropExtend(), image, **{direction: distance})

    crop_left = distance if direction == "crop_left" else 0
    crop_right = distance if direction == "crop_right" else 0
    crop_top = distance if direction == "crop_top" else 0
    crop_bottom = distance if direction == "crop_bottom" else 0
    pad_left = distance if direction == "pad_left" else 0
    pad_right = distance if direction == "pad_right" else 0
    pad_top = distance if direction == "pad_top" else 0
    pad_bottom = distance if direction == "pad_bottom" else 0
    source = image[:, crop_top : 5 - crop_bottom, crop_left : 6 - crop_right, :]
    expected_height = source.shape[1] + pad_top + pad_bottom
    expected_width = source.shape[2] + pad_left + pad_right

    assert output.shape == (1, expected_height, expected_width, 1)
    assert mask.shape == (1, expected_height, expected_width)
    assert torch.equal(output[:, pad_top : pad_top + source.shape[1], pad_left : pad_left + source.shape[2], :], source)
    expected_mask = torch.ones((1, expected_height, expected_width), dtype=torch.float32)
    expected_mask[:, pad_top : pad_top + source.shape[1], pad_left : pad_left + source.shape[2]] = 0.0
    assert torch.equal(mask, expected_mask)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64, torch.int64])
def test_smart_crop_extend_preserves_dtype_device_and_input_for_supported_dtypes(dtype):
    image = torch.arange(2 * 4 * 5 * 3, dtype=dtype).reshape(2, 4, 5, 3)
    original = image.clone()

    output, mask = _execute(
        SmartCropExtend(),
        image,
        crop_left=1,
        crop_bottom=1,
        pad_right=2,
        pad_top=1,
    )

    assert output.dtype == dtype
    assert output.device == image.device
    assert mask.dtype == torch.float32
    assert mask.device == image.device
    assert torch.equal(image, original)


@pytest.mark.parametrize(
    "invalid_image",
    [
        "not-a-tensor",
        torch.zeros((4, 5, 3), dtype=torch.float32),
        torch.zeros((0, 4, 5, 3), dtype=torch.float32),
        torch.zeros((1, 0, 5, 3), dtype=torch.float32),
        torch.zeros((1, 4, 0, 3), dtype=torch.float32),
        torch.zeros((1, 4, 5, 0), dtype=torch.float32),
    ],
)
def test_smart_crop_extend_rejects_invalid_image_shapes(invalid_image):
    with pytest.raises(ValueError, match="image"):
        _execute(SmartCropExtend(), invalid_image)


@pytest.mark.parametrize(
    "direction",
    [
        "crop_left",
        "crop_right",
        "crop_top",
        "crop_bottom",
        "pad_left",
        "pad_right",
        "pad_top",
        "pad_bottom",
    ],
)
def test_smart_crop_extend_rejects_negative_directional_values(direction):
    node = SmartCropExtend()
    image = torch.zeros((1, 4, 5, 3), dtype=torch.float32)

    with pytest.raises(ValueError, match="non-negative"):
        _execute(node, image, **{direction: -1})


@pytest.mark.parametrize("invalid_value", [True, 1.5, "1", None])
def test_smart_crop_extend_rejects_non_integer_directional_values(invalid_value):
    image = torch.zeros((1, 4, 5, 3), dtype=torch.float32)

    with pytest.raises(ValueError, match="non-negative integer"):
        _execute(SmartCropExtend(), image, pad_right=invalid_value)


def test_smart_crop_extend_rejects_crop_that_removes_the_whole_source():
    node = SmartCropExtend()
    image = torch.zeros((1, 4, 5, 3), dtype=torch.float32)

    with pytest.raises(ValueError, match="crop"):
        _execute(node, image, crop_left=3, crop_right=2)


def test_smart_crop_extend_rejects_non_batched_images():
    node = SmartCropExtend()

    with pytest.raises(ValueError, match="shape"):
        _execute(node, torch.zeros((4, 5, 3), dtype=torch.float32))
