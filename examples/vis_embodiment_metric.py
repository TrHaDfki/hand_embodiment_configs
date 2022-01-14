import numpy as np
import open3d as o3d
import pytransform3d.visualizer as pv
from mocap.mano import HandState
from hand_embodiment.embodiment import HandEmbodiment
from hand_embodiment.target_configurations import MIA_CONFIG, manobase2miabase
from hand_embodiment.metrics import (
    highlight_mesh_vertices, MANO_CONTACT_SURFACE_VERTICES,
    highlight_graph_visuals, MIA_CONTACT_SURFACE_VERTICES,
    extract_mano_contact_surface, extract_graph_vertices,
    distances_robot_to_mano)


default_mano_pose = np.array([
    0, 0, 0,
    -0.068, 0, 0.068,
    0, 0.068, 0.068,
    0, 0, 0.615,
    0, 0.137, 0.068,
    0, 0, 0.137,
    0, 0, 0.683,
    0, 0.205, -0.137,
    0, 0.068, 0.205,
    0, 0, 0.205,
    0, 0.137, -0.137,
    0, -0.068, 0.273,
    0, 0, 0.478,
    0.615, 0.068, 0.273,
    0, 0, 0,
    0, 0, 0
])

mano_pose = np.copy(default_mano_pose)
mano_pose[5] = 1.0
mano_pose[14] = 1.0
mano_pose[40] = -0.5

hand_state = HandState(left=False)
hand_state.pose[:] = mano_pose
hand_state.recompute_mesh(manobase2miabase)
highlight_mesh_vertices(hand_state.hand_mesh, MANO_CONTACT_SURFACE_VERTICES["thumb"])

emb = HandEmbodiment(hand_state, MIA_CONFIG)

joint_angles, desired_positions = emb.solve(
    return_desired_positions=True,
    use_cached_forward_kinematics=False)

graph = pv.Graph(
    emb.target_kin.tm, MIA_CONFIG["base_frame"], show_frames=False,
    show_connections=False, show_visuals=True, show_collision_objects=False,
    show_name=False, s=0.02)
highlight_graph_visuals(graph, MIA_CONTACT_SURFACE_VERTICES["thumb"])

dists = distances_robot_to_mano(
    hand_state, graph, MIA_CONTACT_SURFACE_VERTICES,
    ["thumb", "index", "middle", "ring", "little"])
print(dists)

mano_vertices, mano_triangles = extract_mano_contact_surface(hand_state, "thumb")
robot_vertices = extract_graph_vertices(graph, MIA_CONTACT_SURFACE_VERTICES, "thumb")

fig = pv.figure()

#fig.add_geometry(hand_state.hand_mesh)
#graph.add_artist(fig)

mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(mano_vertices),
                                 o3d.utility.Vector3iVector(mano_triangles))
mesh.paint_uniform_color((1, 0.5, 0))
fig.add_geometry(mesh)

pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(robot_vertices))
fig.add_geometry(pc)

fig.show()
