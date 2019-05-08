from .arc_nd_interpolator import ArcNDInterpolator
import numpy as np


class Gaze3DInterpolator:
    def __init__(self, camera_pose, gaze_points, num_cache=21):
        """
        Camera_pos is (a iterable of numpy array with shape (3,)) or (2D numpy array of shape (N, 3)).

        Gaze_points can be either (a single numpy array with shape (3,)), or (a iterable of numpy
        array with shape (3,)) or (2D numpy array of shape (N, 3)). When the input is a single numpy
        array with shape (3,), the camera should always be looking at the same point.
        """
        self.camera_pose = camera_pose

        # For testing
        n = len(camera_pose)
        self.gaze_points = gaze_points
        self.camera_spline = ArcNDInterpolator(camera_pose, num_cache=num_cache)
        self.gaze_spline = None
        if len(self.gaze_points.shape) != 1:
            self.gaze_spline = ArcNDInterpolator(gaze_points, num_cache=num_cache)

    def length(self):
        """
        Return the total arc_length of camera position spline
        """
        return self.camera_spline.length()

    def at(self, arc_length):
        """
        Returns a numpy array with shape (4, 4), representing a homogeneous transform matrix. Evaluates
        camera position at arc length s, and evaluate gaze point at the same ratio of s/total_length
        as camera position.
        """
        camera_pose = self.camera_spline.at(arc_length)
        if len(self.gaze_points.shape) == 1:
            gaze_point = self.gaze_points
        else:
            gaze_spline_length = self.gaze_spline.length()
            gaze_arc_length = arc_length / self.length() * gaze_spline_length
            gaze_point = self.gaze_spline.at(gaze_arc_length)
        return self._get_transform_matrix(camera_pose, gaze_point)

    def generate(self, s_list):
        """
        Batch version of self.at()
        """
        return [self.at(s) for s in s_list]

    def _get_transform_matrix(self, camera_pose, gaze_point):
        gaze_point_local = gaze_point - camera_pose
        z_local = gaze_point_local / np.linalg.norm(gaze_point_local)
        z_global = np.array([0, 0, 1])
        x_local = np.cross(z_local, z_global)
        x_local /= np.linalg.norm(x_local)

        y_local = np.cross(z_local, x_local)

        trans = np.eye(4)
        trans[:3, 0] = x_local
        trans[:3, 1] = y_local
        trans[:3, 2] = z_local
        trans[:3, 3] = camera_pose
        return trans