import bpy
from aiohttp import web
import numpy as np
import tempfile
import uuid
import os
import concurrent
import asyncio
from .blender_utils import jsonify_property
from cinebot_mini_render_server.blender_timer_executor import EXECUTOR

TEMP_DIR = tempfile.TemporaryDirectory()
RENDER_PROPERTIES = ["resolution_x", "resolution_y", "resolution_percentage", "pixel_aspect_x", "pixel_aspect_y"]
RENDER_STATUS = False

routes = web.RouteTableDef()


def get_render_status():
    return RENDER_STATUS


def render_helper(args):
    global RENDER_STATUS
    RENDER_STATUS = True
    bpy.ops.render.render(**args)
    RENDER_STATUS = False
    print("render finished", RENDER_STATUS)


def handle_render_still_helper(file_path):
    bpy.context.scene.render.filepath = file_path

    global RENDER_STATUS
    RENDER_STATUS = True
    bpy.ops.render.render(animation=False, write_still=True, use_viewport=False)
    RENDER_STATUS = False
    # print("render finished", RENDER_STATUS)


@routes.put('/api/render/active_camera')
async def handle_active_camera_put(request):
    input_data = await request.json()

    if "name" not in input_data:
        raise web.HTTPBadRequest()

    camera_name = input_data["name"]
    if camera_name not in bpy.data.objects:
        raise web.HTTPBadRequest()

    scene = bpy.context.scene
    obj = bpy.data.objects[camera_name]
    scene.camera = obj

    data = {
        "result": "SUCCESS",
        "url": '/api/render/active_camera',
        "method": "PUT"
    }
    return web.json_response(data=data)


@routes.get('/api/render/still')
async def handle_render_still_get(request):
    temp_folder = TEMP_DIR.name
    file_name = str(uuid.uuid1()) + '.png'
    file_path = os.path.join(temp_folder, file_name)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(EXECUTOR,
     handle_render_still_helper, file_path)

    return web.FileResponse(file_path)


@routes.put('/api/render/still')
async def handle_render_still_put(request):
    input_data = await request.json()

    if "output_file_path" not in input_data:
        raise web.HTTPBadRequest()

    file_path = input_data["output_file_path"]
    if not os.path.isdir(os.path.dirname(file_path)):
        raise web.HTTPBadRequest()
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(EXECUTOR,
     handle_render_still_helper, file_path)

    data = {
        "result": file_path,
        "url": '/api/render/still',
        "method": "PUT"
    }
    return web.json_response(data=data)


def handle_render_animation_helper(input_data):
    file_path = input_data["output_file_path"]
    scene = bpy.context.scene
    scene.render.filepath = file_path
    scene.frame_start = input_data["frame_start"]
    scene.frame_end = input_data["frame_end"]

    global RENDER_STATUS
    RENDER_STATUS = True
    bpy.ops.render.render(animation=True, write_still=True, use_viewport=False)
    RENDER_STATUS = False
    # print("render finished", RENDER_STATUS)


@routes.put('/api/render/animation')
async def handle_render_animation_put(request):
    input_data = await request.json()

    if "output_file_path" not in input_data \
        or "frame_start" not in input_data \
        or "frame_end" not in input_data:
        raise web.HTTPBadRequest()
    file_path = input_data["output_file_path"]
    if not os.path.isdir(os.path.dirname(file_path)):
        raise web.HTTPBadRequest()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(EXECUTOR,
     handle_render_animation_helper, input_data)

    data = {
        "result": file_path,
        "url": '/api/render/still',
        "method": "PUT"
    }
    return web.json_response(data=data)


@routes.get('/api/render/property')
async def handle_render_property_get(request):
    obj = bpy.context.scene.render

    result = dict()

    properties = dict()
    for prop_name in RENDER_PROPERTIES:
        prop = getattr(obj, prop_name)
        properties[prop_name] = jsonify_property(prop)

    result["properties"] = properties

    data = {
        "result": result,
        "url": '/api/render/property',
        "method": "GET"
    }
    return web.json_response(data=data)


@routes.put('/api/render/property')
async def handle_render_property_put(request):
    input_data = await request.json()

    obj = bpy.context.scene.render

    # ensure atomic change
    if "properties" in input_data:
        for key in input_data["properties"].keys():
            if key not in RENDER_PROPERTIES:
                raise web.HTTPBadRequest()

    # set properties
    if "properties" in input_data:
        for key, val in input_data["properties"].items():
            setattr(obj, key, val)

    result = True
    data = {
        "result": "SUCCESS" if result else "FAILED",
        "url": '/api/render/property',
        "method": "PUT"
    }
    return web.json_response(data=data)
