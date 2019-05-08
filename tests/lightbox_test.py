from cinebot_mini.execution_routine.planner import (
    DirectPlanner,
    GazePlanner,
    save_planner,
    load_planner)
from cinebot_mini.execution_routine.lightbox_planner import LightBoxPlanner
from cinebot_mini.execution_routine.slomo_execution import SlomoModeExecution
from cinebot_mini.execution_routine.lightbox_execution import LightboxExecution
from cinebot_mini.robot_abstraction.cinebot import Cinebot
from cinebot_mini.geometry_utils.transformation_tree import TransformationTree
from cinebot_mini import TRANSFORMS
import numpy as np
import time
import pickle
import time
from cinebot_mini.web_utils.camera_client import VideoRecorder, h264_to_mp4
from cinebot_mini.web_utils.display_client import get_screen_configs
from cinebot_mini.web_utils.blender_client import *
import skvideo.io

robot = Cinebot(port_name="/dev/ttyACM0")
chain = robot.get_chain()

tf = TransformationTree()
tf.add_chain("ROOT", chain)
camera_name = TRANSFORMS["robot_camera_name"]
camera_mat = TRANSFORMS["robot_camera_to_robot"]

tf.add_node("joint5", camera_name, camera_mat)

planner = GazePlanner(robot, tf)

robot.retry = 10
subject_pos = np.array([0, 0.35, 0.06])
planner.add_gaze_point(gaze_point=subject_pos)

planner.record_camera_pose()

planner.duration = 1.0
planner.fps = 120

planner.blender_animate_input()
planner.cache_dirty = True
planner.blender_animate()

# plan_file = "/Users/chengchi/blender_out/circle_icecream.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_coke.pk"
# plan_file = "/Users/chengchi/blender_out/circle_honey.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_seeweed.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_candy.pk"
# plan_file = "/Users/chengchi/Desktop/circle_plan.pk"
# plan_file = "/Users/chengchi/blender_out/circle_plan.pk"

# plan_file = "/home/chicheng/dev/eecs467/plans/circle_icecream.pk"
plan_file = "/home/chicheng/dev/eecs467/plans/drop_plan_coke.pk"
# plan_file = "/Users/chengchi/blender_out/circle_honey.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_seeweed.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_candy.pk"
# plan_file = "/Users/chengchi/Desktop/circle_plan.pk"
# plan_file = "/Users/chengchi/blender_out/circle_plan.pk"
# save_planner(planner, plan_file)
load_planner(planner, plan_file)


lb_planner = LightBoxPlanner()
lb_planner.add_subject(position=subject_pos)

screen_configs = get_screen_configs()

screen_config = {
    "width_pixels": 1920,
    "height_pixels": 1080,
    "width_meters": 0.517,
    "height_meters": 0.285
}

screen_configs = dict()
for i in range(4):
    screen_configs[str(i)] = screen_config

screen_transforms = {
    "0": np.array([
        [0.70710677, 0.70710677, 0, -0.27],
        [-0.70710677, 0.70710677, 0, 0.02],
        [0, 0, 1, 0.18],
        [0, 0, 0, 1]
    ]),
    "1": np.array([
        [-0.70710677, 0.70710677, 0, -0.23],
        [-0.70710677, -0.70710677, 0, 0.53],
        [0, 0, 1, 0.18],
        [0, 0, 0, 1]
    ]),
    "2": np.array([
        [-0.70710677, -0.70710677, 0, 0.23],
        [0.70710677, -0.70710677, 0, 0.53],
        [0, 0, 1, 0.18],
        [0, 0, 0, 1]
    ]),
    "3": np.array([
        [0.70710677, -0.70710677, 0, 0.27],
        [0.70710677, 0.70710677, 0, 0.02],
        [0, 0, 1, 0.18],
        [0, 0, 0, 1]
    ])
}


for key, val in screen_configs.items():
    transform = screen_transforms[key]
    pixel_dims = (val["width_pixels"], val["height_pixels"])
    real_dims = (val["width_meters"], val["height_meters"])
    name = key
    lb_planner.add_screen(name, pixel_dims, real_dims, transform)


config_trajectory = planner.plan()
# config_trajectory = config_trajectory[10:]

# subject_pose = np.eye(4)
# subject_pose[:3, 3] = subject_pos
subject_pose = get_animation("virtual_subject")
lb_planner.set_all_animation(subject_pose, config_trajectory)

# render_dir = "/Users/chengchi/blender_out/lb_test"
render_dir = "/home/chicheng/dev/eecs467/renders/scene1"
lb_planner.render_all(render_dir)


executor = LightboxExecution(robot, config_trajectory, render_dir, 240.0)


executor.init()

executor.preview(duration=5.0)

executor.param_dict = {
    # 'awb_gains': ['135/128', '701/256'],
    "awb_gains": ["171/128", "35/16"],
    'iso': 400,
    'resolution': [3280, 2464],
    'shutter_speed': 60000
}

executor.init()

executor.execute()


save_dir = "/home/chicheng/dev/eecs467/results/scene2"
pk_name = os.path.join(save_dir, "executor.pk")
# save_obj(executor, pk_name)
load_obj(executor, pk_name)

executor.download_all(save_dir)
