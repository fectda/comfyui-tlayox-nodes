import importlib.util
import sys
from pathlib import Path

import pytest

from nodes.video_dimensions import VideoDimensions


class MetadataOnlyVideo:
    """Minimal native VIDEO-shaped test double with metadata access only."""

    def __init__(self, width=1920, height=1080, dimensions=None):
        self.dimensions = (width, height) if dimensions is None else dimensions
        self.get_dimensions_calls = 0

    def get_dimensions(self):
        self.get_dimensions_calls += 1
        return self.dimensions

    def decode(self):
        raise AssertionError("the node must not decode video frames")

    def resize(self):
        raise AssertionError("the node must not resize video frames")

    def copy(self):
        raise AssertionError("the node must not copy the video")

    def save_to(self):
        raise AssertionError("the node must not encode or write the video")


def _load_registration_module():
    package_root = Path(__file__).resolve().parents[1]
    package_name = "tlayox_nodes_video_dimensions_registration_test"
    spec = importlib.util.spec_from_file_location(
        package_name,
        package_root / "__init__.py",
        submodule_search_locations=[str(package_root)],
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(package_name, None)

    return module


def test_video_dimensions_rejects_missing_video_with_clear_error():
    with pytest.raises(ValueError, match="video is required"):
        VideoDimensions().get_dimensions(None)


def test_video_dimensions_rejects_values_without_native_metadata_api():
    with pytest.raises(ValueError, match="native VIDEO"):
        VideoDimensions().get_dimensions(object())


@pytest.mark.parametrize(
    "dimensions,error_message",
    [
        ((0, 1080), "positive integer"),
        ((1920, 0), "positive integer"),
        ((1920.0, 1080), "positive integer"),
        ((True, 1080), "positive integer"),
        ((1920, 1080, 24), "width and height"),
    ],
)
def test_video_dimensions_rejects_invalid_native_metadata(dimensions, error_message):
    video = MetadataOnlyVideo(dimensions=dimensions)

    with pytest.raises(ValueError, match=error_message):
        VideoDimensions().get_dimensions(video)


def test_video_dimensions_passes_video_identity_and_reads_metadata_only():
    video = MetadataOnlyVideo(width=1280, height=720)

    result = VideoDimensions().get_dimensions(video)

    assert result == (video, 1280, 720)
    assert result[0] is video
    assert video.get_dimensions_calls == 1


def test_video_dimensions_declares_native_input_and_unambiguous_outputs():
    assert VideoDimensions.INPUT_TYPES() == {"required": {"video": ("VIDEO",)}}
    assert VideoDimensions.RETURN_TYPES == ("VIDEO", "INT", "INT")
    assert VideoDimensions.RETURN_NAMES == ("video", "width", "height")
    assert VideoDimensions.FUNCTION == "get_dimensions"


def test_video_dimensions_is_registered_with_display_name():
    module = _load_registration_module()

    assert module.NODE_CLASS_MAPPINGS["VideoDimensions"].__name__ == "VideoDimensions"
    assert module.NODE_DISPLAY_NAME_MAPPINGS["VideoDimensions"] == "📹 Video Dimensions"
