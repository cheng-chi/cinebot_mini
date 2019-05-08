from cinebot_mini import SERVERS
import requests
import json


def base_url():
    blender_dict = SERVERS["display"]
    url = "http://{}:{}".format(
        blender_dict["host"], blender_dict["port"])
    return url


def get_screen_configs():
    url = base_url() + '/api/screens'
    r = requests.get(url)
    r_data = r.json()
    return r_data


def set_screen_displays(data):
    json_string = json.dumps(data)
    url = base_url() + '/api/showimgs'
    r = requests.put(url, data=json_string)
    return r

