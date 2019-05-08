from cinebot_mini import SERVERS
import requests
import numpy as np
import json


def base_url():
    blender_dict = SERVERS["blender"]
    url = "http://{}:{}".format(
        blender_dict["host"], blender_dict["port"])
    return url


def handshake():
    url = base_url() + "/api/ping"
    for i in range(5):
        try:
            r = requests.get(url, timeout=1.0)
            r_data = r.json()
            assert(r_data["url"] == "/api/ping")
            return True
        except Exception as e:
            continue
    return False


def create_object(name, type="CAMERA"):
    url = base_url() + "/api/create"
    data = {
        "type": type,
        "name": name
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()

    obj_dict = r_data['result']
    if "name" in obj_dict:
        return obj_dict["name"]
    else:
        print("Creating {} failed!", obj_name)


def create_objects(type="CAMERA", num=4, base_name="screen_camera_"):
    url = base_url() + "/api/create"
    obj_names = []
    for i in range(num):
        obj_name = base_name + str(i)
        data = {
            "type": type,
            "name": obj_name
        }
        r = requests.put(url, data=json.dumps(data))
        r_data = r.json()

        obj_dict = r_data['result']
        if "name" in obj_dict:
            obj_names.append(obj_dict["name"])
        else:
            print("Creating {} failed!", obj_name)

    return obj_names


def set_transform_euler(obj_name, loc, rot, degree=True):
    url = base_url() + "/api/object/" + obj_name + "/property"
    rot_data = list(rot)
    if degree:
        rot_data = (np.array(rot) / 180.0 * np.pi).tolist()
    data = {
        "properties": {
            "location": list(loc),
            "rotation_euler": list(rot_data)
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def set_transform_matrix(obj_name, matrix):
    url = base_url() + "/api/object/" + obj_name + "/property"
    data = {
        "properties": {
            "matrix_world": matrix.tolist()
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def set_transform_matrix(obj_name, matrix):
    url = base_url() + "/api/object/" + obj_name + "/property"
    data = {
        "properties": {
            "matrix_world": matrix.tolist()
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def set_property(obj_name, key, val, prop_type="properties"):
    url = base_url() + "/api/object/" + obj_name + "/property"
    data = {
        prop_type: {
            key: val
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def get_property(obj_name):
    url = base_url() + "/api/object/" + obj_name + "/property"
    r = requests.get(url)
    r_data = r.json()
    return r_data["result"]


def test_object_exist(obj_name):
    url = base_url() + "/api/object/" + obj_name + "/property"
    data = dict()
    r = requests.get(url, data=json.dumps(data))
    return r.status_code != 404


def set_animation_euler(obj_name, locs, rots, degree=True):
    url = base_url() + "/api/object/" + obj_name + "/animation"
    rot_data = rots
    if degree:
        rot_data = rots / 180.0 * np.pi
    transforms = []
    for t in range(len(locs)):
        tf_data = dict()
        tf_data["frame_number"] = t
        tf_data["location"] = locs[t].tolist()
        tf_data["rotation_euler"] = rot_data[t].tolist()
        transforms.append(tf_data)
    data = {
        "transforms": transforms
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def set_animation_matrix(obj_name, matrices):
    url = base_url() + "/api/object/" + obj_name + "/animation"
    transforms = []
    for t in range(len(matrices)):
        tf_data = dict()
        tf_data["frame_number"] = t
        tf_data["matrix_world"] = matrices[t].tolist()
        transforms.append(tf_data)
    data = {
        "transforms": transforms
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def get_animation_dict(obj_name):
    url = base_url() + "/api/object/" + obj_name + "/animation"
    r = requests.get(url)
    r_data = r.json()
    animation = r_data["result"]
    result = dict()
    for frame in animation:
        t = frame["frame_number"]
        arr = np.array(frame["matrix_world"])
        result[t] = arr
    return result


def get_animation(obj_name):
    url = base_url() + "/api/object/" + obj_name + "/animation"
    r = requests.get(url)
    r_data = r.json()
    animation = r_data["result"]
    result = []
    for frame in animation:
        arr = np.array(frame["matrix_world"])
        result.append(arr)
    return result


def delete_animation(obj_name):
    url = base_url() + "/api/object/" + obj_name + "/animation"
    r = requests.delete(url)
    r_data = r.json()
    return r_data["result"]


def delete_object(obj_name):
    url = base_url() + "/api/object/" + obj_name
    r = requests.delete(url)
    r_data = r.json()
    return r_data["result"]


def render_animation(file_name, frame_start, frame_end):
    url = base_url() + "/api/render/animation"
    data = {
        "output_file_path": file_name,
        "frame_start": frame_start,
        "frame_end": frame_end
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"]


def set_render_resolution(pixel_dim):
    url = base_url() + "/api/render/property"
    x, y = pixel_dim
    data = {
        "properties": {
            "resolution_x": x,
            "resolution_y": y
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"] == "SUCCESS"


def set_camera_properties(cam_name, focal_length_m, sensor_dims_m):
    url = base_url() + "/api/object/" + cam_name + "/property"
    lens = focal_length_m * 1000
    w, h = np.array(sensor_dims_m) * 1000
    data = {
        "data_properties": {
            "lens": lens,
            "sensor_width": w,
            "sensor_height": h
        }
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"] == "SUCCESS"


def set_active_camera(cam_name):
    url = base_url() + "/api/render/active_camera"
    data = {
        "name": cam_name
    }
    r = requests.put(url, data=json.dumps(data))
    r_data = r.json()
    return r_data["result"] == "SUCCESS"
