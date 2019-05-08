from cinebot_mini.execution_routine.planner import DirectPlanner
from cinebot_mini.execution_routine.slomo_execution import SlomoModeExecution
from cinebot_mini.robot_abstraction.cinebot import Cinebot
import time

robot = Cinebot()
planner = DirectPlanner(robot)

planner.record()

fps = 120
config_trajectory = planner.plan(duration=5.0, fps=fps)


executor = SlomoModeExecution(robot, config_trajectory, fps)

# for i in range(10):
executor.init()
# time.sleep(1.0)
executor.execute()


start = time.time()
for i in range(10000):
    robot.set_joint_angles([0,0,0,0,0,0])
end = time.time()
print(end - start)

start = time.time()
for i in range(1000):
    angles = robot.get_joint_angles()
end = time.time()
print(end - start)

start = time.time()
angles = [robot.system.get_device(i).present_position.read() for i in range(6)]
end = time.time()
print(end - start)

start = time.time()
for i in range(1000):
    result = [robot.system.get_device(i).goal_position.write(angles[i]) for i in range(6)]
end = time.time()
print(end - start)


id = 5
start = time.time()
for i in range(1000):
    robot.set_joint_angle(id, 0)
end = time.time()
print(end - start)
