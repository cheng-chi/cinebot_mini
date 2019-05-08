from cinebot_mini import TRANSFORMS
from cinebot_mini.robot_abstraction.robot import Robot
from cinebot_mini.geometry_utils import (
    ArcNDInterpolator,
    Gaze3DInterpolator,
    TransformationTree)
from cinebot_mini.web_utils.blender_client import *
import numpy as np
import pickle


def save_planner(planner, fname):
    attr_dict = dict()
    for attr in planner.DATA_ATTRS:
        attr_dict[attr] = getattr(planner, attr)
    pickle.dump(attr_dict, open(fname, 'wb'))


def load_planner(planner, fname):
    attr_dict = pickle.load(open(fname, 'rb'))
    for key, val in attr_dict.items():
        setattr(planner, key, val)


class DirectPlanner:
    DATA_ATTRS = ["configuration_history"]

    def __init__(self, robot: Robot):
        self.robot = robot
        self.configuration_history = []
        self.robot.disable_torque()

    def record(self):
        self.configuration_history.append(
            self.robot.get_joint_angles())

    def plan(self, duration=5.0, fps=30.0):
        input_config = np.array(self.configuration_history)
        interpolator = ArcNDInterpolator(input_config, num_cache=20, input_smoothing=0.0)
        arc_lengths = np.linspace(0, interpolator.length(), int(fps*duration))
        output_config = interpolator.generate(arc_lengths)
        return output_config

    def clear(self):
        self.configuration_history = []

    def blender_visualize(self):
        pass


class GazePlanner:
    DATA_ATTRS = ["configuration_history", "camera_points", "gaze_points", "plan_cache"]

    def __init__(self, robot: Robot, tf_tree: TransformationTree, duration=5.0, fps=30.0):
        self.robot = robot
        self.tf_tree = tf_tree
        self.chain_name = robot.get_chain().name
        self.camera_name = TRANSFORMS["robot_camera_name"]
        self.end_effector_name = self._robot_chain().links[-1].name
        self.duration = duration
        self.fps = fps

        self.configuration_history = []
        self.camera_points = []
        self.gaze_points = []
        self.plan_cache = []
        self.cache_dirty = True

        self.robot.disable_torque()

    def _robot_chain(self):
        return self.tf_tree.chains[self.chain_name]

    def _current_camera_pose(self, joint_angles=None):
        if joint_angles is None:
            joint_angles = self.robot.get_joint_angles()
        self.tf_tree.set_chain_state(self.chain_name, joint_angles)
        camera_pose = self.tf_tree.get_transform(self.camera_name)
        return camera_pose

    def record_camera_pose(self):
        joint_angles = self.robot.get_joint_angles()
        print(joint_angles)
        self.configuration_history.append(joint_angles)
        camera_pose = self._current_camera_pose(joint_angles)
        camera_point = camera_pose[:3, 3]
        self.camera_points.append(camera_point)
        self.cache_dirty = True

    def add_gaze_point(self, gaze_point=None):
        if gaze_point is None:
            camera_pose = self._current_camera_pose()
            camera_point = camera_pose[:3, 3]
            gaze_point = camera_point
        self.gaze_points.append(gaze_point)
        self.cache_dirty = True

    def _interpolate_camera(self):
        gaze_points_input = self.gaze_points[0]
        if len(self.gaze_points) > 3:
            gaze_points_input = np.array(self.gaze_points)
        interpolator = Gaze3DInterpolator(np.array(self.camera_points), gaze_points_input)
        arc_lengths = np.linspace(
            0, interpolator.length(), int(self.fps * self.duration))
        output_camera_poses = interpolator.generate(arc_lengths)
        return output_camera_poses

    def plan(self):
        if self.cache_dirty is False:
            return self.plan_cache

        # init to configuration history
        output_camera_poses = self._interpolate_camera()
        self.tf_tree.set_chain_state(self.chain_name, self.configuration_history[0])
        output_configs = []
        for i in range(len(output_camera_poses)):
            camera_pose = output_camera_poses[i]
            # self.tf_tree.set_chain_state(self.chain_name, [0,0,0,0,0,0])
            try:
                self.tf_tree.set_transform(self.camera_name, camera_pose)
                config = self.tf_tree.chain_states[self.chain_name]
                output_configs.append(config)
            except RuntimeError as e:
                config = self.tf_tree.chain_states[self.chain_name]
                print("IK Failed at i={}, previous configuration:". format(i), config)
                print("Camera pose:", camera_pose)

        self.plan_cache = output_configs
        self.cache_dirty = False
        return output_configs

    def blender_animate(self, axis_size=0.05):
        frame_transforms = dict()
        for frame_name in self.tf_tree.transforms.keys():
            frame_transforms[frame_name] = []
            if not test_object_exist(frame_name):
                create_object(frame_name, type="EMPTY")
                set_property(frame_name, "empty_display_size", axis_size)

        output_configs = self.plan()
        for i in range(len(output_configs)):
            self.tf_tree.set_chain_state(self.chain_name, output_configs[i])
            for frame_name in self.tf_tree.transforms.keys():
                frame_transforms[frame_name].append(
                    self.tf_tree.get_transform(frame_name))

        for frame_name in self.tf_tree.transforms.keys():
            set_animation_matrix(frame_name, frame_transforms[frame_name])

    def blender_animate_input(self, axis_size=0.05):
        point_name = "DEBUG_gaze_point"
        camera_name = "DEBUG_camera_point"
        for frame_name in [point_name, camera_name]:
            if not test_object_exist(frame_name):
                create_object(frame_name, type="EMPTY")
                set_property(frame_name, "empty_display_size", axis_size)

        output_camera_poses = self._interpolate_camera()
        point_pose = np.eye(4)
        point_pose[:3, 3] = self.gaze_points[0]
        point_poses = [point_pose for _ in range(len(output_camera_poses))]

        set_animation_matrix(point_name, point_poses)
        set_animation_matrix(camera_name, output_camera_poses)
