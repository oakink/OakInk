import pickle
import os
import json
import glob
import numpy as np
import logging

ALL_CAT = [
    "apple",
    "banana",
    "binoculars",
    "bottle",
    "bowl",
    "cameras",
    "can",
    "cup",
    "cylinder_bottle",
    "donut",
    "eyeglasses",
    "flashlight",
    "fryingpan",
    "gamecontroller",
    "hammer",
    "headphones",
    "knife",
    "lightbulb",
    "lotion_pump",
    "mouse",
    "mug",
    "pen",
    "phone",
    "pincer",
    "power_drill",
    "scissors",
    "screwdriver",
    "squeezable",
    "stapler",
    "teapot",
    "toothbrush",
    "trigger_sprayer",
    "wineglass",
    "wrench",
]

ALL_SPLIT = [
    "train",
    "val",
    "test",
]

ALL_INTENT = {
    "use": "0001",
    "hold": "0002",
    "liftup": "0003",
    "handover": "0004",
}

CENTER_IDX = 9


def to_list(x):
    if isinstance(x, list):
        return x
    return [x]


def check_valid(list, valid_list):
    for x in list:
        if x not in valid_list:
            return False
    return True


def get_hand_parameter(path):
    pose = pickle.load(open(path, "rb"))
    return pose["pose"], pose["shape"], pose["tsl"]


def get_obj_path(oid, data_path, meta_path, use_downsample=True, key="align"):
    obj_suffix_path = "align_ds" if use_downsample else "align"
    real_meta = json.load(open(os.path.join(meta_path, "object_id.json"), "r"))
    virtual_meta = json.load(open(os.path.join(meta_path, "virtual_object_id.json"), "r"))
    if oid in real_meta:
        obj_name = real_meta[oid]["name"]
        obj_path = os.path.join(data_path, "OakInkObjectsV2")
    else:
        obj_name = virtual_meta[oid]["name"]
        obj_path = os.path.join(data_path, "OakInkVirtualObjectsV2")
    obj_mesh_path = list(
        glob.glob(os.path.join(obj_path, obj_name, obj_suffix_path, "*.obj")) +
        glob.glob(os.path.join(obj_path, obj_name, obj_suffix_path, "*.ply")))
    if len(obj_mesh_path) > 1:
        obj_mesh_path = [p for p in obj_mesh_path if key in os.path.split(p)[1]]
    assert len(obj_mesh_path) == 1
    return obj_mesh_path[0]


def viz_dataset(dataset):

    import open3d as o3d

    curr_idx_in_vis_list = 0
    hand_faces = np.array(dataset.mano_layer.th_faces)

    grasp = dataset[curr_idx_in_vis_list]

    hand_verts_obj = grasp["verts"]

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(
        window_name="Runtime HAND + OBJ",
        width=1024,
        height=1024,
    )

    hand_mesh = o3d.geometry.TriangleMesh()
    hand_mesh.triangles = o3d.utility.Vector3iVector(hand_faces)
    hand_mesh.vertices = o3d.utility.Vector3dVector(hand_verts_obj)
    hand_mesh.vertex_colors = o3d.utility.Vector3dVector(
        np.array([[0.4, 0.81960784, 0.95294118]] * len(np.asarray(hand_verts_obj))))
    hand_mesh.compute_vertex_normals()
    hand_mesh.compute_triangle_normals()
    vis.add_geometry(hand_mesh)

    hand_mesh_alt = o3d.geometry.TriangleMesh()
    hand_mesh_alt.triangles = o3d.utility.Vector3iVector(hand_faces)
    if grasp["action_id"] == "0004":
        hand_verts_obj_alt = grasp["alt_verts"]
        hand_mesh_alt.vertices = o3d.utility.Vector3dVector(hand_verts_obj_alt)
    else:
        hand_mesh_alt.vertices = o3d.utility.Vector3dVector(np.zeros_like(hand_verts_obj))
    hand_mesh_alt.vertex_colors = o3d.utility.Vector3dVector(
        np.array([[0.4, 0.42353, 0.95294118]] * len(hand_verts_obj)))
    hand_mesh_alt.compute_vertex_normals()
    hand_mesh_alt.compute_triangle_normals()
    vis.add_geometry(hand_mesh_alt)

    obj_verts_obj = grasp["obj_verts"]
    obj_faces = grasp["obj_faces"]

    obj_mesh = o3d.geometry.TriangleMesh()
    obj_mesh.triangles = o3d.utility.Vector3iVector(obj_faces)
    obj_mesh.vertices = o3d.utility.Vector3dVector(obj_verts_obj)
    obj_mesh.vertex_colors = o3d.utility.Vector3dVector(np.array([[1.0, 1.0, 0.0]] * len(np.asarray(obj_verts_obj))))
    obj_mesh.compute_vertex_normals()
    obj_mesh.compute_triangle_normals()
    vis.add_geometry(obj_mesh)

    def update_vis(vis):
        nonlocal curr_idx_in_vis_list
        try:
            print(curr_idx_in_vis_list)
            grasp = dataset[curr_idx_in_vis_list]
        except:
            raise Exception("finish!")

        hand_verts_obj = grasp["verts"]

        hand_mesh.vertices = o3d.utility.Vector3dVector(hand_verts_obj)
        hand_mesh.compute_vertex_normals()
        hand_mesh.compute_triangle_normals()

        obj_verts_obj = grasp["obj_verts"]
        obj_faces = grasp["obj_faces"]

        obj_mesh.triangles = o3d.utility.Vector3iVector(obj_faces)
        obj_mesh.vertices = o3d.utility.Vector3dVector(obj_verts_obj)
        obj_mesh.vertex_colors = o3d.utility.Vector3dVector(np.array([[1.0, 1.0, 0.0]] *
                                                                     len(np.asarray(obj_verts_obj))))
        obj_mesh.compute_vertex_normals()
        obj_mesh.compute_triangle_normals()

        if grasp["action_id"] == "0004":
            hand_verts_obj_alt = grasp["alt_verts"]
            hand_mesh_alt.vertices = o3d.utility.Vector3dVector(hand_verts_obj_alt)
        else:
            hand_mesh_alt.vertices = o3d.utility.Vector3dVector(np.zeros_like(hand_verts_obj))
        hand_mesh_alt.compute_vertex_normals()
        hand_mesh_alt.compute_triangle_normals()

    # region ##### view next sample >>>>>
    class next_sample:

        def __call__(self, vis, action, mods):
            nonlocal curr_idx_in_vis_list

            if action != 0:  # only when key up
                return False

            curr_idx_in_vis_list += 1
            update_vis(vis)
            return True

    class before_sample:

        def __call__(self, vis, action, mods):
            nonlocal curr_idx_in_vis_list

            if action != 0:  # only when key up
                return False

            curr_idx_in_vis_list -= 1
            update_vis(vis)
            return True

    class quit:

        def __call__(self, vis, action, mods):
            if action != 0:
                return False

            raise Exception("quit!")

    # endregion

    vis.register_key_action_callback(ord("N"), next_sample())
    vis.register_key_action_callback(ord("M"), before_sample())
    vis.register_key_action_callback(ord("Q"), quit())

    rotating = False

    def key_action_callback(vis, action, mods):
        nonlocal rotating
        if action == 1:  # key down
            rotating = True
        elif action == 0:  # key up
            rotating = False
        elif action == 2:  # key repeat
            pass
        return True

    def animation_callback(vis):
        nonlocal rotating
        if rotating:
            ctr = vis.get_view_control()
            ctr.rotate(5.0, 0.0)

    vis.register_animation_callback(animation_callback)
    vis.register_key_action_callback(ord("A"), key_action_callback)
    try:
        vis.run()
    except Exception as e:
        print(e)
