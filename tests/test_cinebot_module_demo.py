from cinebot_module import Cinebot
import time

test_bot = Cinebot("/dev/ttyACM1", "Cinebot.URDF")
test_bot.disable_torque()

angles_list = []

angles_list.append(test_bot.get_joint_angles())

test_bot.enable_torque()

for angles in angles_list:
    test_bot.set_joint_angles(angles)
    time.sleep(1)

