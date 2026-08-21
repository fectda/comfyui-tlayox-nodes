"""Hostless checks for the child-owned SmartExpectedBox development workflow."""

import json
from pathlib import Path

from nodes.instagram_preset_size import PRESETS, InstagramPresetSize
from workflows.make_smart_expected_box_debug_workflow import DEFAULT_PRESET, build_workflow

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPOSITORY_ROOT / "workflows/smart_expected_box_debug_workflow.json"

REGISTERED_NODE_TYPES = {
    "InstagramPresetSize",
    "SmartExpectedBox",
    "SmartCropExtend",
    "SmartExpectedBoxDebugger",
    "ImagePadForOutpaint",
    "DrawMaskOnImage",
    "ImageScaleToTotalPixels",
    "ImageResizeKJv2",
    "MaskToImage",
}

SQUARE_OUTPAINT_SUBGRAPH_ID = "fd81eb59-7179-4535-bb32-3a6893b83b54"

CANONICAL_COMPOSITION_POSITIONS = [
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
]


def _normalise_node_id(value):
    return str(value)


def _normalise_slot(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _class_matches(class_type, expected):
    class_type = str(class_type)
    return class_type == expected or class_type.endswith(f": {expected}") or class_type.endswith(f"::{expected}")


def _node_input_names(node):
    inputs = node.get("inputs", {})
    if isinstance(inputs, dict):
        return {str(name) for name in inputs}
    if isinstance(inputs, list):
        return {
            str(input_definition["name"])
            for input_definition in inputs
            if isinstance(input_definition, dict) and "name" in input_definition
        }
    return set()


def _node_input_name(node, slot):
    inputs = node.get("inputs", {})
    if isinstance(inputs, list) and 0 <= slot < len(inputs):
        input_definition = inputs[slot]
        if isinstance(input_definition, dict):
            return input_definition.get("name")
    return None


def _extract_nodes(workflow):
    """Return ``node_id -> node`` for API- and UI-style workflow JSON."""
    if isinstance(workflow.get("nodes"), list):
        return {
            _normalise_node_id(node["id"]): node
            for node in workflow["nodes"]
            if isinstance(node, dict) and "id" in node
        }

    api_graph = workflow.get("prompt", workflow)
    if not isinstance(api_graph, dict):
        return {}
    return {
        _normalise_node_id(node_id): node
        for node_id, node in api_graph.items()
        if isinstance(node, dict) and ("class_type" in node or "type" in node)
    }


def _extract_edges(workflow, nodes):
    """Return ``(source_id, source_slot, target_id, target_input)`` edges."""
    edges = set()

    links = workflow.get("links", [])
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, list) or len(link) < 5:
                continue
            _, source_id, source_slot, target_id, target_slot = link[:5]
            source_slot = _normalise_slot(source_slot)
            target_slot = _normalise_slot(target_slot)
            if source_slot is None or target_slot is None:
                continue
            target = nodes.get(_normalise_node_id(target_id), {})
            target_input = _node_input_name(target, target_slot)
            if target_input is not None:
                edges.add(
                    (
                        _normalise_node_id(source_id),
                        source_slot,
                        _normalise_node_id(target_id),
                        str(target_input),
                    )
                )

    for target_id, node in nodes.items():
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for target_input, value in inputs.items():
            references = value if isinstance(value, list) and value and isinstance(value[0], list) else [value]
            for reference in references:
                if not isinstance(reference, (list, tuple)) or len(reference) < 2:
                    continue
                source_slot = _normalise_slot(reference[1])
                if source_slot is None:
                    continue
                edges.add(
                    (
                        _normalise_node_id(reference[0]),
                        source_slot,
                        target_id,
                        str(target_input),
                    )
                )

    return edges


def _class_type(node):
    return node.get("class_type", node.get("type", ""))


def _node_ids(nodes, expected):
    return {node_id for node_id, node in nodes.items() if _class_matches(_class_type(node), expected)}


def _single_node(nodes, expected):
    matching = _node_ids(nodes, expected)
    assert len(matching) == 1, f"Expected exactly one {expected} node, found {matching}"
    return nodes[next(iter(matching))]


def _input_definition(node, input_name):
    return next(
        input_definition for input_definition in node.get("inputs", []) if input_definition.get("name") == input_name
    )


def _assert_link(edges, source_ids, source_slot, target_ids, target_inputs):
    target_inputs = set(target_inputs)
    assert any(
        source_id in source_ids and slot == source_slot and target_id in target_ids and target_input in target_inputs
        for source_id, slot, target_id, target_input in edges
    ), f"Missing link from {source_ids} slot {source_slot} to {target_ids} inputs {target_inputs}"


def _target_ids_for_link(edges, source_ids, source_slot, target_ids, target_inputs):
    target_inputs = set(target_inputs)
    return {
        target_id
        for source_id, slot, target_id, target_input in edges
        if source_id in source_ids and slot == source_slot and target_id in target_ids and target_input in target_inputs
    }


def _load_workflow(path):
    with path.open(encoding="utf-8") as workflow_file:
        workflow = json.load(workflow_file)
    assert isinstance(workflow, dict), "workflow JSON must contain an object"
    return workflow


def _vsr_rounded_dimensions(width, height):
    """Mirror ImageResizeKJv2's RTX VSR alignment rounding for graph checks."""
    return max(8, round(width / 8) * 8), max(8, round(height / 8) * 8)


def test_workflow_graph_parser_supports_api_and_ui_links():
    """Keep the hostless parser covered without requiring a ComfyUI runtime."""
    api_workflow = {
        "1": {"class_type": "LoadImage", "inputs": {}},
        "2": {"class_type": "SmartExpectedBox", "inputs": {"image": ["1", 0]}},
    }
    api_nodes = _extract_nodes(api_workflow)
    api_edges = _extract_edges(api_workflow, api_nodes)
    assert ("1", 0, "2", "image") in api_edges

    ui_workflow = {
        "nodes": [
            {"id": 1, "type": "LoadImage", "inputs": []},
            {"id": 2, "type": "SmartExpectedBox", "inputs": [{"name": "image"}]},
        ],
        "links": [[1, 1, 0, 2, 0, "IMAGE"]],
    }
    ui_nodes = _extract_nodes(ui_workflow)
    ui_edges = _extract_edges(ui_workflow, ui_nodes)
    assert ("1", 0, "2", "image") in ui_edges


def test_generated_workflow_matches_authoritative_generator():
    """Ensure the committed JSON is exactly the generator's deterministic output."""
    assert _load_workflow(WORKFLOW_PATH) == build_workflow()


def test_smart_expected_box_workflow_contract():
    """Validate the child-owned UI graph without requiring a ComfyUI runtime."""
    assert WORKFLOW_PATH.is_file(), f"Missing child-owned workflow artifact: {WORKFLOW_PATH}"

    workflow = _load_workflow(WORKFLOW_PATH)
    nodes = _extract_nodes(workflow)
    edges = _extract_edges(workflow, nodes)
    assert nodes, f"{WORKFLOW_PATH} does not contain a supported API/UI node graph"
    assert isinstance(workflow.get("nodes"), list)
    assert all(len(node.get("pos", ())) == 2 and len(node.get("size", ())) == 2 for node in workflow["nodes"])
    assert all(isinstance(link, list) and len(link) >= 6 for link in workflow.get("links", []))

    for expected in REGISTERED_NODE_TYPES:
        assert _node_ids(nodes, expected), f"{WORKFLOW_PATH} is missing registered node {expected}"

    image_loader = _node_ids(nodes, "LoadImage")
    size_node = _node_ids(nodes, "GetImageSizeAndCount")
    rmbg = _node_ids(nodes, "RMBG")
    mask_box = _node_ids(nodes, "MaskBoxDetect")
    preset = _node_ids(nodes, "InstagramPresetSize")
    router = _node_ids(nodes, "SmartExpectedBox")
    executor = _node_ids(nodes, "SmartCropExtend")
    debugger = _node_ids(nodes, "SmartExpectedBoxDebugger")
    pad = _node_ids(nodes, "ImagePadForOutpaint")
    draw_mask = _node_ids(nodes, "DrawMaskOnImage")
    scale = _node_ids(nodes, "ImageScaleToTotalPixels")
    resize_nodes = _node_ids(nodes, "ImageResizeKJv2")
    mask_to_image = _node_ids(nodes, "MaskToImage")
    previews = _node_ids(nodes, "PreviewImage")
    model = _node_ids(nodes, SQUARE_OUTPAINT_SUBGRAPH_ID)

    assert (
        image_loader
        and size_node
        and rmbg
        and mask_box
        and preset
        and router
        and executor
        and debugger
        and pad
        and draw_mask
        and scale
        and resize_nodes
        and mask_to_image
        and model
    )
    assert len(resize_nodes) == 2
    assert len(previews) >= 6, f"{WORKFLOW_PATH} needs geometry, green-image, mask, model, and final previews"
    assert len(pad) == 1, f"{WORKFLOW_PATH} must perform padding exactly once"
    assert len(model) == 1, f"{WORKFLOW_PATH} must embed the existing square outpaint block exactly once"

    mask_box_node = _single_node(nodes, "LayerMask: MaskBoxDetect")
    assert mask_box_node["widgets_values"] == ["mask_area"]

    router_node = nodes[next(iter(router))]
    router_inputs = _node_input_names(router_node)
    assert "safety_padding_px" in router_inputs
    assert "composition" in router_inputs
    safety_input = next(
        input_definition
        for input_definition in router_node["inputs"]
        if input_definition.get("name") == "safety_padding_px"
    )
    composition_input = next(
        input_definition for input_definition in router_node["inputs"] if input_definition.get("name") == "composition"
    )
    assert "link" not in safety_input
    assert safety_input["widget"] == {"name": "safety_padding_px"}
    assert "link" not in composition_input
    assert composition_input["widget"] == {"name": "composition"}
    assert router_node["widgets_values"] == [20, "center"]
    assert router_node["size"][1] >= 450
    assert router_node["properties"]["composition_grid"] == {
        "type": "radio_grid",
        "positions": CANONICAL_COMPOSITION_POSITIONS,
        "default": "center",
    }

    _assert_link(edges, image_loader, 0, size_node, {"image"})
    _assert_link(edges, image_loader, 0, rmbg, {"image"})
    _assert_link(edges, rmbg, 1, mask_box, {"mask"})
    _assert_link(edges, mask_box, 7, router, {"crop_box"})

    # These slots are the proven width/height links from the read-only host reference.
    _assert_link(edges, size_node, 1, router, {"orig_w"})
    _assert_link(edges, size_node, 2, router, {"orig_h"})
    _assert_link(edges, preset, 0, router, {"target_w"})
    _assert_link(edges, preset, 1, router, {"target_h"})

    directional_names = (
        "crop_left",
        "crop_right",
        "crop_top",
        "crop_bottom",
    )
    executor_node = nodes[next(iter(executor))]
    executor_inputs = {name.lower() for name in _node_input_names(executor_node)}
    assert set(directional_names) <= executor_inputs
    for slot, input_name in enumerate(directional_names):
        _assert_link(edges, router, slot, executor, {input_name})
    _assert_link(edges, image_loader, 0, executor, {"image"})

    # SmartCropExtend is the existing crop-only fallback. Its four pad inputs
    # must remain literal zero widgets so ImagePadForOutpaint is the only pad.
    for input_name in ("pad_left", "pad_right", "pad_top", "pad_bottom"):
        input_definition = _input_definition(executor_node, input_name)
        assert "link" not in input_definition
        assert input_definition.get("widget") == {"name": input_name}
    assert executor_node["widgets_values"] == [0, 0, 0, 0]
    assert not any(source_id in executor and source_slot == 1 for source_id, source_slot, _, _ in edges)

    pad_node = _single_node(nodes, "ImagePadForOutpaint")
    assert pad_node["widgets_values"] == [0, 0, 0, 0, 40]
    assert _input_definition(pad_node, "feathering")["widget"] == {"name": "feathering"}
    _assert_link(edges, executor, 0, pad, {"image"})
    _assert_link(edges, router, 4, pad, {"left"})
    _assert_link(edges, router, 6, pad, {"top"})
    _assert_link(edges, router, 5, pad, {"right"})
    _assert_link(edges, router, 7, pad, {"bottom"})

    draw_mask_node = _single_node(nodes, "DrawMaskOnImage")
    assert draw_mask_node["widgets_values"][0].replace(" ", "") == "0,255,0"
    _assert_link(edges, pad, 0, draw_mask, {"image"})
    _assert_link(edges, pad, 1, draw_mask, {"mask"})

    scale_node = _single_node(nodes, "ImageScaleToTotalPixels")
    assert 0.9 <= float(scale_node["widgets_values"][1]) <= 1.1
    _assert_link(edges, draw_mask, 0, scale, {"image"})

    model_node = _single_node(nodes, SQUARE_OUTPAINT_SUBGRAPH_ID)
    assert model_node["properties"]["outpaint_block_name"] == "Square Outpaint"
    _assert_link(edges, scale, 0, model, {"image"})
    assert not any(
        source_id in {next(iter(pad)), next(iter(mask_to_image))} and target_id in model
        for source_id, _, target_id, _ in edges
    )
    assert "mask" not in _node_input_names(model_node)
    definitions = workflow.get("definitions", {})
    subgraphs = definitions.get("subgraphs", []) if isinstance(definitions, dict) else []
    assert any(
        subgraph.get("id") == SQUARE_OUTPAINT_SUBGRAPH_ID and subgraph.get("name") == "Square Outpaint"
        for subgraph in subgraphs
    )

    mask_preview = _target_ids_for_link(edges, pad, 1, mask_to_image, {"mask"})
    assert mask_preview == {next(iter(mask_to_image))}
    _assert_link(edges, mask_to_image, 0, previews, {"images"})
    _assert_link(edges, draw_mask, 0, previews, {"images"})

    node_types = {_class_type(node) for node in nodes.values()}
    assert "ImageScale" not in node_types
    assert not any(
        any(forbidden in str(node_type) for forbidden in ("RealESRGAN", "UpscaleModelLoader", "ImageUpscaleWithModel"))
        for node_type in node_types
    )

    resize_by_method = {}
    for resize_id in resize_nodes:
        resize_node = nodes[resize_id]
        method = resize_node["widgets_values"][2]
        assert method not in resize_by_method, f"Duplicate ImageResizeKJv2 method: {method}"
        resize_by_method[method] = resize_id
        assert _input_definition(resize_node, "width")["widget"] == {"name": "width"}
        assert _input_definition(resize_node, "height")["widget"] == {"name": "height"}
        assert resize_node["widgets_values"][0:2] == list(PRESETS[DEFAULT_PRESET])
        assert resize_node["widgets_values"][3] == "stretch"
        assert resize_node["widgets_values"][4] == "0, 0, 0"
        assert resize_node["widgets_values"][5] == "center"
        assert resize_node["widgets_values"][6] == 1
        assert resize_node["widgets_values"][7] == "cpu"
        _assert_link(edges, preset, 0, {resize_id}, {"width"})
        _assert_link(edges, preset, 1, {resize_id}, {"height"})

    assert set(resize_by_method) == {"nvidia_rtx_vsr", "lanczos"}
    vsr_resize = {resize_by_method["nvidia_rtx_vsr"]}
    exact_resize = {resize_by_method["lanczos"]}
    _assert_link(edges, model, 0, vsr_resize, {"image"})
    _assert_link(edges, vsr_resize, 0, exact_resize, {"image"})

    final_previews = {
        preview_id
        for preview_id in previews
        if nodes[preview_id].get("properties", {}).get("preview_role") == "final_output"
    }
    assert len(final_previews) == 1
    assert _target_ids_for_link(edges, exact_resize, 0, previews, {"images"}) == final_previews

    _assert_link(edges, image_loader, 0, debugger, {"image"})
    _assert_link(edges, router, 8, debugger, {"BOX_DATA"})

    geometry_previews = _target_ids_for_link(edges, debugger, 0, previews, {"images"})
    prepared_previews = _target_ids_for_link(edges, scale, 0, previews, {"images"})
    mask_previews = _target_ids_for_link(edges, mask_to_image, 0, previews, {"images"})
    assert len(geometry_previews) == 1
    assert len(prepared_previews) == 1
    assert len(mask_previews) == 1
    assert final_previews.isdisjoint(geometry_previews)
    assert final_previews.isdisjoint(prepared_previews)
    assert final_previews.isdisjoint(mask_previews)
    assert geometry_previews.isdisjoint(prepared_previews)
    assert geometry_previews.isdisjoint(mask_previews)
    assert prepared_previews.isdisjoint(mask_previews)

    crop_types = {
        str(class_type)
        for class_type in {_class_type(node) for node in nodes.values()}
        if "crop" in str(class_type).lower()
    }
    assert crop_types <= {"SmartCropExtend"}, f"Unexpected custom crop node(s): {crop_types}"
    pad_types = {
        str(class_type)
        for class_type in {_class_type(node) for node in nodes.values()}
        if "pad" in str(class_type).lower()
    }
    assert pad_types == {"ImagePadForOutpaint"}


def test_instagram_preset_selector_represents_all_target_dimensions():
    """Ensure every Instagram target pair remains available to both resize links."""
    options = InstagramPresetSize.INPUT_TYPES()["required"]["preset"][0]

    assert tuple(options) == tuple(PRESETS)
    assert {PRESETS[preset] for preset in options} == set(PRESETS.values())
    assert all(f"{width}x{height}" in preset for preset, (width, height) in PRESETS.items())


def test_kj_vsr_alignment_requires_exact_correction_for_each_instagram_preset():
    """Validate RTX VSR rounding against every target represented by the selector."""
    rounded_dimensions = {dimensions: _vsr_rounded_dimensions(*dimensions) for dimensions in PRESETS.values()}

    assert rounded_dimensions == {
        (1080, 1920): (1080, 1920),
        (1080, 1350): (1080, 1352),
        (1080, 1080): (1080, 1080),
        (1080, 566): (1080, 568),
        (320, 320): (320, 320),
    }
    assert {dimensions for dimensions, rounded in rounded_dimensions.items() if dimensions != rounded} == {
        (1080, 1350),
        (1080, 566),
    }
