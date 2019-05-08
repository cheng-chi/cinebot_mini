import ikpy
import numpy as np
from ete3 import Tree
from cinebot_mini.web_utils.blender_client import *
from cinebot_mini.geometry_utils.closed_form_ik import inverse_kinematics_closed_form


class TransformationTree:
    def __init__(self):
        """A dictionary containing children of a node"""
        self.children = {}
        """A dictionary containing parent of a node"""
        self.parent = {}
        """A dictionary containing transformation to its parent.
        If node is link on ikpy chain, this entry should store the name of the chain."""
        self.transforms = {}
        """A dictionary mapping chain name to ikpy Chain object."""
        self.chains = {}
        """A dictionary stores joint angles of a ikpy Chain"""
        self.chain_states = {}

        self.tree = Tree()

        self.transforms["ROOT"] = np.eye(4)

    def add_node(self, parent_name, child_name, matrix):
        """
        parent_	name: string
        child_name: string, the name of this node
        matrix: 4x4 homogeneous matrix, relative to parent
        """
        if child_name in self.parent:
            raise NameError
        self.parent[child_name] = parent_name
        self.transforms[child_name] = matrix

        if parent_name not in self.children:
            self.children[parent_name] = []
        self.children[parent_name].append(child_name)

    def add_chain(self, parent_name, chain: ikpy.chain.Chain):
        """
        parent_name: string
        chain: ikpy.chain.Chain
        """
        chain_name = chain.name

        if chain_name in self.chains:
            raise NameError
        self.chains[chain_name] = chain

        self.add_node(parent_name, chain.links[0].name, np.eye(4))

        for i in range(len(chain.links)-1):
            self.add_node(chain.links[i].name, chain.links[i+1].name, chain_name)

        default_state = [0 for _ in range(len(chain.links) - 1)]
        self.set_chain_state(chain_name, default_state)

    def set_chain_state(self, chain_name, state):
        """
        Chain_name: string
        State: (a Iterable of floats) or (a 1D numpy array)
        The length of the state should match the corresponding chain. If not, raise an exception.
        """
        if len(self.chains[chain_name].links) != (len(state) + 1):
            raise ValueError
        self.chain_states[chain_name] = state

    def get_ancestor(self, node):
        # ancestor = [node]
        ancestor = []
        while node in self.parent:
            node = self.parent[node]
            ancestor.append(node)
        return ancestor

    def get_transform_same(self, to_name, from_name, ancestor):
        """
        Return the 4x4 homogeneous matrix from two nodes on the same branch
        """
        trace = ancestor[: ancestor.index(to_name)]
        trace.insert(0, from_name)

        H = np.eye(4)
        chain_name = ''
        link_count = 0

        for i in range(len(trace)):
            node = trace[i]
            if type(self.transforms[node]) == str:
                if self.transforms[node] != chain_name:
                    chain_name = self.transforms[node]
                    link_count = 0
                link_count += 1

            else:
                # either a node or a chain base
                if link_count > 0:
                    chain = self.chains[chain_name]
                    state = self.chain_states[chain_name]
                    link_transform = chain.forward_kinematics([0] + list(state), full_kinematics=True)[link_count]
                    H = np.dot(link_transform, H)
                    link_count = 0

                H = np.dot(self.transforms[node], H)

        if link_count > 0:
            # to_name is a link in a chain
            chain = self.chains[chain_name]
            state = self.chain_states[chain_name]
            if type(self.transforms[to_name]) != str:
                # to_name is the chain base
                link_transform = chain.forward_kinematics([0] + list(state), full_kinematics=True)[link_count]
                H = np.dot(link_transform, H)
            else:
                # find the position of from_name link
                for j in range(len(chain.links)):
                    if chain.links[j].name == from_name:
                        break
                # to_name -> links[j]
                # end link -> links[j + link_count]
                forward_transforms = chain.forward_kinematics(state, full_kinematics=True)
                end_base = forward_transforms[j + link_count]
                from_base = forward_transforms[j]
                # end_base = from_base * end_from
                end_from = np.dot(np.array(np.mat(from_base).I), end_base)
                H = np.dot(end_from, H)

        return H

    def get_transform(self, from_name, to_name="ROOT"):
        """
        from_name: string
        to_name: string
        Should return 4x4 homogeneous matrix from “from_name” node to “to_name” node.
        Note: the two frames queried might not be on the same branch of the transformation tree! Some non-trivial tree traversal algorithm is needed.
        """
        if to_name == from_name:
            return np.mat(np.eye(4))

        from_name_ancestor = self.get_ancestor(from_name)
        # print(to_name_ancestor)
        if to_name in from_name_ancestor:
            # to_name and from_name are on the same branch
            return self.get_transform_same(to_name, from_name, from_name_ancestor)

        to_name_ancestor = self.get_ancestor(to_name)
        # print(from_name_ancestor)
        if from_name in to_name_ancestor:
            # from_name is descendant of to_name
            return np.array(np.mat(self.get_transform_same(from_name, to_name, to_name_ancestor)).I)

        common_ancestor = None
        # to_name and from_name are on different branches
        for i in range(len(from_name_ancestor)):
            if from_name_ancestor[i] in to_name_ancestor:
                common_ancestor = from_name_ancestor[i]
                break
        from_common = self.get_transform_same(common_ancestor, from_name, from_name_ancestor)
        to_common = self.get_transform_same(common_ancestor, to_name, to_name_ancestor)
        # from_common = to_common * from_to
        from_to = np.dot(np.array(np.mat(to_common).I), from_common)
        return from_to

    def set_transform(self, frame_name, transform_mat):
        """
        Sets state of nearest parent chain, raises exception if cannot be done.
        :param frame_name:
        :param transform_mat:
        :return:
        """
        chain_name = None
        top_to_end_effector = np.eye(4)
        chain_root_to_root = np.eye(4)

        curr_frame = frame_name
        while True:
            if curr_frame not in self.parent:
                # we are at root
                break
            if type(self.transforms[curr_frame]) is str:
                # we found the first chain
                chain_name = self.transforms[curr_frame]
                chain_root_name = self.chains[chain_name].links[0].name
                chain_root_to_root = self.get_transform(chain_root_name)
                break
            curr_to_parent = self.transforms[curr_frame]
            top_to_end_effector = curr_to_parent @ top_to_end_effector
            curr_frame = self.parent[curr_frame]

        if chain_name is None:
            raise RuntimeError("Could not find chain between this frame and ROOT.")

        end_effector_to_chain_root = np.linalg.inv(chain_root_to_root)\
                                     @ transform_mat\
                                     @ np.linalg.inv(top_to_end_effector)
        initial_config = self.chain_states[chain_name]
        # new_config = self.chains[chain_name].inverse_kinematics(
        #     end_effector_to_chain_root, [0] + list(initial_config))

        try:
            # new_config = inverse_kinematics_closed_form(
            #     self.chains[chain_name],
            #     end_effector_to_chain_root,
            #     [0] + list(initial_config))
            new_config = inverse_kinematics_closed_form(
                self.chains[chain_name],
                end_effector_to_chain_root)
            self.set_chain_state(chain_name, new_config[1:])
        except ValueError as e:
            print("Value error, transform:")
            print(transform_mat)

    def get_subtree(self, t, node_name):
        if node_name in self.children:
            tree_node = t.search_nodes(name=node_name)[0]

            for child in self.children[node_name]:
                tree_node.add_child(name=child)

            for child in self.children[node_name]:
                t = self.get_subtree(t, child)
        return t

    def get_ete(self):
        """
        Return a ete3.Tree representing the topology of the transformation tree, with each node having its corresponding name.
        """
        return self.get_subtree(Tree("ROOT;"), "ROOT")

    def plot(self):
        """
        Plot the tree with ete3
        """
        self.tree = self.get_ete()
        print(self.tree.get_ascii(show_internal=True))

    def plot_blender(self, axis_size=0.05):
        for frame_name in self.transforms.keys():
            if not test_object_exist(frame_name):
                create_object(frame_name, type="EMPTY")
                set_property(frame_name, "empty_display_size", axis_size)

        for frame_name in self.transforms.keys():
            matrix = self.get_transform(frame_name)
            set_transform_matrix(frame_name, matrix)

    def set_transform_blender(self, frame_name):
        assert(frame_name in self.transforms)
        camera_properties = get_property(frame_name)
        b_camera_mat = np.array(camera_properties["properties"]["matrix_world"])
        self.set_transform(frame_name, b_camera_mat)

    def add_node_relative(self, parent_name, child_name,  reference_name, child_ref):
        """
        parent_name: string, the name of the parent node
        child_name: string, the name of this node
        Referece_name: string, the name of reference node
        child_ref: 4x4 homogeneous matrix, relative to reference node
        """
        parent_ref = self.get_transform(parent_name, reference_name)
        # child_ref = parent_ref * child_parent
        child_parent = np.dot(np.array(np.mat(parent_ref).I), child_ref)
        self.add_node(parent_name, child_name, child_parent)
