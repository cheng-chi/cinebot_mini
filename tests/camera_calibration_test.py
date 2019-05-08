from cinebot_mini.camera_calibration import *
import numpy as np
from matplotlib import pyplot as plt
import glob
import cv2


def main():
    data_path = "./data_iphone/"

    # loading images
    img_paths = sorted(glob.glob(data_path + "*.JPG"))

    resize_factor = 5
    imgs = []
    for i, img_path in enumerate(img_paths):
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.resize(img, (int(img.shape[1] / resize_factor), int(img.shape[0] / resize_factor)))
        imgs.append(img)

    # plt.imshow(imgs[0], cmap='gray')
    # plt.show()

    cell_edge_meters = 0.029
    print("computing intrinsic matrix...")
    intrinsic, dist, extrinsics = single_camera_calibration(
        imgs, cell_shape=(7, 9), cell_edge_meters=cell_edge_meters)
    print(intrinsic)

    img = imgs[-1]
    # H, W = img.shape[:2]
    # newcameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, dist, (W, H), 1, (W, H))

    # estimate camera pose
    print("estimate camera pose with intrinsic...")
    extrinsic = single_camera_pose_estimation(
        img, intrinsic, dist, cell_shape=(7, 9), cell_edge_meters=cell_edge_meters)
    print(extrinsic)

    vis_img = plot_axis(img, intrinsic, extrinsic, cell_edge_meters)
    plt.imshow(vis_img)
    plt.show()
