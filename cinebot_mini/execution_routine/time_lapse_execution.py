from cinebot_mini.robot_abstraction.robot import Robot
from cinebot_mini.web_utils.camera_client import *
import numpy as np
import time
from collections import OrderedDict
from matplotlib import pyplot as plt


def key_to_str(key):
    return '{:06d}'.format(key)


class TimeLapseExecution:
    DATA_ATTRS = ["config_trajectory", "duration", "param_dict", "photo_data"]
    MIN_FRAME_TIME = 1.0

    def __init__(self,
                 robot: Robot,
                 config_trajectory,
                 duration):
        self.robot = robot
        self.config_trajectory = config_trajectory
        self.duration = duration

        self.param_dict = None
        self.photo_data = OrderedDict()

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
        # if frame_time < self.MIN_FRAME_TIME:
        #     raise RuntimeError("Unarchiveable frame rate.")

        start_time = time.time()
        last_time = time.time()
        for i in range(len(self.config_trajectory)):
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
