from ikpy.chain import Chain
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

def wrap_to_pi(degree):
	if(degree > math.pi):
		return degree - math.pi*2
	elif(degree < -math.pi):
		return degree + math.pi*2
	else:
		return degree


def check_valid(state, bounds):
	for i in range(6):
		if((state[i] < bounds[i][0]) or (state[i] > bounds[i][1])):
			return False
	return True
				

def inverse_kinematics_closed_form(chain, end_effector_pose, initial_position=[0,0,0,0,0,0,0]):
	'''
	Chain: ikpy.chain.Chain
	End_effector_pose: 4x4 numpy array
	Initial_position: list/1D numpy array of length 7
	Return: list of length 7
	'''

	if(chain == None):
		raise RuntimeError("Could not find chain.")

	if(len(initial_position) != 7):
		raise RuntimeError("Invalid initial angle state.")

	link_len = [chain.links[i].length for i in range(1, len(chain.links))]
	joint_bounds = [chain.links[i].bounds for i in range(1, len(chain.links))]

	possible_states = []
	theta = np.zeros(6)
	joint_poses = np.zeros((6,3))

	end_pose = end_effector_pose[:3, 3]
	end_rot = end_effector_pose[:3, :3]

	joint_poses[0] = [0.0, 0.0, link_len[0]]
	joint_poses[1] = [0.0, 0.0, link_len[0]+link_len[1]]
	joint_poses[5] = end_pose
	z_axis = np.array([0.0, 0.0, 1.0])
	joint_poses[4] = joint_poses[5] - link_len[5]* np.dot(end_rot, z_axis)
	
	theta[0] = wrap_to_pi(math.atan2(joint_poses[4][1], joint_poses[4][0])-math.pi/2)
	
	delta_l = np.linalg.norm(joint_poses[4]-joint_poses[1])
	l_a = link_len[3] + link_len[4]
	l_b = link_len[2]
	cos_theta2 = (l_a*l_a + l_b*l_b - delta_l*delta_l) / (2*l_a*l_b)
	if(cos_theta2 >1 or cos_theta2 < -1):
		raise ValueError

	sin_beta = (joint_poses[4][2]-joint_poses[1][2])/delta_l
	if(sin_beta >1 or sin_beta < -1):
		raise ValueError
	beta = np.arcsin(sin_beta)
	
	cos_phi = (delta_l*delta_l + l_b*l_b - l_a*l_a) / (2*l_b*delta_l)
	if(cos_phi >1 or cos_phi < -1):
		raise ValueError
	phi = np.arccos(cos_phi)
	
	if(cos_theta2 == -1):
		# one solution
		theta[2] = np.arccos(-cos_theta2)
		theta[1] = beta - math.pi/2
		possible_states.append(theta)

	elif(cos_theta2 == 1):
		# unreachable 
		raise RuntimeError("Cannot find reachable state.")

	else:
		# two possible solutions
		theta[2] = -np.arccos(-cos_theta2)
		theta[1] = wrap_to_pi(beta + phi - math.pi/2)
		possible_states.append(theta.copy())

		theta[2] = np.arccos(-cos_theta2)
		theta[1] = wrap_to_pi(beta - phi - math.pi/2)
		possible_states.append(theta.copy())

	# finish theta 0, 1, 2

	valid_states = []

	# Change to fram joint_2 and calculate theta[3], [4], [5]
	for i in range(len(possible_states)):

		theta_state = possible_states[i]
		H_2_global = chain.forward_kinematics(np.insert(theta_state, 0, 0.0), full_kinematics=True)[3]
		# end_effector_pose = H_2_global * H_end_2
		H_end_2 = np.dot(np.array(np.mat(H_2_global).I), end_effector_pose)
		end_pose_inf2 = H_end_2[:3,3]
		
		# two possibilities for theta3
		theta3_possible = [wrap_to_pi(math.atan2(end_pose_inf2[1], end_pose_inf2[0])-math.pi/2),wrap_to_pi(math.atan2(-end_pose_inf2[1], -end_pose_inf2[0])-math.pi/2)]

		for theta3 in theta3_possible:
			theta_state[3] = theta3
			H_3_global = chain.forward_kinematics(np.insert(theta_state, 0, 0.0), full_kinematics=True)[4]
			# end_effector_pose = H_3_global * H_end_3
			H_end_3 = np.dot(np.array(np.mat(H_3_global).I), end_effector_pose)
			end_pose_inf3 = H_end_3[:3,3]
			delta_z = end_pose_inf3[2] - link_len[4]
			delta_y = end_pose_inf3[1]
			theta_state[4] = -math.atan2(delta_y, delta_z)

			H_4_global = chain.forward_kinematics(np.insert(theta_state, 0, 0.0), full_kinematics=True)[5]
			# end_effector_pose = H_4_global * H_end_4
			H_end_4 = np.dot(np.array(np.mat(H_4_global).I), end_effector_pose)
			theta_state[5] = R.from_dcm(H_end_4[:3, :3]).as_rotvec()[2]

			if(check_valid(theta_state, joint_bounds)):
				valid_states.append(np.insert(theta_state, 0, 0.0).copy())


	if(len(valid_states) == 0):
		raise RuntimeError("Cannot find reachable state.")
	elif(len(valid_states) == 1):
		return valid_states[0]
	else:
		# select the closest state to initial_position
		init_pose = np.array(initial_position)
		min_dis = 10000.0
		min_state = None
		for i in range(len(valid_states)):
			dis = np.linalg.norm(valid_states[i] - init_pose)
			if(dis < min_dis):
				min_dis = dis
				min_state = valid_states[i]
		return min_state
