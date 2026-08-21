import importlib.util
import sys
from pathlib import Path


def _load_registration_module():
    package_root = Path(__file__).resolve().parents[1]
    package_name = "tlayox_nodes_registration_test"
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


def test_smart_expected_box_nodes_are_registered_without_host_runtime():
    module = _load_registration_module()

    assert module.NODE_CLASS_MAPPINGS["SmartExpectedBox"].__name__ == "SmartExpectedBox"
    assert module.NODE_CLASS_MAPPINGS["SmartCropExtend"].__name__ == "SmartCropExtend"
    assert module.NODE_CLASS_MAPPINGS["SmartExpectedBoxDebugger"].__name__ == "SmartExpectedBoxDebugger"
    assert module.NODE_DISPLAY_NAME_MAPPINGS["SmartCropExtend"] == "🖼️ Smart Crop Extend"


def test_smart_expected_box_registration_uses_fixed_pixel_padding():
    module = _load_registration_module()

    required = module.NODE_CLASS_MAPPINGS["SmartExpectedBox"].INPUT_TYPES()["required"]

    assert "margin" not in required
    assert required["safety_padding_px"] == ("INT", {"default": 20, "min": 0, "max": 8192})
