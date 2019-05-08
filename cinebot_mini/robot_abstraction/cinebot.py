import Pynamixel
from cinebot_mini import TRANSFORMS
from cinebot_mini.robot_abstraction.robot import Robot
import time
import numpy as np
from ikpy.chain import Chain
import copy
import sys
import os

""" Radians to/from  Degrees conversions """
D2R = 3.141592 / 180.0
R2D = 180.0 / 3.141592


def get_cinebot_chain():
    dir_name = os.path.dirname(os.path.realpath(__file__))
    urdf_file = os.path.join(dir_name, "Cinebot.URDF")
    chain = Chain.from_urdf_file(urdf_file)
    chain.name = TRANSFORMS["chain_name"]
    return chain

class Cinebot(Robot):
    # DEVICES = [
    #     {
    #         "id": 0,
    #         "type": Pynamixel.devices.MX28,
    #         "params": {
    #             "p_gain": 32,
    #             "i_gain": 20,
    #             "d_gain": 64
    #         }
    #     },
    #     {
    #         "id": 1,
    #         "type": Pynamixel.devices.MX28,
    #         "params": {
    #             "p_gain": 32,
    #             "i_gain": 32,
    #             "d_gain": 64
    #         }
    #     },
    #     {
    #         "id": 2,
    #         "type": Pynamixel.devices.MX28,
    #         "params": {
    #             "p_gain": 32,
    #             "i_gain": 32,
    #             "d_gain": 64
    #         }
    #     },
    #     {
    #         "id": 3,
    #         "type": Pynamixel.devices.AX12,
    #         "params": {
    #             "clockwise_compliance_margin": 1,
    #             "counter_clockwise_compliance_margin": 1,
    #             "punch": 32
    #         }
    #     },
    #     {
    #         "id": 4,
    #         "type": Pynamixel.devices.AX12,
    #         "params": {
    #             "clockwise_compliance_margin": 1,
    #             "counter_clockwise_compliance_margin": 1,
    #             "punch": 32
    #         }
    #     },
    #     {
    #         "id": 5,
    #         "type": Pynamixel.devices.XL320,
    #         "params": {
    #             "p_gain": 64,
    #             "i_gain": 0,
    #             "d_gain": 0
    #         }
    #     }
    # ]

    DEVICES = [
        {
            "id": 0,
            "type": Pynamixel.devices.MX28,
            "params": {
                "p_gain": 32,
                "i_gain": 0,
                "d_gain": 0
            }
        },
        {
            "id": 1,
            "type": Pynamixel.devices.MX28,
            "params": {
                "p_gain": 64,
                "i_gain": 0,
                "d_gain": 0
            }
        },
        {
            "id": 2,
            "type": Pynamixel.devices.MX28,
            "params": {
                "p_gain": 64,
                "i_gain": 0,
                "d_gain": 0
            }
        },
        {
            "id": 3,
            "type": Pynamixel.devices.AX12,
            "params": {
                "clockwise_compliance_margin": 1,
                "counter_clockwise_compliance_margin": 1,
                "punch": 32
            }
        },
        {
            "id": 4,
            "type": Pynamixel.devices.AX12,
            "params": {
                "clockwise_compliance_margin": 1,
                "counter_clockwise_compliance_margin": 1,
                "punch": 32
            }
        },
        {
            "id": 5,
            "type": Pynamixel.devices.XL320,
            "params": {
                "p_gain": 32,
                "i_gain": 0,
                "d_gain": 0
            }
        }
    ]

    def __init__(self, urdf_file=None, port_name=None, retry=1, simulation=False):
        if urdf_file is None:
            dir_name = os.path.dirname(os.path.realpath(__file__))
            urdf_file = os.path.join(dir_name, "Cinebot.URDF")

        if port_name is None:
            if sys.platform == "linux":
                port_name = "/dev/ttyACM1"
            elif sys.platform == "darwin":
                port_name = "/dev/cu.usbmodem14101"
            elif sys.platform == "win32" or sys.platform == "win64":
                port_name = "COM3"
            else:
                raise RuntimeError("No default port for {}! Please specify port_name.".format(sys.platform))
            print("No port_name specified, using default: {}".format(port_name))

        self.hardware = Pynamixel.hardwares.USB2AX(port_name, 1000000)
        self.system = Pynamixel.System(Pynamixel.Bus(self.hardware))

        # add all the servos with corresponding IDs
        # self.system.add_device(Pynamixel.devices.MX28, 0)
        # self.system.add_device(Pynamixel.devices.MX28, 1)
        # self.system.add_device(Pynamixel.devices.MX28, 2)
        # self.system.add_device(Pynamixel.devices.AX12, 3)
        # self.system.add_device(Pynamixel.devices.AX12, 4)
        # self.system.add_device(Pynamixel.devices.XL320, 5)
        # self.num_joints = 6
        for device_config in self.DEVICES:
            device = self.system.add_device(device_config["type"], device_config["id"])
            # for key, val in device_config["params"].items():
            #     getattr(device, key).write(val)
        self.num_joints = len(self.DEVICES)

        # initialize chain for ikpy
        self.chain = Chain.from_urdf_file(urdf_file)
        self.chain.name = TRANSFORMS["chain_name"]
        self.retry = retry

    def initialize(self):
        self.enable_torque()

    def run_with_retry(self, func, args, id):
        for i in range(self.retry):
            try:
                return func(*args)
            except Exception as e:
                print("Servo {} failed due to".format(id), e)
                self.hardware.flush()
                pass
        print("Servo {} failed {} times. Give up!".format(id, self.retry))
        return None

    def set_joint_angle(self, id, joint_angle):
        joint_angle = self.clamp(id, joint_angle)
        encode = self.angle_to_encode(id, joint_angle)
        self.run_with_retry(self.system.get_device(id).goal_position.write, (encode,), id)

    def set_joint_angles(self, joint_angles):
        for i, joint_angle in enumerate(joint_angles):
            self.set_joint_angle(i, joint_angle)

    def get_joint_angle(self, id):
        encode = self.run_with_retry(self.system.get_device(id).present_position.read, tuple(), id)
        return self.encode_to_angle(id, encode)

    def get_joint_angles(self):
        angles = []
        for id in range(self.num_joints):
            angles.append(self.get_joint_angle(id))
        return angles

    def get_end_pose(self):
        angles = self.get_joint_angles()
        return self.chain.forward_kinematics(angles)

    def enable_torque(self):
        for id in range(self.num_joints):
            self.run_with_retry(self.system.get_device(id).torque_enable.write, (1,), id)

    def disable_torque(self):
        for id in range(self.num_joints):
            self.run_with_retry(self.system.get_device(id).torque_enable.write, (0,), id)

    def get_chain(self):
        return copy.deepcopy(self.chain)

    def get_ik(self, pose_matrix):
        angles = self.get_ik(pose_matrix).tolist()
        angles.pop(0)
        return angles

    def set_end_pose(self, pose_matrix):
        angles = self.get_ik(pose_matrix)
        self.set_joint_angles(angles)

    def clamp(self, id, joint_angles):
        # define angle ranges for all servos
        upper_angle = 0.0
        lower_angle = 0.0
        if id == 0:
            upper_angle = 3.14
            lower_angle = -3.14
        elif id == 1:
            upper_angle = 2.18
            lower_angle = -2.18
        elif id == 2:
            upper_angle = 1.85
            lower_angle = -2.09
        elif id == 3:
            upper_angle = 2.61
            lower_angle = -2.61
        elif id == 4:
            upper_angle = 1.81
            lower_angle = -1.86
        elif id == 5:
            upper_angle = 2.61
            lower_angle = -2.61

        if joint_angles > upper_angle:
            return upper_angle
        elif joint_angles < lower_angle:
            return lower_angle
        else:
            return joint_angles

    def angle_to_encode(self, id, joint_angle):
        if id < 3:
            encode = int((R2D * joint_angle + 180) / 0.088)
        else:
            encode = int((R2D * joint_angle + 150) / 0.29)
        return encode

    def encode_to_angle(self, id, encode):
        if id < 3:
            angle = (encode * 0.088 - 180) * D2R
        else:
            angle = (encode * 0.29 - 150) * D2R
        return angle
