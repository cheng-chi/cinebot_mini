import bpy
from .bpy_camera_matrix import get_calibration_matrix_K_from_blender

def camera_focal_length_pixel_helper(obj, input_data=None):
    if input_data is not None:
        focal_length_pixel = input_data
        resolution_x_in_px = bpy.context.scene.render.resolution_x
        width_scale = obj.data.sensor_width / resolution_x_in_px
        obj.data.lens = input_data * width_scale
        return focal_length_pixel
    else:
        resolution_x_in_px = bpy.context.scene.render.resolution_x
        width_scale = obj.data.sensor_width / resolution_x_in_px
        return obj.data.lens / width_scale


def camera_intrinsic_matrix_helper(obj, input_data=None):
    if input_data is not None:
        intrinsic_matrix = input_data
        focal_length_pixel = intrinsic_matrix[0][0]
        resolution_x_in_px = bpy.context.scene.render.resolution_x
        width_scale = obj.data.sensor_width / resolution_x_in_px
        obj.data.lens = input_data * width_scale
        return intrinsic_matrix
    else:
        intrinsic_matrix = get_calibration_matrix_K_from_blender(obj.data)
        return intrinsic_matrix
