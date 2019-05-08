import bpy
from aiohttp import web
import numpy as np
from .virtual_property_helper import *
from .blender_utils import jsonify_property, set_property
import time
import asyncio
from cinebot_mini_render_server.blender_timer_executor import EXECUTOR

COMMON_PROPERTIES = ["location", "rotation_euler", "matrix_world"]
OBJ_PROPERTIES = {
    "EMPTY": ["empty_display_type", "empty_display_size"] + COMMON_PROPERTIES,
    "CAMERA": [] + COMMON_PROPERTIES
}
OBJ_DATA_PROPERTIES = {
    "CAMERA": ["sensor_width", "sensor_height", "lens"]
}
OBJ_VIRTUAL_PROPERTIES = {
    "CAMERA": {
        "focal_length_pixel": camera_focal_length_pixel_helper,
        "intrinsic_matrix": camera_intrinsic_matrix_helper
    }
}

routes = web.RouteTableDef()


def get_server_collection():
    desired_name = "ServerCreated"
    if not desired_name in bpy.data.collections:
        collection = bpy.data.collections.new(desired_name)
        bpy.context.scene.collection.children.link(collection)
    return desired_name


def handle_create_put_helper(input_data):
    collection_name = get_server_collection()
    
    r_data = dict()
    if "type" not in input_data \
       or "name" not in input_data:
        return r_data
    
    obj_type = input_data["type"]
    obj_name = input_data["name"]
    if obj_type == "EMPTY":
        args = {
            "type": "ARROWS",
            "radius": 1.0
        }
        if "arguments" in input_data:
            args.update(input_data["arguments"])
        print("before empty_add")
        obj = bpy.data.objects.new(obj_name, None)
        obj.empty_display_type = "ARROWS"
        bpy.data.collections[collection_name].objects.link(obj)

        r_data["name"] = obj.name
        r_data["collection"] = collection_name
    elif obj_type == "CAMERA":
        args = dict()
        if "arguments" in input_data:
            args.update(input_data["arguments"])

        cam_obj = bpy.data.cameras.new(obj_name)
        obj = bpy.data.objects.new(obj_name, cam_obj)
        bpy.data.collections[collection_name].objects.link(obj)

        r_data["name"] = obj.name
        r_data["collection"] = collection_name
    else:
        return r_data

    return r_data


@routes.put('/api/create')
async def handle_create_put(request):
    input_data = await request.json()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR,
     handle_create_put_helper, input_data)
   
    data = {
        "result": result,
        "url": '/api/create',
        "method": "PUT"
    }
    return web.json_response(data=data)


@routes.get('/api/object/{obj_name}/property')
async def handle_object_property_get(request):
    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPNotFound()
    
    obj = bpy.data.objects[obj_name]
    obj_type = obj.type

    result = dict()
    
    if obj_type in OBJ_PROPERTIES:
        properties = dict()
        for prop_name in OBJ_PROPERTIES[obj_type]:
            properties[prop_name] = jsonify_property(getattr(obj, prop_name))
        result["properties"] = properties
    
    if obj_type in OBJ_DATA_PROPERTIES:
        data_properties = dict()
        for prop_name in OBJ_DATA_PROPERTIES[obj_type]:
            data_properties[prop_name] = jsonify_property(getattr(obj.data, prop_name))
        result["data_properties"] = data_properties
    
    if obj_type in OBJ_VIRTUAL_PROPERTIES:
        virtual_properties = dict()
        for prop_name, func in OBJ_VIRTUAL_PROPERTIES[obj_type].items():
            prop = func(obj)
            virtual_properties[prop_name] = jsonify_property(prop)
        result["virtual_properties"] = virtual_properties
    
    data = {
        "result": result,
        "url": '/api/object/{}/property'.format(obj_name),
        "method": "GET"
    }
    return web.json_response(data=data)


def handle_object_property_put_helper(input_data, obj_name):
    obj = bpy.data.objects[obj_name]
    obj_type = obj.type

    # ensure atomic change
    if "properties" in input_data:
        for key in input_data["properties"].keys():
            if key not in OBJ_PROPERTIES[obj_type]:
                return False
    
    if "data_properties" in input_data:
        for key in input_data["data_properties"].keys():
            if key not in OBJ_DATA_PROPERTIES[obj_type]:
                return False

    if "virtual_properties" in input_data:
        for key in input_data["virtual_properties"].keys():
            if key not in OBJ_VIRTUAL_PROPERTIES[obj_type]:
                return False

    # set properties
    if "properties" in input_data:
        for key, val in input_data["properties"].items():
            set_property(obj, key, val)
    
    if "data_properties" in input_data:
        for key, val in input_data["data_properties"].items():
            set_property(obj.data, key, val)

    if "virtual_properties" in input_data:
        for key, value in input_data["virtual_properties"].items():
            OBJ_VIRTUAL_PROPERTIES[obj_type][key](obj, value)
    return True


@routes.put('/api/object/{obj_name}/property')
async def handle_object_property_put(request):
    input_data = await request.json()

    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPBadRequest()
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR,
     handle_object_property_put_helper, input_data, obj_name)

    data = {
        "result": "SUCCESS" if result else "FAILED",
        "url": '/api/object/{}/property'.format(obj_name),
        "method": "PUT"
    }
    return web.json_response(data=data)


def handle_object_delete_helper(obj_name):
    if obj_name not in bpy.data.objects:
        return False
    
    obj = bpy.data.objects[obj_name]
    bpy.data.objects.remove(obj)
    return True


@routes.delete('/api/object/{obj_name}')
async def handle_object_delete(request):
    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPBadRequest()
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR,
     handle_object_delete_helper, obj_name)
    
    data = {
        "result": "SUCCESS" if result else "FAILED",
        "url": '/api/object/{}'.format(obj_name),
        "method": "DELETE"
    }
    return web.json_response(data=data)
