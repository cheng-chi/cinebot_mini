from cinebot_mini.execution_routine.planner import (
    DirectPlanner,
    GazePlanner,
    save_planner,
    load_planner)
from cinebot_mini.execution_routine.slomo_execution import SlomoModeExecution
from cinebot_mini.robot_abstraction.cinebot import Cinebot
from cinebot_mini.geometry_utils.transformation_tree import TransformationTree
from cinebot_mini import TRANSFORMS
import numpy as np
import time
import pickle
import time
from cinebot_mini.web_utils.camera_client import VideoRecorder, h264_to_mp4
import skvideo.io

robot = Cinebot()
chain = robot.get_chain()

tf = TransformationTree()
tf.add_chain("ROOT", chain)
camera_name = TRANSFORMS["robot_camera_name"]
camera_mat = TRANSFORMS["robot_camera_to_robot"]

tf.add_node("joint5", camera_name, camera_mat)

planner = GazePlanner(robot, tf)

robot.retry = 10
planner.add_gaze_point()
planner.add_gaze_point(gaze_point=np.array([0, 0.35, 0.06]))

planner.record_camera_pose()

planner.duration = 1.0
planner.fps = 120

planner.blender_animate_input()
planner.cache_dirty = True
planner.blender_animate()

# plan_file = "/Users/chengchi/blender_out/circle_icecream.pk"
plan_file = "/Users/chengchi/blender_out/drop_plan_coke.pk"
# plan_file = "/Users/chengchi/blender_out/circle_honey.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_seeweed.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan.pk"
# plan_file = "/Users/chengchi/blender_out/drop_plan_candy.pk"
# plan_file = "/Users/chengchi/Desktop/circle_plan.pk"
# plan_file = "/Users/chengchi/blender_out/circle_plan.pk"
# save_planner(planner, plan_file)
load_planner(planner, plan_file)

config_trajectory = planner.plan()
# config_trajectory = config_trajectory[10:]

executor = SlomoModeExecution(robot, config_trajectory, 120)

executor.init()

t = VideoRecorder(fps=110, duration=6.0, iso=300)
# t.auto_exposure()
t.param_dict = {
    'awb_gains': ['107/64', '441/256'],
    'iso': 400,
    'resolution': [1280, 720],
    'shutter_speed': 5794
}
t.capture()

time.sleep(2.5)
executor.execute()


dir_name = "/Users/chengchi/blender_out"
file_path = t.download_video(dir_name, blocking=True)
mp4_path = h264_to_mp4(file_path)

d = skvideo.io.ffprobe(mp4_path)
fps = d['video']['@avg_frame_rate']
duration = float(d['video']['@duration'])

for i in range(10):
    executor.init()
    time.sleep(1.0)
    executor.execute()



