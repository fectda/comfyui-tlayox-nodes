"""Read native VIDEO dimensions while preserving the original video object."""

from numbers import Integral


class VideoDimensions:
    """Pass through a native ComfyUI VIDEO and expose its pixel dimensions."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"video": ("VIDEO",)}}

    RETURN_TYPES = ("VIDEO", "INT", "INT")
    RETURN_NAMES = ("video", "width", "height")
    FUNCTION = "get_dimensions"
    CATEGORY = "Tlayox/Utils"

    def get_dimensions(self, video):
        """Return the original video and its native width and height metadata."""
        if video is None:
            raise ValueError("video is required")

        get_dimensions = getattr(video, "get_dimensions", None)
        if not callable(get_dimensions):
            raise ValueError("video must be a native VIDEO object with get_dimensions()")

        try:
            dimensions = get_dimensions()
        except Exception as error:
            raise ValueError("video dimensions could not be read") from error

        try:
            width, height = dimensions
        except (TypeError, ValueError) as error:
            raise ValueError("video get_dimensions() must return width and height") from error

        if (
            isinstance(width, bool)
            or isinstance(height, bool)
            or not isinstance(width, Integral)
            or not isinstance(height, Integral)
            or width < 1
            or height < 1
        ):
            raise ValueError("video get_dimensions() must return positive integer dimensions")

        return video, int(width), int(height)
