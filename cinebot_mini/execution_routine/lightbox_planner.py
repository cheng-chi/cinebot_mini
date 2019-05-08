from cinebot_mini import TRANSFORMS
from cinebot_mini.robot_abstraction.cinebot import get_cinebot_chain
from cinebot_mini.geometry_utils.transformation_tree import TransformationTree
from cinebot_mini.web_utils.blender_client import *
import numpy as np
import os


class LightBoxPlanner:
    def __init__(self):
        self.screens = dict()
        self.tf_tree = TransformationTree()

        # build tree
        self.real_root_name = "real_root"
        self.virtual_root_name = "ROOT"
        self.tf_tree.add_node(self.virtual_root_name, self.real_root_name, np.eye(4))

        self.robot_chain = get_cinebot_chain()
        self.tf_tree.add_chain(self.real_root_name, self.robot_chain)
        self.camera_name = TRANSFORMS["robot_camera_name"]
        camera_mat = TRANSFORMS["robot_camera_to_robot"]
        self.tf_tree.add_node("joint5", self.camera_name, camera_mat)

        self.subject_name = "subject"

        self.animation_length = 0

    def add_screen(self, name, pixel_dims, real_dims, transform):
        if self.subject_name not in self.tf_tree.transforms:
            raise RuntimeError("Subject not set.")

        subject_pose = self.tf_tree.get_transform(self.subject_name, self.real_root_name)
        subject_pos = subject_pose[:3, 3]
        screen_y = transform @ np.array([0, 1, 0, 1]).T
        y_to_screen = screen_y[:-1] - transform[:3, 3]
        subject_to_screen = subject_pos - transform[:3, 3]
        dist_subject_to_screen = np.dot(subject_to_screen, y_to_screen)

        camera_pos = (transform @ np.array([0, dist_subject_to_screen, 0, 1]).T)[:-1]
        camera_z = camera_pos - transform[:3, 3]
        camera_z /= np.linalg.norm(camera_z)
        camera_y = transform[:3, 2]
        camera_x = np.cross(camera_y, camera_z)

        camera_mat = np.eye(4)
        camera_mat[:3, 0] = camera_x
        camera_mat[:3, 1] = camera_y
        camera_mat[:3, 2] = camera_z
        camera_mat[:3, 3] = camera_pos

        info_dict = {
            "pixel_dims": pixel_dims,
            "real_dims": real_dims,
            "transform": transform,
            "camera_transform": camera_mat,
            "focal_length": dist_subject_to_screen
        }
        self.screens[name] = info_dict
        self.tf_tree.add_node(self.real_root_name, name, transform)
        self.tf_tree.add_node(self.real_root_name, name + "_camera", camera_mat)

    def add_subject(self, transform=None, position=None):
        if transform is None and position is None:
            return

        if transform is None:
            transform = np.eye(4)
            transform[:3, 3] = position
        self.tf_tree.add_node(self.real_root_name, self.subject_name, transform)

    def set_subject_virtual_transform(self, transform):
        subject_to_real_root = self.tf_tree.get_transform(self.subject_name, self.real_root_name)
        real_to_virtual_root = transform @ np.linalg.inv(subject_to_real_root)
        self.tf_tree.transforms[self.real_root_name] = real_to_virtual_root

    def set_all_animation(self, subject_trajectory, robot_config_history):
        if type(subject_trajectory) != list and len(subject_trajectory.shape) == 2:
            subject_trajectory = [subject_trajectory] * len(robot_config_history)

        frame_transforms = dict()
        for frame_name in self.tf_tree.transforms.keys():
            frame_transforms[frame_name] = []
            if not test_object_exist(frame_name):
                if frame_name.endswith("_camera"):
                    create_object(frame_name, type="CAMERA")
                else:
                    create_object(frame_name, type="EMPTY")
                    set_property(frame_name, "empty_display_size", 0.05)

        max_len = min(len(subject_trajectory), len(robot_config_history))
        self.animation_length = max_len
        for t in range(max_len):
            self.set_subject_virtual_transform(subject_trajectory[t])
            self.tf_tree.set_chain_state(self.robot_chain.name, robot_config_history[t])
            for frame_name in self.tf_tree.transforms.keys():
                frame_transforms[frame_name].append(
                    self.tf_tree.get_transform(frame_name))

        for frame_name in self.tf_tree.transforms.keys():
            set_animation_matrix(frame_name, frame_transforms[frame_name])

        for screen_name in self.screens:
            self.set_camera(screen_name)

    def render_screen(self, screen_name, folder):
        if self.animation_length < 1:
            raise RuntimeError("Animation Not Set")

        self.set_camera(screen_name)

        output_path = os.path.join(folder, "#####")
        render_animation(output_path, 0, self.animation_length)

    def render_all(self, folder):
        if not os.path.isdir(folder):
            raise RuntimeError("folder {} does not exist".format(folder))

        for screen_name in self.screens:
            screen_folder = os.path.join(folder, screen_name)
            if not os.path.isdir(screen_folder):
                os.mkdir(screen_folder)
            print("Rendering {}".format(screen_name))
            self.render_screen(screen_name, screen_folder)

    def set_camera(self, screen_name):
        obj_name = screen_name + "_camera"

        if not test_object_exist(obj_name):
            create_object(obj_name, type="CAMERA")
        set_active_camera(obj_name)

        info_dict = self.screens[screen_name]
        set_camera_properties(obj_name, info_dict["focal_length"], info_dict["real_dims"])
        set_render_resolution(info_dict["pixel_dims"])
        # set_transform_matrix(self.screen_camera_name, info_dict["camera_transform"])
