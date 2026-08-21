"""Generate the child-owned SmartExpectedBox development workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKFLOW_PATH = Path(__file__).with_name("smart_expected_box_debug_workflow.json")
DEFAULT_IMAGE = "example.png"
DEFAULT_PRESET = "Stories & Reels (1080x1920 - 9:16)"
DEFAULT_SAFETY_PADDING_PX = 20
DEFAULT_COMPOSITION = "center"
DEFAULT_OUTPAINT_MEGAPIXELS = 1.0
SQUARE_OUTPAINT_SUBGRAPH_ID = "fd81eb59-7179-4535-bb32-3a6893b83b54"
REFERENCE_CONDITIONING_SUBGRAPH_ID = "4a73b37e-5f4b-4852-bd13-56ee643dd5f3"
DEFAULT_OUTPAINT_PROMPT = "extend the image naturally"
DEFAULT_OUTPAINT_UNET = "flux-2-klein-9b-nvfp4.safetensors"
DEFAULT_OUTPAINT_CLIP = "qwen_3_8b_fp8mixed.safetensors"
DEFAULT_OUTPAINT_VAE = "flux2-vae.safetensors"
DEFAULT_OUTPAINT_SEED = 869001131783628
SMART_EXPECTED_BOX_NODE_SIZE = (330, 450)
COMPOSITION_POSITIONS = (
    "top_left",
    "top_center",
    "top_right",
    "center_left",
    "center",
    "center_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)


def _input(name: str, type_name: str, *, link: int | None = None, widget: bool = False) -> dict[str, Any]:
    """Build one UI-workflow input definition."""
    input_definition: dict[str, Any] = {"name": name, "type": type_name}
    if link is not None:
        input_definition["link"] = link
    if widget:
        input_definition["widget"] = {"name": name}
    return input_definition


def _output(name: str, type_name: str, slot: int, links: list[int] | None = None) -> dict[str, Any]:
    """Build one UI-workflow output definition."""
    return {"name": name, "type": type_name, "links": links, "slot_index": slot}


def _node(
    node_id: int,
    node_type: str,
    position: tuple[int, int],
    size: tuple[int, int],
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    widgets_values: list[Any],
    order: int,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic ComfyUI UI-style node record."""
    node = {
        "id": node_id,
        "type": node_type,
        "pos": list(position),
        "size": list(size),
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": node_type},
        "widgets_values": widgets_values,
    }
    if properties:
        node["properties"].update(properties)
    return node


def _image_resize_kjv2_node(
    node_id: int,
    position: tuple[int, int],
    image_link: int,
    width_link: int,
    height_link: int,
    output_link: int,
    upscale_method: str,
    order: int,
) -> dict[str, Any]:
    """Build a preset-driven KJNodes resize with widget links preserved."""
    return _node(
        node_id,
        "ImageResizeKJv2",
        position,
        (300, 340),
        [
            _input("image", "IMAGE", link=image_link),
            {"name": "mask", "shape": 7, "type": "MASK"},
            _input("width", "INT", link=width_link, widget=True),
            _input("height", "INT", link=height_link, widget=True),
            _input("upscale_method", "COMBO", widget=True),
            _input("keep_proportion", "COMBO", widget=True),
            _input("pad_color", "STRING", widget=True),
            _input("crop_position", "COMBO", widget=True),
            _input("divisible_by", "INT", widget=True),
            {"name": "device", "shape": 7, "type": "COMBO", "widget": {"name": "device"}},
        ],
        [
            _output("IMAGE", "IMAGE", 0, [output_link]),
            _output("width", "INT", 1, []),
            _output("height", "INT", 2, []),
            _output("mask", "MASK", 3, []),
        ],
        [1080, 1920, upscale_method, "stretch", "0, 0, 0", "center", 1, "cpu"],
        order,
        properties={
            "cnr_id": "comfyui-kjnodes",
            "ver": "bc8e4ce4254bcd0050383386ee2f9d753dbf1fa5",
            "ue_properties": {
                "version": "7.5.2",
                "widget_ue_connectable": {"width": True, "height": True},
                "input_ue_unconnectable": {},
            },
        },
    )


def _subgraph_node(
    node_id: int,
    node_type: str,
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    widgets_values: list[Any],
    order: int,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact node record for an embedded existing subgraph."""
    node = {
        "id": node_id,
        "type": node_type,
        "pos": [0, 0],
        "size": [280, 100],
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {
            "cnr_id": "comfy-core",
            "ver": "0.8.2",
            "Node name for S&R": node_type,
        },
        "widgets_values": widgets_values,
    }
    if properties:
        node["properties"].update(properties)
    return node


def _reference_conditioning_subgraph() -> dict[str, Any]:
    """Return the nested conditioning subgraph used by the existing outpaint block."""
    return {
        "id": REFERENCE_CONDITIONING_SUBGRAPH_ID,
        "version": 1,
        "state": {"lastGroupId": 0, "lastNodeId": 78, "lastLinkId": 170, "lastRerouteId": 0},
        "revision": 0,
        "config": {},
        "name": "Reference Conditioning",
        "inputNode": {"id": -10, "bounding": [-170, 1000, 128, 88]},
        "outputNode": {"id": -20, "bounding": [600, 980, 128, 68]},
        "inputs": [
            {"id": "reference-positive", "name": "conditioning", "type": "CONDITIONING", "linkIds": [165]},
            {
                "id": "reference-negative",
                "name": "conditioning_1",
                "type": "CONDITIONING",
                "linkIds": [166],
            },
            {"id": "reference-pixels", "name": "pixels", "type": "IMAGE", "linkIds": [167]},
            {"id": "reference-vae", "name": "vae", "type": "VAE", "linkIds": [168]},
        ],
        "outputs": [
            {"id": "reference-positive-output", "name": "CONDITIONING", "type": "CONDITIONING", "linkIds": [169]},
            {
                "id": "reference-negative-output",
                "name": "CONDITIONING_1",
                "type": "CONDITIONING",
                "linkIds": [170],
            },
        ],
        "widgets": [],
        "nodes": [
            _subgraph_node(
                76,
                "ReferenceLatent",
                [
                    {"name": "conditioning", "type": "CONDITIONING", "link": 166},
                    {"name": "latent", "type": "LATENT", "link": 163},
                ],
                [_output("CONDITIONING", "CONDITIONING", 0, [170])],
                [],
                1,
            ),
            _subgraph_node(
                78,
                "VAEEncode",
                [
                    {"name": "pixels", "type": "IMAGE", "link": 167},
                    {"name": "vae", "type": "VAE", "link": 168},
                ],
                [_output("LATENT", "LATENT", 0, [163, 164])],
                [],
                0,
            ),
            _subgraph_node(
                77,
                "ReferenceLatent",
                [
                    {"name": "conditioning", "type": "CONDITIONING", "link": 165},
                    {"name": "latent", "type": "LATENT", "link": 164},
                ],
                [_output("CONDITIONING", "CONDITIONING", 0, [169])],
                [],
                2,
            ),
        ],
        "groups": [],
        "links": [
            {"id": 163, "origin_id": 78, "origin_slot": 0, "target_id": 76, "target_slot": 1, "type": "LATENT"},
            {"id": 164, "origin_id": 78, "origin_slot": 0, "target_id": 77, "target_slot": 1, "type": "LATENT"},
            {"id": 165, "origin_id": -10, "origin_slot": 0, "target_id": 77, "target_slot": 0, "type": "CONDITIONING"},
            {"id": 166, "origin_id": -10, "origin_slot": 1, "target_id": 76, "target_slot": 0, "type": "CONDITIONING"},
            {"id": 167, "origin_id": -10, "origin_slot": 2, "target_id": 78, "target_slot": 0, "type": "IMAGE"},
            {"id": 168, "origin_id": -10, "origin_slot": 3, "target_id": 78, "target_slot": 1, "type": "VAE"},
            {"id": 169, "origin_id": 77, "origin_slot": 0, "target_id": -20, "target_slot": 0, "type": "CONDITIONING"},
            {"id": 170, "origin_id": 76, "origin_slot": 0, "target_id": -20, "target_slot": 1, "type": "CONDITIONING"},
        ],
        "extra": {"workflowRendererVersion": "LG", "pixaromaGroups": []},
    }


def _square_outpaint_subgraph() -> dict[str, Any]:
    """Return the existing square-outpaint graph without introducing a new node."""
    return {
        "id": SQUARE_OUTPAINT_SUBGRAPH_ID,
        "version": 1,
        "state": {"lastGroupId": 4, "lastNodeId": 146, "lastLinkId": 260, "lastRerouteId": 0},
        "revision": 0,
        "config": {},
        "name": "Square Outpaint",
        "inputNode": {"id": -10, "bounding": [-576, 559, 128, 188]},
        "outputNode": {"id": -20, "bounding": [1373, 549, 128, 68]},
        "inputs": [
            {"id": "outpaint-seed", "name": "noise_seed", "type": "INT", "linkIds": [158]},
            {"id": "outpaint-unet", "name": "unet_name", "type": "COMBO", "linkIds": [159]},
            {"id": "outpaint-clip", "name": "clip_name", "type": "COMBO", "linkIds": [160]},
            {"id": "outpaint-vae", "name": "vae_name", "type": "COMBO", "linkIds": [161]},
            {"id": "outpaint-prompt", "name": "text", "type": "STRING", "linkIds": [162], "label": "prompt"},
            {"id": "outpaint-image", "name": "image", "type": "IMAGE", "linkIds": [175]},
            {"id": "outpaint-megapixels", "name": "megapixels", "type": "FLOAT", "linkIds": [256]},
        ],
        "outputs": [
            {"id": "outpaint-image-output", "name": "IMAGE", "type": "IMAGE", "linkIds": [153]},
        ],
        "widgets": [],
        "nodes": [
            _subgraph_node(
                64,
                "SamplerCustomAdvanced",
                [
                    {"name": "noise", "type": "NOISE", "link": 142},
                    {"name": "guider", "type": "GUIDER", "link": 143},
                    {"name": "sampler", "type": "SAMPLER", "link": 144},
                    {"name": "sigmas", "type": "SIGMAS", "link": 145},
                    {"name": "latent_image", "type": "LATENT", "link": 146},
                ],
                [
                    _output("output", "LATENT", 0, [147]),
                    _output("denoised_output", "LATENT", 1, []),
                ],
                [],
                3,
            ),
            _subgraph_node(
                65,
                "VAEDecode",
                [
                    {"name": "samples", "type": "LATENT", "link": 147},
                    {"name": "vae", "type": "VAE", "link": 148},
                ],
                [_output("IMAGE", "IMAGE", 0, [153])],
                [],
                4,
            ),
            _subgraph_node(
                73,
                "RandomNoise",
                [{"name": "noise_seed", "type": "INT", "widget": {"name": "noise_seed"}, "link": 158}],
                [_output("NOISE", "NOISE", 0, [142])],
                [DEFAULT_OUTPAINT_SEED, "randomize"],
                9,
            ),
            _subgraph_node(
                70,
                "UNETLoader",
                [
                    {"name": "unet_name", "type": "COMBO", "widget": {"name": "unet_name"}, "link": 159},
                    {"name": "weight_dtype", "type": "COMBO", "widget": {"name": "weight_dtype"}, "link": None},
                ],
                [_output("MODEL", "MODEL", 0, [139])],
                [DEFAULT_OUTPAINT_UNET, "default"],
                6,
            ),
            _subgraph_node(
                71,
                "CLIPLoader",
                [
                    {"name": "clip_name", "type": "COMBO", "widget": {"name": "clip_name"}, "link": 160},
                    {"name": "type", "type": "COMBO", "widget": {"name": "type"}, "link": None},
                    {"name": "device", "type": "COMBO", "widget": {"name": "device"}, "link": None},
                ],
                [_output("CLIP", "CLIP", 0, [151])],
                [DEFAULT_OUTPAINT_CLIP, "flux2", "default"],
                7,
            ),
            _subgraph_node(
                72,
                "VAELoader",
                [{"name": "vae_name", "type": "COMBO", "widget": {"name": "vae_name"}, "link": 161}],
                [_output("VAE", "VAE", 0, [148, 176])],
                [DEFAULT_OUTPAINT_VAE],
                8,
            ),
            _subgraph_node(
                66,
                "EmptyFlux2LatentImage",
                [
                    {"name": "width", "type": "INT", "widget": {"name": "width"}, "link": 172},
                    {"name": "height", "type": "INT", "widget": {"name": "height"}, "link": 174},
                    {"name": "batch_size", "type": "INT", "widget": {"name": "batch_size"}, "link": None},
                ],
                [_output("LATENT", "LATENT", 0, [146])],
                [1024, 1024, 1],
                5,
            ),
            _subgraph_node(
                63,
                "CFGGuider",
                [
                    {"name": "model", "type": "MODEL", "link": 139},
                    {"name": "positive", "type": "CONDITIONING", "link": 167},
                    {"name": "negative", "type": "CONDITIONING", "link": 168},
                    {"name": "cfg", "type": "FLOAT", "widget": {"name": "cfg"}, "link": None},
                ],
                [_output("GUIDER", "GUIDER", 0, [143])],
                [1],
                2,
            ),
            _subgraph_node(
                62,
                "Flux2Scheduler",
                [
                    {"name": "steps", "type": "INT", "widget": {"name": "steps"}, "link": None},
                    {"name": "width", "type": "INT", "widget": {"name": "width"}, "link": 171},
                    {"name": "height", "type": "INT", "widget": {"name": "height"}, "link": 173},
                ],
                [_output("SIGMAS", "SIGMAS", 0, [145])],
                [4, 1024, 1024],
                1,
            ),
            _subgraph_node(
                82,
                "ConditioningZeroOut",
                [{"name": "conditioning", "type": "CONDITIONING", "link": 177}],
                [_output("CONDITIONING", "CONDITIONING", 0, [178])],
                [],
                14,
            ),
            _subgraph_node(
                81,
                "GetImageSize",
                [{"name": "image", "type": "IMAGE", "link": 170}],
                [
                    _output("width", "INT", 0, [171, 172]),
                    _output("height", "INT", 1, [173, 174]),
                    _output("batch_size", "INT", 2, []),
                ],
                [],
                13,
            ),
            _subgraph_node(
                79,
                REFERENCE_CONDITIONING_SUBGRAPH_ID,
                [
                    {"name": "conditioning", "type": "CONDITIONING", "link": 165},
                    {"name": "conditioning_1", "type": "CONDITIONING", "link": 178},
                    {"name": "pixels", "type": "IMAGE", "link": 169},
                    {"name": "vae", "type": "VAE", "link": 176},
                ],
                [
                    _output("CONDITIONING", "CONDITIONING", 0, [167]),
                    _output("CONDITIONING_1", "CONDITIONING", 1, [168]),
                ],
                [],
                11,
                properties={"proxyWidgets": []},
            ),
            _subgraph_node(
                61,
                "KSamplerSelect",
                [{"name": "sampler_name", "type": "COMBO", "widget": {"name": "sampler_name"}, "link": None}],
                [_output("SAMPLER", "SAMPLER", 0, [144])],
                ["euler"],
                0,
            ),
            _subgraph_node(
                74,
                "CLIPTextEncode",
                [
                    {"name": "clip", "type": "CLIP", "link": 151},
                    {"name": "text", "type": "STRING", "widget": {"name": "text"}, "link": 162},
                ],
                [_output("CONDITIONING", "CONDITIONING", 0, [165, 177])],
                [DEFAULT_OUTPAINT_PROMPT],
                10,
                properties={"title": "CLIP Text Encode (Positive Prompt)"},
            ),
            _subgraph_node(
                80,
                "ImageScaleToTotalPixels",
                [
                    {"name": "image", "type": "IMAGE", "link": 175},
                    {"name": "upscale_method", "type": "COMBO", "widget": {"name": "upscale_method"}, "link": None},
                    {"name": "megapixels", "type": "FLOAT", "widget": {"name": "megapixels"}, "link": 256},
                    {"name": "resolution_steps", "type": "INT", "widget": {"name": "resolution_steps"}, "link": None},
                ],
                [_output("IMAGE", "IMAGE", 0, [169, 170])],
                ["lanczos", DEFAULT_OUTPAINT_MEGAPIXELS, 1],
                12,
            ),
        ],
        "groups": [],
        "links": [
            {"id": 139, "origin_id": 70, "origin_slot": 0, "target_id": 63, "target_slot": 0, "type": "MODEL"},
            {"id": 142, "origin_id": 73, "origin_slot": 0, "target_id": 64, "target_slot": 0, "type": "NOISE"},
            {"id": 143, "origin_id": 63, "origin_slot": 0, "target_id": 64, "target_slot": 1, "type": "GUIDER"},
            {"id": 144, "origin_id": 61, "origin_slot": 0, "target_id": 64, "target_slot": 2, "type": "SAMPLER"},
            {"id": 145, "origin_id": 62, "origin_slot": 0, "target_id": 64, "target_slot": 3, "type": "SIGMAS"},
            {"id": 146, "origin_id": 66, "origin_slot": 0, "target_id": 64, "target_slot": 4, "type": "LATENT"},
            {"id": 147, "origin_id": 64, "origin_slot": 0, "target_id": 65, "target_slot": 0, "type": "LATENT"},
            {"id": 148, "origin_id": 72, "origin_slot": 0, "target_id": 65, "target_slot": 1, "type": "VAE"},
            {"id": 151, "origin_id": 71, "origin_slot": 0, "target_id": 74, "target_slot": 0, "type": "CLIP"},
            {"id": 153, "origin_id": 65, "origin_slot": 0, "target_id": -20, "target_slot": 0, "type": "IMAGE"},
            {"id": 158, "origin_id": -10, "origin_slot": 0, "target_id": 73, "target_slot": 0, "type": "INT"},
            {"id": 159, "origin_id": -10, "origin_slot": 1, "target_id": 70, "target_slot": 0, "type": "COMBO"},
            {"id": 160, "origin_id": -10, "origin_slot": 2, "target_id": 71, "target_slot": 0, "type": "COMBO"},
            {"id": 161, "origin_id": -10, "origin_slot": 3, "target_id": 72, "target_slot": 0, "type": "COMBO"},
            {"id": 162, "origin_id": -10, "origin_slot": 4, "target_id": 74, "target_slot": 1, "type": "STRING"},
            {"id": 165, "origin_id": 74, "origin_slot": 0, "target_id": 79, "target_slot": 0, "type": "CONDITIONING"},
            {"id": 167, "origin_id": 79, "origin_slot": 0, "target_id": 63, "target_slot": 1, "type": "CONDITIONING"},
            {"id": 168, "origin_id": 79, "origin_slot": 1, "target_id": 63, "target_slot": 2, "type": "CONDITIONING"},
            {"id": 169, "origin_id": 80, "origin_slot": 0, "target_id": 79, "target_slot": 2, "type": "IMAGE"},
            {"id": 170, "origin_id": 80, "origin_slot": 0, "target_id": 81, "target_slot": 0, "type": "IMAGE"},
            {"id": 171, "origin_id": 81, "origin_slot": 0, "target_id": 62, "target_slot": 1, "type": "INT"},
            {"id": 172, "origin_id": 81, "origin_slot": 0, "target_id": 66, "target_slot": 0, "type": "INT"},
            {"id": 173, "origin_id": 81, "origin_slot": 1, "target_id": 62, "target_slot": 2, "type": "INT"},
            {"id": 174, "origin_id": 81, "origin_slot": 1, "target_id": 66, "target_slot": 1, "type": "INT"},
            {"id": 175, "origin_id": -10, "origin_slot": 5, "target_id": 80, "target_slot": 0, "type": "IMAGE"},
            {"id": 176, "origin_id": 72, "origin_slot": 0, "target_id": 79, "target_slot": 3, "type": "VAE"},
            {"id": 177, "origin_id": 74, "origin_slot": 0, "target_id": 82, "target_slot": 0, "type": "CONDITIONING"},
            {"id": 178, "origin_id": 82, "origin_slot": 0, "target_id": 79, "target_slot": 1, "type": "CONDITIONING"},
            {"id": 256, "origin_id": -10, "origin_slot": 6, "target_id": 80, "target_slot": 2, "type": "FLOAT"},
        ],
        "extra": {"workflowRendererVersion": "LG", "pixaromaGroups": []},
    }


def build_workflow() -> dict[str, Any]:
    """Return the complete deterministic UI-style workflow graph."""
    nodes = [
        _node(
            1,
            "LoadImage",
            (40, 260),
            (260, 300),
            [],
            [],
            [DEFAULT_IMAGE, "image"],
            0,
        ),
        _node(
            2,
            "GetImageSizeAndCount",
            (360, 60),
            (260, 160),
            [_input("image", "ANY", link=1)],
            [],
            [],
            1,
        ),
        _node(
            3,
            "RMBG",
            (360, 430),
            (260, 300),
            [_input("image", "ANY", link=2)],
            [],
            ["RMBG-2.0", 1, 1024, 0, 0, False, "#000000"],
            1,
        ),
        _node(
            4,
            "LayerMask: MaskBoxDetect",
            (680, 430),
            (280, 180),
            [_input("mask", "ANY", link=3)],
            [],
            ["mask_area"],
            2,
        ),
        _node(
            5,
            "InstagramPresetSize",
            (680, 60),
            (280, 160),
            [],
            [
                _output("width", "INT", 0, [6, 36, 40]),
                _output("height", "INT", 1, [7, 37, 41]),
            ],
            [DEFAULT_PRESET],
            0,
        ),
        _node(
            6,
            "SmartExpectedBox",
            (1020, 260),
            SMART_EXPECTED_BOX_NODE_SIZE,
            [
                _input("orig_w", "INT", link=4),
                _input("orig_h", "INT", link=5),
                _input("target_w", "INT", link=6),
                _input("target_h", "INT", link=7),
                _input("crop_box", "BOX", link=8),
                _input("safety_padding_px", "INT", widget=True),
                _input("composition", "COMBO", widget=True),
            ],
            [
                _output("crop_left", "INT", 0, [9]),
                _output("crop_right", "INT", 1, [10]),
                _output("crop_top", "INT", 2, [11]),
                _output("crop_bottom", "INT", 3, [12]),
                _output("pad_left", "INT", 4, [13]),
                _output("pad_right", "INT", 5, [14]),
                _output("pad_top", "INT", 6, [15]),
                _output("pad_bottom", "INT", 7, [16]),
                _output("BOX_DATA", "DICT", 8, [19]),
            ],
            [DEFAULT_SAFETY_PADDING_PX, DEFAULT_COMPOSITION],
            3,
            properties={
                "composition_grid": {
                    "type": "radio_grid",
                    "positions": list(COMPOSITION_POSITIONS),
                    "default": DEFAULT_COMPOSITION,
                }
            },
        ),
        _node(
            7,
            "SmartExpectedBoxDebugger",
            (1400, 60),
            (300, 190),
            [_input("image", "IMAGE", link=18), _input("BOX_DATA", "DICT", link=19)],
            [_output("image", "IMAGE", 0, [20])],
            [],
            5,
        ),
        _node(
            8,
            "PreviewImage",
            (1740, 60),
            (300, 260),
            [_input("images", "IMAGE", link=20)],
            [],
            [],
            10,
        ),
        _node(
            9,
            "SmartCropExtend",
            (1400, 430),
            (330, 380),
            [
                _input("image", "IMAGE", link=17),
                _input("crop_left", "INT", link=9),
                _input("crop_right", "INT", link=10),
                _input("crop_top", "INT", link=11),
                _input("crop_bottom", "INT", link=12),
                _input("pad_left", "INT", widget=True),
                _input("pad_right", "INT", widget=True),
                _input("pad_top", "INT", widget=True),
                _input("pad_bottom", "INT", widget=True),
            ],
            [_output("image", "IMAGE", 0, [21]), _output("outpaint_mask", "MASK", 1, [])],
            [0, 0, 0, 0],
            4,
        ),
        _node(
            10,
            "ImagePadForOutpaint",
            (1780, 430),
            (300, 220),
            [
                _input("image", "IMAGE", link=21),
                _input("left", "INT", link=13),
                _input("top", "INT", link=15),
                _input("right", "INT", link=14),
                _input("bottom", "INT", link=16),
                _input("feathering", "INT", widget=True),
            ],
            [_output("IMAGE", "IMAGE", 0, [22]), _output("MASK", "MASK", 1, [23, 25])],
            [0, 0, 0, 0, 40],
            5,
        ),
        _node(
            11,
            "DrawMaskOnImage",
            (2140, 430),
            (300, 180),
            [_input("image", "IMAGE", link=22), _input("mask", "MASK", link=23)],
            [_output("images", "IMAGE", 0, [24, 27])],
            ["0, 255, 0", "gpu"],
            6,
        ),
        _node(
            12,
            "ImageScaleToTotalPixels",
            (2500, 430),
            (300, 180),
            [
                _input("image", "IMAGE", link=24),
                _input("upscale_method", "COMBO", widget=True),
                _input("megapixels", "FLOAT", widget=True),
                _input("resolution_steps", "INT", widget=True),
            ],
            [_output("IMAGE", "IMAGE", 0, [28, 29])],
            ["lanczos", DEFAULT_OUTPAINT_MEGAPIXELS, 1],
            7,
        ),
        _node(
            13,
            "MaskToImage",
            (2140, 700),
            (220, 120),
            [_input("mask", "MASK", link=25)],
            [_output("IMAGE", "IMAGE", 0, [26])],
            [],
            7,
        ),
        _node(
            14,
            SQUARE_OUTPAINT_SUBGRAPH_ID,
            (2860, 400),
            (400, 405),
            [
                _input("noise_seed", "INT", widget=True),
                _input("unet_name", "COMBO", widget=True),
                _input("clip_name", "COMBO", widget=True),
                _input("vae_name", "COMBO", widget=True),
                _input("text", "STRING", widget=True),
                _input("image", "IMAGE", link=29),
                _input("megapixels", "FLOAT", widget=True),
            ],
            [_output("IMAGE", "IMAGE", 0, [30, 35])],
            [
                DEFAULT_OUTPAINT_SEED,
                DEFAULT_OUTPAINT_UNET,
                DEFAULT_OUTPAINT_CLIP,
                DEFAULT_OUTPAINT_VAE,
                DEFAULT_OUTPAINT_PROMPT,
                DEFAULT_OUTPAINT_MEGAPIXELS,
            ],
            8,
            properties={
                "proxyWidgets": [
                    ["73", "noise_seed"],
                    ["70", "unet_name"],
                    ["71", "clip_name"],
                    ["72", "vae_name"],
                    ["74", "text"],
                    ["80", "megapixels"],
                ],
                "cnr_id": "comfy-core",
                "ver": "0.8.2",
                "outpaint_block_name": "Square Outpaint",
            },
        ),
        _image_resize_kjv2_node(15, (3320, 500), 35, 36, 37, 39, "nvidia_rtx_vsr", 9),
        _image_resize_kjv2_node(23, (3700, 500), 39, 40, 41, 42, "lanczos", 10),
        _node(17, "PreviewImage", (1780, 760), (300, 260), [_input("images", "IMAGE", link=34)], [], [], 10),
        _node(18, "PreviewImage", (2500, 700), (300, 260), [_input("images", "IMAGE", link=27)], [], [], 10),
        _node(19, "PreviewImage", (2860, 80), (300, 260), [_input("images", "IMAGE", link=28)], [], [], 10),
        _node(20, "PreviewImage", (2500, 1000), (300, 260), [_input("images", "IMAGE", link=26)], [], [], 10),
        _node(21, "PreviewImage", (3320, 80), (300, 260), [_input("images", "IMAGE", link=30)], [], [], 10),
        _node(
            22,
            "PreviewImage",
            (4060, 500),
            (300, 260),
            [_input("images", "IMAGE", link=42)],
            [],
            [],
            11,
            properties={"preview_role": "final_output"},
        ),
    ]

    links = [
        [1, 1, 0, 2, 0, "ANY"],
        [2, 1, 0, 3, 0, "ANY"],
        [3, 3, 1, 4, 0, "ANY"],
        [4, 2, 1, 6, 0, "ANY"],
        [5, 2, 2, 6, 1, "ANY"],
        [6, 5, 0, 6, 2, "INT"],
        [7, 5, 1, 6, 3, "INT"],
        [8, 4, 7, 6, 4, "BOX"],
        [9, 6, 0, 9, 1, "INT"],
        [10, 6, 1, 9, 2, "INT"],
        [11, 6, 2, 9, 3, "INT"],
        [12, 6, 3, 9, 4, "INT"],
        [17, 1, 0, 9, 0, "IMAGE"],
        [18, 1, 0, 7, 0, "IMAGE"],
        [19, 6, 8, 7, 1, "DICT"],
        [20, 7, 0, 8, 0, "IMAGE"],
        [21, 9, 0, 10, 0, "IMAGE"],
        [22, 10, 0, 11, 0, "IMAGE"],
        [23, 10, 1, 11, 1, "MASK"],
        [24, 11, 0, 12, 0, "IMAGE"],
        [25, 10, 1, 13, 0, "MASK"],
        [26, 13, 0, 20, 0, "IMAGE"],
        [27, 11, 0, 18, 0, "IMAGE"],
        [28, 12, 0, 19, 0, "IMAGE"],
        [29, 12, 0, 14, 5, "IMAGE"],
        [30, 14, 0, 21, 0, "IMAGE"],
        [34, 9, 0, 17, 0, "IMAGE"],
        [35, 14, 0, 15, 0, "IMAGE"],
        [36, 5, 0, 15, 2, "INT"],
        [37, 5, 1, 15, 3, "INT"],
        [39, 15, 0, 23, 0, "IMAGE"],
        [40, 5, 0, 23, 2, "INT"],
        [41, 5, 1, 23, 3, "INT"],
        [42, 23, 0, 22, 0, "IMAGE"],
        [13, 6, 4, 10, 1, "INT"],
        [14, 6, 5, 10, 3, "INT"],
        [15, 6, 6, 10, 2, "INT"],
        [16, 6, 7, 10, 4, "INT"],
    ]

    return {
        "last_node_id": 23,
        "last_link_id": 42,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"workflowRendererVersion": "LG"},
        "definitions": {
            "subgraphs": [_reference_conditioning_subgraph(), _square_outpaint_subgraph()],
        },
        "version": 0.4,
    }


def write_workflow() -> None:
    """Write only the generated workflow beside this generator."""
    serialized = json.dumps(build_workflow(), ensure_ascii=False, indent=2) + "\n"
    WORKFLOW_PATH.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    write_workflow()
