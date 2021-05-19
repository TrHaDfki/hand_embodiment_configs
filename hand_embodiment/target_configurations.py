import math
import numpy as np
import pytransform3d.transformations as pt
import pytransform3d.rotations as pr
from pkg_resources import resource_filename


###############################################################################
# Mia hand
###############################################################################

def kinematic_model_hook_mia(kin):
    """Extends kinematic model to include links for embodiment mapping."""
    kin.tm.add_transform(
        "thumb_tip", "thumb_fle",
        np.array([
            [1, 0, 0, 0.025],
            [0, 1, 0, 0.08],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
    kin.tm.add_transform(
        "index_tip", "index_fle",
        np.array([
            [1, 0, 0, -0.02],
            [0, 1, 0, 0.09],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
    kin.tm.add_transform(
        "middle_tip", "middle_fle",
        np.array([
            [1, 0, 0, -0.02],
            [0, 1, 0, 0.09],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
    kin.tm.add_transform(
        "ring_tip", "ring_fle",
        np.array([
            [1, 0, 0, -0.017],
            [0, 1, 0, 0.083],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))
    kin.tm.add_transform(
        "little_tip", "little_fle",
        np.array([
            [1, 0, 0, -0.015],
            [0, 1, 0, 0.068],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]))


class MiaVirtualThumbJoint:
    def __init__(self, real_joint_name):
        self.real_joint_name = real_joint_name
        self.min_angle = -0.628
        self.max_angle = 0.0
        self.angle_threshold = 0.5 * (self.min_angle + self.max_angle)

    def make_virtual_joint(self, joint_name, tm):
        limits = tm.get_joint_limits(self.real_joint_name)

        return (joint_name + "_from", joint_name + "_to", np.eye(4),
                np.array([0, 0, 0]), limits, "revolute")

    def __call__(self, value):
        if value >= self.angle_threshold:
            angle = self.max_angle
        else:
            angle = self.min_angle
        return {self.real_joint_name: angle}


manobase2miabase = pt.transform_from(
    R=pr.active_matrix_from_intrinsic_euler_xyz(np.array([-1.634, 1.662, -0.182])),
    p=np.array([0.002, 0.131, -0.024]))
MIA_CONFIG = {
    "joint_names":
        {
            "thumb": ["j_thumb_fle", "j_thumb_opp_binary"],
            "index": ["j_index_fle"],
            "middle": ["j_mrl_fle"],
            "ring": ["j_ring_fle"],
            "little": ["j_little_fle"],
        },
    "base_frame": "palm",
    "ee_frames":
        {
            "thumb": "thumb_tip",
            "index": "index_tip",
            "middle": "middle_tip",
            "ring": "ring_tip",
            "little": "little_tip"
        },
    "handbase2robotbase": manobase2miabase,
    "model":
        {
            # this xacro is actually just plain urdf:
            "urdf": resource_filename(
                "hand_embodiment",
                "model/mia_hand_description/urdf/mia_hand.urdf.xacro"),
            "package_dir": resource_filename("hand_embodiment", "model/"),
            "kinematic_model_hook": kinematic_model_hook_mia
        },
    "virtual_joints_callbacks":
        {
            "j_thumb_opp_binary": MiaVirtualThumbJoint("j_thumb_opp"),
        }
}

###############################################################################
# Shadow dexterous hand
###############################################################################


class ShadowVirtualF0Joint:
    def __init__(self, first_real_joint_name, second_real_joint_name):
        self.first_real_joint_name = first_real_joint_name
        self.second_real_joint_name = second_real_joint_name
        self.first_joint_max = 0.5 * np.pi

    def make_virtual_joint(self, joint_name, tm):
        first_limits = tm.get_joint_limits(self.first_real_joint_name)
        second_limits = tm.get_joint_limits(self.second_real_joint_name)

        joint_range = (second_limits[1] - second_limits[0] +
                       first_limits[1] - first_limits[0])
        return (joint_name + "_from", joint_name + "_to", np.eye(4),
                np.array([0, 0, 0]), (0, joint_range), "revolute")

    def __call__(self, value):
        if value > self.first_joint_max:
            first_joint_value = self.first_joint_max
            second_joint_value = value - self.first_joint_max
        else:
            first_joint_value = value
            second_joint_value = 0.0
        return {self.first_real_joint_name: first_joint_value,
                self.second_real_joint_name: second_joint_value}


manobase2shadowbase = pt.transform_from(
    R=pr.active_matrix_from_intrinsic_euler_xyz(np.array([-3.17, 1.427, 3.032])),
    p=np.array([0.011, -0.014, 0.36]))
SHADOW_HAND_CONFIG = {
    "joint_names":
        {  # wrist: rh_WRJ2, rh_WRJ1
            "thumb": ["rh_THJ5", "rh_THJ4", "rh_THJ3", "rh_THJ2", "rh_THJ1"],
            "index": ["rh_FFJ4", "rh_FFJ3", "rh_FFJ0"],
            "middle": ["rh_MFJ4", "rh_MFJ3", "rh_MFJ0"],
            "ring": ["rh_RFJ4", "rh_RFJ3", "rh_RFJ0"],
            "little": ["rh_LFJ5", "rh_LFJ4", "rh_LFJ3", "rh_LFJ0"],
        },
    "base_frame": "rh_forearm",
    "ee_frames":
        {
            "thumb": "rh_thtip",
            "index": "rh_fftip",
            "middle": "rh_mftip",
            "ring": "rh_rftip",
            "little": "rh_lftip"
        },
    "handbase2robotbase": manobase2shadowbase,
    "model":
        {
            "urdf": resource_filename(
                "hand_embodiment",
                "model/sr_common/sr_description/urdf/shadow_hand.urdf"),
            "package_dir": resource_filename(
                "hand_embodiment", "model/sr_common/"),
            "kinematic_model_hook": lambda x: x  # TODO
        },
    "virtual_joints_callbacks":
        {
            "rh_FFJ0": ShadowVirtualF0Joint("rh_FFJ2", "rh_FFJ1"),
            "rh_MFJ0": ShadowVirtualF0Joint("rh_MFJ2", "rh_MFJ1"),
            "rh_RFJ0": ShadowVirtualF0Joint("rh_RFJ2", "rh_RFJ1"),
            "rh_LFJ0": ShadowVirtualF0Joint("rh_LFJ2", "rh_LFJ1"),
        }
}
