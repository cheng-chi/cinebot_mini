from cinebot_mini import TRANSFORMS
from cinebot_mini.geometry_utils import TransformationTree
from cinebot_mini.robot_abstraction.cinebot import Cinebot
from cinebot_mini.web_utils.blender_client import *

robot = Cinebot()
chain = robot.get_chain()

tf = TransformationTree()
tf.add_chain("ROOT", chain)
camera_name = TRANSFORMS["robot_camera_name"]
camera_mat = TRANSFORMS["robot_camera_to_robot"]
tf.add_node("joint5", camera_name, camera_mat)

# tf.set_chain_state(chain.name, [0, -0.1, -0.1, -0.1, -0.1, -0.1])
#
# tf.plot_blender()

camera_properties = get_property(camera_name)
b_camera_mat = np.array(camera_properties["properties"]["matrix_world"])

tf.set_transform(camera_name, b_camera_mat)
tf.plot_blender()
