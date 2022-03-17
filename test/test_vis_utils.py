import numpy as np
from hand_embodiment.vis_utils import Insole, PillowSmall
from numpy.testing import assert_array_almost_equal


def test_transform_from_insole_mesh_to_origin():
    artist = Insole(insole_back=np.array([0, 0, 0.1]),
                    insole_front=np.array([0.19, 0, 0.1]))
    p_in_origin = artist.transform_from_mesh_to_origin([0.1, 0.2, 0.3])
    assert_array_almost_equal(p_in_origin, [0.049615, -0.134307, -0.207])


def test_transform_from_pillow_mesh_to_origin():
    pillow_left = np.array([-0.11, 0.13, 0.2])
    pillow_right = np.array([-0.11, -0.13, 0.2])
    pillow_top = np.array([0.11, -0.13, 0.2])
    artist = PillowSmall(pillow_left, pillow_right, pillow_top)
    p_in_origin = artist.transform_from_mesh_to_origin([0.1, 0.2, 0.3])
    assert_array_almost_equal(p_in_origin, [0.22, -0.1, 0.405])
