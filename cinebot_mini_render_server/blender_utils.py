import bpy
import numpy as np
from mathutils import Color, Euler, Matrix, Quaternion, Vector

ARRAY_PROPERTIES = {Color, Euler, Matrix, Quaternion, Vector}


def jsonify_property(property):
    result = property
    if type(property) in ARRAY_PROPERTIES:
        arr = np.array(property)
        result = arr.tolist()
    return result


def set_property(obj, prop_name, value):
    t = type(getattr(obj, prop_name))
    if t in ARRAY_PROPERTIES:
        arr = t(value)
        setattr(obj, prop_name, arr)
    else:
        setattr(obj, prop_name, value)
