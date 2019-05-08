import numpy as np
from ikpy.chain import Chain

# cinebot = Chain.from_urdf_file("/home/chicheng/dev/eecs467/ikpy/resources/poppy_ergo.URDF")

cinebot = Chain.from_urdf_file("Cinebot.URDF")

poppy = Chain.from_urdf_file("../poppy_ergo.URDF")

target_vector = [0, 0.2, 0.2]
target_frame = np.eye(4)
target_frame[:3, 3] = target_vector

print("The angles of each joints are : ", cinebot.inverse_kinematics(target_frame))


