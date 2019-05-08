import bpy
from aiohttp import web
import asyncio
import threading
import requests
import concurrent
import atexit
import logging
import sys
from .bpy_camera_matrix import get_calibration_matrix_K_from_blender, get_3x4_RT_matrix_from_blender, get_3x4_P_matrix_from_blender, project_by_object_utils
import numpy as np
from mathutils import Matrix, Vector
import os
import time

from cinebot_mini_render_server.blender_timer_executor import EXECUTOR
import cinebot_mini_render_server.object_routes as object_routes
import cinebot_mini_render_server.animation_routes as animation_routes
import cinebot_mini_render_server.render_routes as render_routes

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


SERVER_STATE = {
    "running": False,
    "host": '127.0.0.1',
    "port": 8089,
    "thread": None
}
STOP_API_URL = '/api/stop'


routes = web.RouteTableDef()


@routes.get('/api/ping')
async def handle_ping_get(request):
    data = {
        "url": '/api/ping'
    }
    return web.json_response(data=data)


@routes.get('/api/executor_print')
async def handle_executor_print_get(request):
    args = {
        "input_str": '/api/executor_print'
    }

    def print_test(input_str):
        print("print_test started")
        time.sleep(5.0)
        print("print_test finished")
        return "print finished!"
    
    print("print started")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(EXECUTOR, print_test, args)
    print("print started")
    # await asyncio.sleep(5, loop=loop)
    # result = "print finsihed"
    print(result)

    data = {
        "url": '/api/executor_print'
    }
    return web.json_response(data=data)


@routes.get('/api/set_frame/{number}')
async def handle_set_frame(request):
    number = int(request.match_info.get('number', '0'))
    bpy.context.scene.frame_set(number)

    text = "succes!"
    return web.Response(text=text)


@routes.get(STOP_API_URL)
async def stop_handle(request):
    loop = asyncio.get_event_loop()
    loop.call_soon(loop.stop)
    text = "Stop called"
    return web.Response(text=text)


def runner():
    print(logging.getLogger('aiohttp.internal'))
    app = web.Application()
    app.add_routes(routes)
    app.add_routes(object_routes.routes)
    app.add_routes(animation_routes.routes)
    app.add_routes(render_routes.routes)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = loop.create_server(app.make_handler(),
                                host=SERVER_STATE['host'],
                                port=SERVER_STATE['port'])
    srv = loop.run_until_complete(server)
    print("server starting")
    loop.run_forever()

    # clean up server resources, free sockets
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.shutdown())
    loop.run_until_complete(app.cleanup())
    loop.close()
    print('loop closed!')


def start_server():
    print("start server!")
    if SERVER_STATE['thread'] is None or not SERVER_STATE['thread'].is_alive():
        SERVER_STATE['thread'] = threading.Thread(target=runner, daemon=True)
        SERVER_STATE['thread'].start()


def close_server():
    print("close_server executed!")
    if SERVER_STATE['thread'] is not None and SERVER_STATE['thread'].is_alive():
        print("event_thread is running")
        print(STOP_API_URL)
        url = "http://{}:{}{}".format(SERVER_STATE['host'], SERVER_STATE['port'], STOP_API_URL)
        print(url)
        r = requests.get(url)
        print(r)
        SERVER_STATE['thread'].join()
    
    SERVER_STATE['thread'] = None


class RestartAiohttpServer(bpy.types.Operator):
    bl_idname = "aiohttp_server.restart"
    bl_label = "Restarts the aiohttp server"
    
    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        # create new object reay run
        print('started operator')
        close_server()
        start_server()
        return {'FINISHED'}


class HelloWorldPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Hello World Panel"
    bl_idname = "OBJECT_PT_hello"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Rendering!" if render_routes.get_render_status() else "Not rendering.")
        print("draw panel")

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")

        row = layout.row()
        props = row.operator(RestartAiohttpServer.bl_idname, text='Restart Server')


def register():
    print("register!")
    atexit.register(close_server)
    start_server()
    bpy.utils.register_class(RestartAiohttpServer)
    bpy.utils.register_class(HelloWorldPanel)

def unregister():
    print("unregister!")
    close_server()
    bpy.utils.unregister_class(RestartAiohttpServer)
    bpy.utils.unregister_class(HelloWorldPanel)
    atexit.unregister(close_server)
