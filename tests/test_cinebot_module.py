from cinebot_module import Cinebot

test_bot = Cinebot("/dev/ttyACM0", "Cinebot.URDF")

test_bot.set_end_pose([[1, 0, 0, 0.1],
                 [0, 1, 0, 0.1],
                 [0, 0, 1, 0.1],
                 [0, 0, 0, 1.0]])
