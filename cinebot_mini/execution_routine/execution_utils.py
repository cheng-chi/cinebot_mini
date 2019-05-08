import pickle
import numpy as np


def save_obj(obj, fname):
    attr_dict = dict()
    for attr in obj.DATA_ATTRS:
        attr_dict[attr] = getattr(obj, attr)
    pickle.dump(attr_dict, open(fname, 'wb'))


def load_obj(obj, fname):
    attr_dict = pickle.load(open(fname, 'rb'))
    for key, val in attr_dict.items():
        setattr(obj, key, val)

