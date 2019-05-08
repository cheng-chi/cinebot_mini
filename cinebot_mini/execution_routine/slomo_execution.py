from cinebot_mini.robot_abstraction.robot import Robot
import numpy as np
import time


class SlomoModeExecution:
    def __init__(self, robot: Robot, config_trajectory, fps=60):
        self.robot = robot
        self.config_trajectory = config_trajectory
        self.fps = fps

    def init(self):
        self.robot.enable_torque()
        self.robot.set_joint_angles(self.config_trajectory[0])

    def execute(self):
        start_time = time.time()
        last_time = time.time()
        for i in range(len(self.config_trajectory)):
            config = self.config_trajectory[i]
            self.robot.set_joint_angles(config)
            print(i)
            curr_time = time.time()
            time_diff = 1.0/self.fps - (curr_time - last_time)
            if time_diff > 0:
                print("Sleep {}".format(time_diff))
                time.sleep(time_diff)
            last_time = curr_time
        end_time = time.time()
        print("Total time: {}".format(end_time - start_time))
