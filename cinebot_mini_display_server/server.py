from cinebot_mini import SERVERS
from aiohttp import web
import aiohttp_cors
import json
from copy import *
import os
from shutil import copy2
import asyncio
from aiohttp_sse import sse_response

screenConfirmed = {}
screenDisplay = {}
nextDisplay = {}

routes = web.RouteTableDef()
routes.static('/ui', 'lightbox-ui', name='ui')
routes.static('/api/static', 'static', name='static')


@routes.get('/')
async def root_handler(request):
    return web.HTTPFound('/ui/index.html')


@routes.get('/api')
async def hello(request):
    return web.Response(text="Hello, world")


@routes.get('/api/screens')
async def screens(request):
    cfg = {}
    with open("screenCfg.json", "r") as cfgFile:
        try:
            cfg = json.load(cfgFile)
        except:
            pass

    for k in cfg:
        cfg[k]["width_pixels"] = float(cfg[k]["wPx"])
        cfg[k]["height_pixels"] = float(cfg[k]["hPx"])

        if ("wCm" in cfg[k]):
            cfg[k]["width_meters"] = float(cfg[k]["wCm"]) / 100
            cfg[k]["height_meters"] = cfg[k]["height_pixels"] / cfg[k]["width_pixels"] * cfg[k]["width_meters"]
            del cfg[k]["wCm"]
        else:
            cfg[k]["width_meters"] = float(cfg[k]["wPx"]) / float(cfg[k]["ppcm"]) / 100
            cfg[k]["height_meters"] = float(cfg[k]["hPx"]) / float(cfg[k]["ppcm"]) / 100

        del cfg[k]["wPx"]
        del cfg[k]["hPx"]
        del cfg[k]["ppcm"]

    return web.json_response(cfg)


@routes.get('/api/confirm/{id}')
async def confirm(request):
    global screenConfirmed
    screenid = request.match_info["id"]
    screenConfirmed[screenid] = True

    print(screenConfirmed)
    return web.Response(text="confirmed, screen {}".format(screenid))


@routes.post('/api/login')
async def login(request):
    global screenConfirmed

    data = await request.text()
    data = json.loads(data)
    screenid = data["screenid"]
    wPx = None if ("wPx" not in data or data["wPx"] == "") else data["wPx"]
    hPx = None if ("hPx" not in data or data["hPx"] == "") else data["hPx"]
    ppcm = None if ("ppcm" not in data or data["ppcm"] == "") else data["ppcm"]
    wCm = None if ("wCm" not in data or data["wCm"] == "") else data["wCm"]
    print("received dimensions: ", (wPx, hPx))

    with open("screenCfg.json", "a+") as file:
        pass

    prevCfg = {}
    with open("screenCfg.json", "r+") as cfgFile:
        try:
            prevCfg = json.load(cfgFile)
        except:
            pass

    resp = {}
    with open("screenCfg.json", "w") as cfgFile:
        config = deepcopy(prevCfg)
        if (wPx is not None and hPx is not None):
            config[str(screenid)] = {
                "wPx": wPx,
                "hPx": hPx
            }
            resp["wPx"] = wPx
            resp["hPX"] = hPx
        else:
            print(config, screenid)
            if (str(screenid) in config):
                wPx = config[screenid]["wPx"]
                hPx = config[screenid]["hPx"]
            else:
                (wPx, hPx) = (1920, 1080)

        if (ppcm is None):
            if (str(screenid) in prevCfg and "ppcm" in prevCfg[str(screenid)]):
                ppcm = prevCfg[str(screenid)]["ppcm"]
            else:
                ppcm = 72

        config[str(screenid)] = {
            "wPx": wPx,
            "hPx": hPx,
            "ppcm": ppcm
        }

        if (wCm is not None):
            config[str(screenid)]["wCm"] = wCm

        json.dump(config, cfgFile)

    resp = {
        "wPx": wPx,
        "hPx": hPx,
        "rgb": [128, 128, 128]
    }

    screenConfirmed[screenid] = False
    screenDisplay[screenid] = {"rgb": resp["rgb"]}

    return web.json_response(resp)


@routes.put('/api/showimgs')
async def showimgs(request):
    global screenDisplay, nextDisplay
    data = await request.text()
    data = json.loads(data)

    resp = {}

    for d in data:
        id = d["id"]
        if (id not in screenDisplay):
            resp = {
                "status": "failed",
                "message": "no screen with id {}".format(id)
            }
            break

        if ("img_url" in d):
            nextDisplay[id] = {
                "img_url": d["img_url"]
            }


        elif ("img_path" in d):
            path = d["img_path"]
            if (not os.path.isfile(path)):
                resp = {
                    "status": "failed",
                    "message": "unable to find file {}".format(path)
                }
                break

            splitted = os.path.split(path)
            prefixHash = hash(splitted[0])
            if (prefixHash < 0):
                prefix = hex(prefixHash).lstrip("-0x") + "_1"
            else:
                prefix = hex(prefixHash).lstrip("0x") + "_0"

            filename = "{}_{}".format(prefix, splitted[1])

            if (not os.path.isfile("./static/{}".format(filename))):
                copy2(path, "./static/{}".format(filename))

            nextDisplay[id] = {
                "img_path": str(resources.url_for(filename=filename))
            }

        elif ("rgb" in d):
            nextDisplay[id] = {
                "rgb": d["rgb"]
            }

    if (len(resp) == 0):
        resp["status"] = "success"

    return web.json_response(resp)

# @routes.get('/changeImg')
# async def changeImg(request):
# 	global imageIdx, nextIdx
# 	nextIdx = (imageIdx + 1) % 2

# 	return web.Response(text="done")

@routes.get('/api/serverloop/{id}')
async def hello(request):
    global screenDisplay, nextDisplay, screenConfirmed

    screenid = request.match_info["id"]

    loop = request.app.loop
    async with sse_response(request) as resp:
        while True:
            await asyncio.sleep(0.01, loop=loop)
            if (screenid not in screenDisplay): continue
            # print("screen ", screenid, screenDisplay[screenid])
            if (screenid not in nextDisplay): continue
            if (screenDisplay[screenid] != nextDisplay[screenid]):
                # print("sending message now, ", screenid)
                screenConfirmed[screenid] = False
                screenDisplay[screenid] = nextDisplay[screenid]
                del nextDisplay[screenid]
                # await resp.send(str(resources.url_for(filename="image_{}.jpg".format(imageIdx))))
                await resp.send(json.dumps(screenDisplay[screenid]))


app = web.Application()

app.add_routes(routes)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})

resources = app.router.named_resources().get("static")
print(type(resources))

for route in list(app.router.routes()):
    cors.add(route)
    print(route)

server_config = SERVERS["display"]
web.run_app(app, host=server_config["host"], port=server_config["port"])
