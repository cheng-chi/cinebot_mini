import numpy as np

SERVERS = {
    "blender": {
        "host": "localhost",
        "port": 8089
    },
    "camera": {
        "host": "192.168.2.126",
        "port": 80
    },
    "display": {
        "host": "0.0.0.0",
        "port": 8088
    }
}

TRANSFORMS = {
    "chain_name": "cinebot_mini",
    "robot_camera_name": "pi_camera",
    "robot_camera_to_robot": np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0.022],
        [0, 0, 0, 1]
    ])
}
