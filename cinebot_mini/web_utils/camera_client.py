from cinebot_mini import SERVERS
import requests
import numpy as np
import json
import os
import skimage
import urllib
import threading
import copy
import subprocess


def base_url():
    blender_dict = SERVERS["camera"]
    url = "http://{}:{}".format(
        blender_dict["host"], blender_dict["port"])
    return url


def auto_exposure(iso=200):
    url = base_url() + "/api/autoexposure" + "?iso={}".format(int(iso))
    r = requests.get(url)
    if r.status_code != 200:
        return None
    r_data = r.json()
    params_dict = r_data["params"]
    return params_dict


def save_photo(params_dict):
    url = base_url() + "/api/savephoto"
    r = requests.put(url, json=params_dict)
    if r.status_code != 200:
        print(r.status_code)
        return None
    r_data = r.json()
    shot_params = r_data["params"]
    image_name = r_data["resource"]
    return image_name


def save_video(params_dict):
    url = base_url() + "/api/savevideo"
    r = requests.put(url, json=params_dict)
    if r.status_code != 200:
        print(r.status_code)
        return None
    r_data = r.json()
    shot_params = r_data["params"]
    video_name = r_data["resource"]
    return video_name


def avaliable_resources():
    url = base_url() + "/api/resource"
    r = requests.get(url)
    r_data = r.json()
    resource_dict = r_data["resources"]
    return resource_dict


def clear_resources():
    url = base_url() + "/api/resource"
    r = requests.delete(url)
    return r.status_code == 200


def download_resource(file_name, file_path):
    url = base_url() + "/resource/" + file_name
    try:
        urllib.request.urlretrieve(url, file_path)
        return True
    except urllib.error.HTTPError as e:
        return False


def get_image(file_name):
    url = base_url() + "/resource/" + file_name
    try:
        img = skimage.io.imread(url)
        return img
    except urllib.error.HTTPError as e:
        return None


def h264_to_mp4(file_path):
    assert(file_path.endswith(".h264"))
    output_path = file_path[:-5] + ".mp4"
    args = ['ffmpeg', '-i', '{}'.format(file_path), '-c:v', 'copy',
            '-f', 'mp4', '{}'.format(output_path)]

    subprocess.call(args)
    return output_path


class VideoRecorder(threading.Thread):
    def __init__(self, fps=90, duration=10.0, iso=200):
        super().__init__()
        self.fps = fps
        self.duration = duration
        self.iso = iso
        self.param_dict = None
        self.done = threading.Event()
        self.video_name = None

    def auto_exposure(self):
        self.param_dict = auto_exposure(self.iso)

    def capture(self):
        if self.param_dict is None:
            raise RuntimeError("Exposure parameters not set")
        self.start()

    def run(self):
        curr_param_dict = copy.deepcopy(self.param_dict)
        curr_param_dict['fps'] = self.fps
        curr_param_dict['duration'] = self.duration
        self.video_name = save_video(curr_param_dict)
        self.done.set()

    def download_video(self, dir_name, blocking=False):
        if blocking:
            self.done.wait(timeout=self.duration + 4.0)
            if not self.done.is_set():
                raise TimeoutError("Blocking timeout.")
        file_path = os.path.join(dir_name, self.video_name)
        download_resource(self.video_name, file_path)
        return file_path


def test():
    t = VideoRecorder(fps=110, duration=2.0, iso=300)
    t.auto_exposure()
    t.capture()
    dir_name = "/Users/chengchi/blender_out"
    file_path = t.download_video(dir_name, blocking=True)
    mp4_path = h264_to_mp4(file_path)
    d = skvideo.io.ffprobe(mp4_path)
    fps = d['video']['@avg_frame_rate']
    duration = float(d['video']['@duration'])

