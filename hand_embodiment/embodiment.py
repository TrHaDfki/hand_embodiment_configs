import numpy as np

from .kinematics import Kinematics
from .record_markers import make_finger_kinematics
import pytransform3d.transformations as pt


class HandEmbodiment:
    def __init__(self, hand_state, target_config, mano_finger_kinematics=None):
        self.hand_state = hand_state
        self.manobase2handbase = target_config["manobase2handbase"]
        if mano_finger_kinematics is None:
            self.mano_finger_kinematics = {
                "index": make_finger_kinematics(self.hand_state, "index")
            }
        else:
            self.mano_finger_kinematics = mano_finger_kinematics
        self.target_kin = load_kinematic_model(target_config)
        # TODO for each finger
        self.index_chain = self.target_kin.create_chain(
            target_config["joint_names"]["index"],
            target_config["base_frame"],
            target_config["ee_frames"]["index"])
        self.q = np.zeros(len(target_config["joint_names"]["index"]))

    def solve(self):
        # TODO for each finger
        index_tip_in_manobase = self.mano_finger_kinematics["index"].forward(
            self.hand_state.pose[self.mano_finger_kinematics["index"].finger_pose_param_indices])
        index_tip_in_handbase = pt.transform(
            self.manobase2handbase, pt.vector_to_point(index_tip_in_manobase))
        self.q = self.index_chain.inverse_position(index_tip_in_handbase[:3], self.q)
        return pt.translate_transform(np.eye(4), index_tip_in_handbase), self.q


def load_kinematic_model(hand_config):
    model = hand_config["model"]
    with open(model["urdf"], "r") as f:
        kin = Kinematics(urdf=f.read(), package_dir=model["package_dir"])
    if "kinematic_model_hook" in model:
        model["kinematic_model_hook"](kin)
    return kin
