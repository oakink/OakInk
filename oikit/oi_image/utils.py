import json
import logging
import os
import pickle

import imageio
import numpy as np
import trimesh


def persp_project(points3d, cam_intr):
    hom_2d = np.array(cam_intr).dot(points3d.transpose()).transpose()
    points2d = (hom_2d / (hom_2d[:, 2:] + 1e-6))[:, :2]
    return points2d.astype(np.float32)


def load_object_by_id(obj_id, obj_root):
    # load object mesh
    try:
        mesh_file = os.path.join(obj_root, f"{obj_id}.obj")
        if not os.path.exists(mesh_file):
            mesh_file = os.path.join(obj_root, f"{obj_id}.ply")
        if not os.path.exists(mesh_file):
            raise FileNotFoundError(f"Cannot found valid object mesh [ .obj | .ply] at {obj_root} for {obj_id}")
        obj = trimesh.load(mesh_file, process=False, skip_materials=True, force="mesh")
        bbox_center = (obj.vertices.min(0) + obj.vertices.max(0)) / 2
        obj.vertices = obj.vertices - bbox_center
    except Exception as e:
        raise RuntimeError(f"failed to load object {obj_id}! {e}")
    return obj


def load_object(obj_root, filename):
    # load object mesh
    try:
        mesh_file = os.path.join(obj_root, filename)
        if not os.path.exists(mesh_file):
            raise FileNotFoundError(f"Cannot found valid object mesh file at {obj_root} for {filename}")
        obj = trimesh.load(mesh_file, process=False, skip_materials=True, force="mesh")
        bbox_center = (obj.vertices.min(0) + obj.vertices.max(0)) / 2
        obj.vertices = obj.vertices - bbox_center
    except Exception as e:
        raise RuntimeError(f"failed to load object {filename}! {e}")
    return obj


