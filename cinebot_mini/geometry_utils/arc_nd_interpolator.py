import numpy as np
from scipy.interpolate import splprep, splev
from scipy.integrate import quad


np.seterr(all="raise")


class ArcNDInterpolator:
    def __init__(self,
                 input_path,
                 num_cache=21,
                 input_smoothing=0.0,
                 output_smoothing=0.0,
                 bisection_error=0.0001,
                 max_count=10000,
                 step=0.0001):
        """ Input path is an iterable (e.g List) of 1D numpy arrays. Or a 2D numpy array.
            Should generate all intermediate variables here"""

        #  Algorithm parameters
        self.num_intermediate_point = num_cache
        self.bisection_error = bisection_error
        self.max_count = max_count
        self.desired_t_step = step

        #  preprocess input spline
        self.input_path = input_path
        self.input_t = np.arange(len(input_path))  # input parameter, assumed as time
        # generate spline parameter
        input_length = len(self.input_path)
        input_s = input_smoothing * (input_length - np.sqrt(2 * input_length))
        tck, u = splprep(self.input_path.T, u=self.input_t, k=3, s=input_s)
        self.input_spline_params = tck
        self.input_arc_lengths = self._generate_spline_arc_length()

        #  devidie into m equally spaced splines
        self.intermediate_arc_lengths = np.linspace(
            self.input_arc_lengths[0], self.input_arc_lengths[-1], self.num_intermediate_point)
        self.intermediate_t = self._find_intermediate_t()
        self.intermediate_path = np.array(self._find_intermediate_path())
        output_s = output_smoothing * (num_cache - np.sqrt(2 * num_cache))
        tck, u = splprep(self.intermediate_path.T, u=self.intermediate_arc_lengths, k=3, s=output_s)
        self.intermediate_spline_params = tck

    def length(self):
        return self.input_arc_lengths[-1]

    def at(self, arc_length):
        return np.array(splev(arc_length, self.intermediate_spline_params))

    def generate(self, arc_length_list):
        return np.array(splev(arc_length_list, self.intermediate_spline_params)).T

    def _find_intermediate_path(self):
        intermediate_path = [self.input_path[0]]
        for i in range(1, self.num_intermediate_point - 1):
            intermediate_path.append(
                self._interpolate_at_t(self.intermediate_t[i]))
        intermediate_path.append(self.input_path[-1])
        return intermediate_path

    def _interpolate_at_t(self, t):
        return splev(t, self.input_spline_params)

    def _find_intermediate_t(self):
        intermediate_t = [0]
        for i in range(1, self.num_intermediate_point - 1):
            intermediate_t.append(
                self._find_t_at_arc_length(self.intermediate_arc_lengths[i]))
        intermediate_t.append(self.input_t[-1])
        return intermediate_t

    def _find_t_at_arc_length(self, arc_length):
        left_anchor_input_index = 0
        for i in range(len(self.input_arc_lengths)):
            if self.input_arc_lengths[i] > arc_length:
                left_anchor_input_index = i - 1
                break

        left_anchor_t = self.input_t[left_anchor_input_index]
        left_t = left_anchor_t
        left_anchor_arc_length = self.input_arc_lengths[left_anchor_input_index]
        right_t = self.input_t[left_anchor_input_index + 1]

        count = 0
        mid_t = (left_t + right_t) / 2
        while count < self.max_count:
            mid_t = (left_t + right_t) / 2
            arc_length_to_left = self._integrate_arc_length_interval(left_anchor_t, mid_t)
            mid_arc_length = left_anchor_arc_length + arc_length_to_left
            if abs(mid_arc_length - arc_length) < self.bisection_error:
                return mid_t
            if mid_arc_length < arc_length:
                left_t = mid_t
            if mid_arc_length > arc_length:
                right_t = mid_t
            count += 1
        return mid_t

    def _generate_spline_arc_length(self):
        arc_lengths = [0]
        for i in range(len(self.input_t) - 1):
            curr_arc_length = self._integrate_arc_length_interval(
                self.input_t[i], self.input_t[i + 1])
            arc_lengths.append(arc_lengths[-1] + curr_arc_length)
        return arc_lengths

    def _integrate_arc_length_interval(self, time1, time2):
        func = lambda t: np.linalg.norm(splev(t, self.input_spline_params, der=1))
        arc_length, abserr = quad(func, time1, time2)
        return arc_length

    def _integrate_arc_length_interval_finite(self, time1, time2):
        time_length = np.abs(time1 - time2)
        num_segments = int(np.ceil(np.abs(time1 - time2) / self.desired_t_step))
        if num_segments < 1:
            return 0.0

        true_step_size = time_length / num_segments
        t_arr = np.linspace(min(time1, time2), max(time1, time2), num_segments)
        # integrate up until last to avoid duplication
        vel_array = np.array(splev(t_arr[:-1], self.input_spline_params, der=1))
        segment_lengths = np.linalg.norm(vel_array * true_step_size, axis=0)
        arc_length = np.sum(segment_lengths)
        return arc_length

