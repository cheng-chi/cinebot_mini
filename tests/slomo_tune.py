from cinebot_mini.execution_routine.planner import DirectPlanner
from cinebot_mini.execution_routine.slomo_execution import SlomoModeExecution
from cinebot_mini.robot_abstraction.cinebot import Cinebot
import time
from cinebot_mini.web_utils.camera_client import VideoRecorder, h264_to_mp4

robot = Cinebot()
planner = DirectPlanner(robot)

robot.retry = 10
planner.record()

fps = 120
config_trajectory = planner.plan(duration=3.0, fps=fps)


executor = SlomoModeExecution(robot, config_trajectory, fps)


executor.init()


t = VideoRecorder(fps=110, duration=5.0, iso=400)
t.auto_exposure()


t.capture()
time.sleep(2.5)
executor.execute()


dir_name = "/Users/chengchi/blender_out"
file_path = t.download_video(dir_name, blocking=True)
mp4_path = h264_to_mp4(file_path)
