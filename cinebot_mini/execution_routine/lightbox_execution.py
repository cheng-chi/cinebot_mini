from cinebot_mini.robot_abstraction.robot import Robot
from cinebot_mini.web_utils.camera_client import *
from cinebot_mini.web_utils.display_client import *
import numpy as np
import time
from collections import OrderedDict
from matplotlib import pyplot as plt
import os


def key_to_str(key):
    return '{:06d}'.format(key)


class LightboxExecution:
    DATA_ATTRS = ["config_trajectory", "duration", "param_dict", "photo_data"]
    MIN_FRAME_TIME = 1.0

    def __init__(self,
                 robot: Robot,
                 config_trajectory,
                 renderer_dir,
                 duration):
        self.robot = robot
        self.config_trajectory = config_trajectory
        self.duration = duration

        self.param_dict = None
        self.photo_data = OrderedDict()
        self.renderer_dir = renderer_dir
        self.screen_imgs = self.load_img_names(self.renderer_dir)

        min_num_imgs = min([len(x) for x in self.screen_imgs.values()])
        self.max_available_frame = min([min_num_imgs, len(config_trajectory)])
        if self.max_available_frame < len(config_trajectory):
            print("Not enough images for the full trajectory")
            print("Setting frame number to " + str(self.max_available_frame))

    def load_img_names(self, renderer_dir):
        screen_imgs = dict()
        screen_ids = filter(lambda x: os.path.isdir(os.path.join(renderer_dir, x)), os.listdir(renderer_dir))
        for screen_id in screen_ids:
            screen_folder = os.path.join(renderer_dir, screen_id)
            imgs = sorted(filter(lambda x: os.path.isfile(os.path.join(screen_folder, x)), os.listdir(screen_folder)))
            screen_imgs[screen_id] = [os.path.join(screen_folder, x) for x in imgs]
        return screen_imgs


    def init(self):
        self.robot.enable_torque()
        self.robot.set_joint_angles(self.config_trajectory[0])

    def auto_exposure(self, iso=200, resolution=(3280, 2464)):
        self.param_dict = auto_exposure(iso)
        self.param_dict["resolution"] = list(resolution)
        img_name = save_photo(self.param_dict)
        img = get_image(img_name)
        plt.imshow(img)
        plt.show()

    def get_key(self, idx):
        return idx

    def preview(self, duration=5.0):
        frame_time = duration / len(self.config_trajectory)
        start_time = time.time()
        last_time = time.time()
        for i in range(len(self.config_trajectory)):
            config = self.config_trajectory[i]
            self.robot.set_joint_angles(config)

            print(i)
            curr_time = time.time()
            time_diff = frame_time - (curr_time - last_time)
            print("frame_time:", curr_time - last_time)
            if time_diff > 0:
                print("Sleep {}".format(time_diff))
                time.sleep(time_diff)
            last_time = time.time()
        end_time = time.time()
        print("Total time: {}".format(end_time - start_time))

    def execute(self):
        if self.param_dict is None:
            raise RuntimeError("Exposure parameters not set")

        frame_time = self.duration / len(self.config_trajectory)
        if frame_time < self.MIN_FRAME_TIME:
            raise RuntimeError("Unarchiveable frame rate.")

        start_time = time.time()
        last_time = time.time()
        for i in range(self.max_available_frame):
            self.set_screen_displays_timestamp(i)
            
            img_name = save_photo(self.param_dict)
            self.photo_data[self.get_key(i)] = img_name

            config = self.config_trajectory[i]
            self.robot.set_joint_angles(config)

            print(i)
            curr_time = time.time()
            time_diff = frame_time - (curr_time - last_time)
            if time_diff > 0:
                print("Sleep {}".format(time_diff))
                time.sleep(time_diff)
            last_time = time.time()
        end_time = time.time()
        print("Total time: {}".format(end_time - start_time))

    def download_all(self, dir_name):
        self.download_photos(dir_name, self.photo_data)

    def download_photos(self, dir_name, photo_data: OrderedDict):
        if not os.path.isdir(dir_name):
            raise RuntimeError('Directory "{}" does not exists.'.format(dir_name))

        unsuccessful_images = OrderedDict()
        for key, img_name in photo_data.items():
            extention = os.path.splitext(img_name)[-1]
            save_name = key_to_str(key) + extention
            save_path = os.path.join(dir_name, save_name)
            result = download_resource(img_name, save_path)
            if result is False:
                unsuccessful_images[key] = img_name
            print(key)
        return unsuccessful_images

    def set_screen_displays_timestamp(self, timestamp):
        configs = get_screen_configs()
        data = []
        for screen_id in configs:
            inputs = dict()
            inputs["id"] = screen_id
            inputs["img_path"] = self.screen_imgs[screen_id][timestamp]
            data.append(inputs)
        print(data)
        set_screen_displays(data)

    def set_screen_displays_rgb(self, rgb):
        configs = get_screen_configs()
        data = []
        for screen_id in configs:
            inputs = dict()
            inputs["id"] = screen_id
            inputs["rgb"] = rgb
            data.append(inputs)
        set_screen_displays(data)