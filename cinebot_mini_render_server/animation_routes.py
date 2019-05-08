import bpy
from aiohttp import web
import numpy as np
from mathutils import Matrix, Vector
import asyncio
from cinebot_mini_render_server.blender_timer_executor import EXECUTOR

routes = web.RouteTableDef()


def delete_animation_helper(obj):
    if not obj.animation_data:
        return False
    if not obj.animation_data.action:
        return False
    if not obj.animation_data.action.fcurves:
        return False
    action = obj.animation_data.action
    remove_types = ["location", "scale", "rotation"]
    fcurves = [fc for fc in action.fcurves
                for type in remove_types
                if fc.data_path.startswith(type)]
    while fcurves:
        fc = fcurves.pop()
        action.fcurves.remove(fc)
    return True


def handle_object_animation_get_helper(obj_name):
    scene = bpy.context.scene
    obj = bpy.data.objects[obj_name]

    fc = obj.animation_data.action.fcurves[0]
    start, end = fc.range()
    transforms = []
    for t in range(int(start), int(end)):
        scene.frame_set(t)
        matrix_world = np.array(obj.matrix_world)
        tf_data = {
            "frame_number": t,
            "matrix_world": matrix_world.tolist()
        }
        transforms.append(tf_data)

    return transforms


@routes.get('/api/object/{obj_name}/animation')
async def handle_object_animation_get(request):
    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPBadRequest()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR,
                                        handle_object_animation_get_helper, obj_name)

    data = {
        "result": result,
        "url": '/api/object/{}/animation'.format(obj_name),
        "method": "GET"
    }
    return web.json_response(data)


def handle_object_animation_put_helper(input_data, obj_name):
    scene = bpy.context.scene
    obj = bpy.data.objects[obj_name]

    print("before delete")
    delete_animation_helper(obj)
    print("after delete")

    if not obj.animation_data:
        obj.animation_data_create()

    if not obj.animation_data.action:
        obj.animation_data.action = bpy.data.actions.new(name=obj_name + "_action")

    f_curves_loc = [obj.animation_data.action.fcurves.new(data_path="location", index=i) for i in range(3)]
    f_curves_rot = [obj.animation_data.action.fcurves.new(data_path="rotation_euler", index=i) for i in range(3)]
    [x.keyframe_points.add(len(input_data["transforms"])) for x in f_curves_loc]
    [x.keyframe_points.add(len(input_data["transforms"])) for x in f_curves_rot]
    for i, frame in enumerate(input_data["transforms"]):
        frame_number = frame["frame_number"]
        location = None
        rotation_euler = None
        
        if "matrix_world" in frame:
            matrix_world = frame["matrix_world"]
            m = Matrix(matrix_world)
            location = m.to_translation()
            rotation_euler = m.to_euler()
        elif "location" in frame and "rotation_euler" in frame:
            location = frame["location"]
            rotation_euler = frame["rotation_euler"]
        else:
            return False

        for j in range(3):
            f_curves_loc[j].keyframe_points[i].co = [float(frame_number), location[j]]
            f_curves_rot[j].keyframe_points[i].co = [float(frame_number), rotation_euler[j]]

    return True


@routes.put('/api/object/{obj_name}/animation')
async def handle_object_animation_put(request):
    input_data = await request.json()

    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPBadRequest()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR, 
    handle_object_animation_put_helper, input_data, obj_name)

    data = {
        "result": "SUCCESS" if result else "FAILED",
        "url": '/api/object/{}/animation'.format(obj_name),
        "method": "PUT"
    }
    return web.json_response(data=data)


def handle_object_animation_delete_helper(obj_name):
    scene = bpy.context.scene
    obj = bpy.data.objects[obj_name]
    result = delete_animation_helper(obj)
    return result


@routes.delete('/api/object/{obj_name}/animation')
async def handle_object_animation_delete(request):
    obj_name = request.match_info.get('obj_name', "None")
    if obj_name not in bpy.data.objects:
        raise web.HTTPBadRequest()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR,
     handle_object_animation_delete_helper, obj_name)

    data = {
        "result": "SUCCESS" if result else "FAILED",
        "url": '/api/object/{}/animation'.format(obj_name),
        "method": "DELETE"
    }
    return web.json_response(data=data)
