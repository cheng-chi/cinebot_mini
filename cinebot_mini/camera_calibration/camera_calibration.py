import numpy as np
import cv2
import os
from urllib.request import urlretrieve


def download_sample_data(data_path):
    '''
    Download sample checkerboard images from opencv website

    Inputs:
    - data_path: path to store downloaded files
    '''
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    base_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/"
    image_names = ["left", "right"]
    num_images = ["%.2d" % i for i in range(1, 15)]
    num_images.remove('10')
    for image_name in image_names:
        for num in num_images:
            file_name = image_name + num + ".jpg"
            url = base_url + file_name
            file_path = os.path.join(data_path, file_name)
            urlretrieve(url, file_path)


def get_obj_img_points(imgs, shape):
    '''
    Compute the intrinsic matrix of a single camera

    The input imgs has shape (N, H, W).

    Inputs:
    - imgs: A numpy array containing input data, of shape (N, H, W)
    - shape: num of cols and rows in imgs, of shape (cols, rows)

    Returns:
    - objpoints: list of 2D image points
    - imgpoints: list of 3D points
    '''
    cols, rows = shape
    channels = 3

    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(7,5,0)
    objp = np.zeros((cols * rows, channels), np.float32)
    objp[:, :(channels - 1)] = np.mgrid[0:cols, 0:rows].T.reshape(-1, (channels - 1))

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for i in range(len(imgs)):
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(imgs[i], (cols, rows), None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(imgs[i], corners, (11, 11), (-1, -1), criteria)
            # img = cv2.drawChessboardCorners(imgs[i], (9, 7), corners2,ret)
            # cv2.imshow('img',img)
            # cv2.waitKey(500)

            imgpoints.append(corners2)

    return objpoints, imgpoints


def reject_outliers(data, m=3):
    data = np.array(data)
    return data[abs(data - np.mean(data)) < m * np.std(data)]


def adjust_cv_points(objpoints, imgpoints, cell_shape=(6, 7), cell_edge_meters=0.03):
    dtype = objpoints[0].dtype
    cell_center = (np.array(cell_shape, dtype=dtype) - 1) / 2
    cell_center_3d = np.zeros(3, dtype=dtype)
    cell_center_3d[:2] = cell_center

    new_objpoints = [(x - cell_center_3d) * cell_edge_meters for x in objpoints]
    return new_objpoints, imgpoints


def single_camera_calibration(imgs, cell_shape=(6, 7), cell_edge_meters=0.03, use_undistort=False):
    '''
    Compute the intrinsic matrix of a single camera

    The input imgs has shape (N, H, W).

    Inputs:
    - imgs: A numpy array containing input data, of shape (N, H, W)
    - cell_width: cell width of checkerboards
    - cell_height: cell height of checkerboards
    - distorted: boolean, whether intrinsic matrix is distorted or not
    - cell_length: meter per cell in the checkerboard

    Returns:
    - cameraMatrix: intrinsic matrix, of shape (3, 3)
    - dist: distortion vector, of shape (5,)
    - extrinsics: list of extrinsic matrix, of shape (N, 3, 4)
    '''

    img_shape = imgs[0].shape[:2]
    objpoints, imgpoints = get_obj_img_points(imgs, cell_shape)
    objpoints, imgpoints = adjust_cv_points(objpoints, imgpoints, cell_shape, cell_edge_meters)

    rmserr, intrinsic, dist, rvecs, tvecs = None, None, None, None, None
    if use_undistort:
        flags = cv2.CALIB_FIX_PRINCIPAL_POINT
        rmserr, intrinsic, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_shape, cameraMatrix=None, distCoeffs=None, flags=flags)
    else:
        intrinsic = np.array([
            [1, 0, img_shape[0] / 2],
            [0, 1, img_shape[1] / 2],
            [0, 0, 1]
        ])
        flags = cv2.CALIB_FIX_ASPECT_RATIO | cv2.CALIB_FIX_PRINCIPAL_POINT | cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K1 | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3
        prior_dist = (0, 0, 0, 0, 0)
        rmserr, intrinsic, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_shape, cameraMatrix=intrinsic, distCoeffs=prior_dist, flags=flags)

    extrinsics = [calculate_extrinsic_matrix(rvecs[i], tvecs[i]) for i in range(len(imgs))]
    return intrinsic, dist, extrinsics


def calculate_extrinsic_matrix(rvec, tvec):
    '''
    Compute extrinsic matrix:

    Inputs:
    - rvec: rotation vector
    - tvec: translation vector

    Outputs:
    - extrinsic: extrinsic matrix
    '''
    rmtx, _ = cv2.Rodrigues(rvec)
    extrinsic = np.zeros((4, 4))
    extrinsic[3, 3] = 1
    extrinsic[:3] = np.hstack((rmtx, tvec.reshape(-1, 1)))
    return extrinsic


def undistort_img(img, cameraMatrix, dist):
    '''
    Undistorted img of various channels

    Inputs:
    - img: A numpy array containing input data, of shape (H, W, 3)
    - cameraMatrix: camera intrinsic matrix, of shape (3, 3)
    - dist: distortion coefficients

    Returns:
    - out: undistorted img
    '''
    H, W = img.shape[:2]
    # newcameraMatrix: 3 x 3 extrinsic matrix
    # roi: radius of img
    newcameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, dist, (W, H), 1, (W, H))
    out = cv2.undistort(img, cameraMatrix, dist, None, newcameraMatrix)
    # crop the image
    x, y, w, h = roi
    out = out[y:y + h, x:x + w]
    return out


def single_camera_pose_estimation(img, intrinsics, dist, cell_shape=(6, 7), cell_edge_meters=0.03):
    '''
    Estimate camera pose and compute extrinsic matrix

    Inputs:
    - img: A numpy array containing input data, of shape (H, W)
    - cameraMatrix: camera intrinsic matrix
    - dist: distortion coefficients
    - cell_width: cell width of checkerboards
    - cell_height: cell height of checkerboards
    - cell_length: meter per cell in the checkerboard

    Returns:
    - out: extrinsic matrix in meters, of shape (4, 4)
    '''
    objpoints, imgpoints = get_obj_img_points([img], cell_shape)
    objpoints, imgpoints = adjust_cv_points(objpoints, imgpoints, cell_shape, cell_edge_meters)

    retval, rvec, tvec = cv2.solvePnP(objpoints[0], imgpoints[0], intrinsics, dist)

    extrinsic = calculate_extrinsic_matrix(rvec, tvec)
    return extrinsic


def pix_to_arg(arr):
    return tuple(arr.astype(np.int).reshape(-1))


def plot_axis(img, intrinsic, extrinsic, arrow_length=0.05):
    points = np.array([
        [0, 0, 0, 1],
        [arrow_length, 0, 0, 1],
        [0, arrow_length, 0, 1],
        [0, 0, arrow_length, 1]
    ], dtype=np.float32).T
    points_camera_h = extrinsic @ points
    points_camera = points_camera_h[:3, :] / points_camera_h[3, :]
    points_pixel_h = intrinsic @ points_camera
    points_pixel = points_pixel_h[:2, :] / points_pixel_h[2, :]

    axis_row = points_pixel.T
    new_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # plot x, y, z axis as r, g, b
    cv2.line(new_img, pix_to_arg(axis_row[0]), pix_to_arg(axis_row[1]), color=(255, 0, 0), thickness=3)
    cv2.line(new_img, pix_to_arg(axis_row[0]), pix_to_arg(axis_row[2]), color=(0, 255, 0), thickness=3)
    cv2.line(new_img, pix_to_arg(axis_row[0]), pix_to_arg(axis_row[3]), color=(0, 0, 255), thickness=3)
    return new_img


def plot_corners(img, cell_shape=(6, 7), cell_edge_meters=0.03):
    objpoints, imgpoints = get_obj_img_points([img], cell_shape)
    objpoints, imgpoints = adjust_cv_points(objpoints, imgpoints, cell_shape, cell_edge_meters)
    objpoints, imgpoints = objpoints[0], imgpoints[0]

    new_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for i in range(len(imgpoints) - 1):
        cv2.arrowedLine(new_img, pix_to_arg(imgpoints[i]), pix_to_arg(imgpoints[i + 1]), color=(255, 0, 0), thickness=2)
    return new_img


def camera_matrix_visualization(img, cameraMatrix, dist, cell_width=6, cell_height=7):
    '''
    Draw an image with axis drew on the origin of the checkerboard coordinate frame

    Inputs:
    - img: original imgs
    - cameraMatrix: intrinsic matrix of the camera
    - dist: distortion coefficients
    - cell_width: cell width of checkerboards
    - cell_height: cell height of checkerboards

    Outputs:
    - out: visualized img with cooridnates
    '''
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    channels = 3
    # cell_width, cell_height, channels = 7, 9, 3
    objp = np.zeros((cell_width * cell_height, channels), np.float32)
    objp[:, :(channels - 1)] = np.mgrid[0:cell_height, 0:cell_width].T.reshape(-1, (channels - 1))
    axis = np.float32([[3, 0, 0], [0, 3, 0], [0, 0, -3]]).reshape(-1, 3)
    ret, corners = cv2.findChessboardCorners(img, (cell_height, cell_width), None)

    out = None
    if ret == True:
        corners2 = cv2.cornerSubPix(img, corners, (11, 11), (-1, -1), criteria)
        # Find the rotation and translation vectors.
        ret, rvecs, tvecs = cv2.solvePnP(objp, corners2, cameraMatrix, dist)
        # project 3D points to image plane
        imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, cameraMatrix, dist)
        out = draw(img, corners2, imgpts)
    return out


def draw(img, corners, imgpts):
    '''
    Draw xyz coordinates on img

    Inputs:
    - img: original img
    - corners: refined coordinate
    - imgpts: array of image points

    Outputs:
    - img: img that has coordinates on it 
    '''
    corner = tuple(corners[0].ravel())
    img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (100, 100, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (100, 100, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (100, 100, 0), 5)
    return img


def computeF(cameraMatrix1, cameraMatrix2, R, t):
    '''
    Compute the fundamental matrix.

    Inputs:
    - cameraMatrix1: intrinsic matrix for left img1, of shape (3, 3)
    - cameraMatrix2: intrinsic matrix for right img2, of shape (3, 3)
    - R: rotation matrix from left img to right img, of shape (3, 3)
    - t: translation vector from left img to right img, of shape (3,)

    Outputs:
    - F: the fundamental matrix that relates two point correspondences
        in the left and right image.
    '''
    A = np.dot(cameraMatrix1.dot(R.T), t)
    C = np.array([[0, -A[2], A[1]],
                  [A[2], 0, -A[0]],
                  [-A[1], A[0], 0]])
    F = np.inv(cameraMatrix2).dot(R).dot(cameraMatrix1.T).dot(C)
    return F
