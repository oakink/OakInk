import hashlib
import os
import re
import json
import numpy as np
import torch
import trimesh
import pickle
from manotorch.manolayer import ManoLayer, MANOOutput
from oikit import __version__ as oikit_version
from oikit.common import suppress_trimesh_logging
from oikit.oi_shape.utils import (
    ALL_CAT,
    ALL_INTENT,
    ALL_SPLIT,
    CENTER_IDX,
    check_valid,
    get_hand_parameter,
    get_obj_path,
    to_list,
)
from tqdm import tqdm


class OakInkShape:

    def __init__(self,
                 data_split=ALL_SPLIT,
                 intent_mode=list(ALL_INTENT),
                 category=ALL_CAT,
                 mano_assets_root="assets/mano_v1_2",
                 use_cache=True,
                 use_downsample_mesh=False):
        self.name = "OakInkShape"

        assert 'OAKINK_DIR' in os.environ, "environment variable 'OAKINK_DIR' is not set"
        data_dir = os.path.join(os.environ['OAKINK_DIR'], "shape")
        oi_shape_dir = os.path.join(data_dir, "oakink_shape_v2")
        meta_dir = os.path.join(data_dir, "metaV2")

        if data_split == 'all':
            data_split = ALL_SPLIT
        if category == 'all':
            category = ALL_CAT
        if intent_mode == 'all':
            intent_mode = list(ALL_INTENT)

        self.data_split = to_list(data_split)
        self.categories = to_list(category)
        self.intent_mode = to_list(intent_mode)
        assert (check_valid(self.data_split, ALL_SPLIT) and check_valid(self.categories, ALL_CAT) and
                check_valid(self.intent_mode, list(ALL_INTENT))), "invalid data split, category, or intent!"

        self.intent_idx = [ALL_INTENT[i] for i in self.intent_mode]

        self.mano_layer = ManoLayer(center_idx=0, mano_assets_root=mano_assets_root)

        if use_cache is True:
            cache_identifier_dict = {
                "version": oikit_version,
                "data_split": self.data_split,
                "categories": self.categories,
                "intent_mode": self.intent_mode
            }
            cache_identifier_raw = json.dumps(cache_identifier_dict, sort_keys=True)
            cache_identifier = hashlib.md5(cache_identifier_raw.encode("ascii")).hexdigest()
            cache_path = os.path.join(os.path.expanduser('~'), ".cache", self.name, oikit_version,
                                      f"{cache_identifier}.pkl")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            if os.path.exists(cache_path):
                print(f"{self.name} loading cache from {cache_path}")
                with open(cache_path, "rb") as p_f:
                    cache = pickle.load(p_f)
                self.grasp_list = cache["grasp_list"]
                self.obj_warehouse = cache["obj_warehouse"]
                self.data_dir = data_dir
                self.meta_dir = meta_dir
                return

        # * >>>> filter with regex
        grasp_list = []
        category_begin_idx = []
        seq_cat_matcher = re.compile(r"(.+)/(.{6})_(.{4})_([_0-9]+)/([\-0-9]+)")
        for cat in tqdm(self.categories, desc="Process categories"):
            real_matcher = re.compile(rf"({cat}/(.{{6}})/.{{10}})/hand_param\.pkl$")
            virtual_matcher = re.compile(rf"({cat}/(.{{6}})/.{{10}})/(.{{6}})/hand_param\.pkl$")
            path = os.path.join(oi_shape_dir, cat)
            category_begin_idx.append(len(grasp_list))
            for cur, dirs, files in os.walk(path, followlinks=False):
                dirs.sort()
                for f in files:
                    re_match = virtual_matcher.findall(os.path.join(cur, f))
                    is_virtual = len(re_match) > 0
                    re_match = re_match + real_matcher.findall(os.path.join(cur, f))
                    if len(re_match) > 0:
                        # ? regex should return : [(path, raw_oid, tag, [oid])]
                        assert len(re_match) == 1, "regex should return only one match"
                        source = open(os.path.join(oi_shape_dir, re_match[0][0], "source.txt")).read()
                        grasp_cat_match = seq_cat_matcher.findall(source)[0]
                        pass_stage, raw_obj_id, action_id, subject_id, seq_ts = (
                            grasp_cat_match[0],
                            grasp_cat_match[1],
                            grasp_cat_match[2],
                            grasp_cat_match[3],
                            grasp_cat_match[4],
                        )
                        obj_id = re_match[0][2] if is_virtual else re_match[0][1]
                        assert (is_virtual and raw_obj_id == re_match[0][1]) or obj_id == raw_obj_id
                        # * filter with intent mode
                        if action_id not in self.intent_idx:
                            continue
                        # * filter with data split
                        obj_id_hash = int(hashlib.md5(obj_id.encode("utf-8")).hexdigest(), 16)  # random select
                        if obj_id_hash % 10 < 8 and "train" not in self.data_split:
                            continue
                        elif obj_id_hash % 10 == 8 and "val" not in self.data_split:
                            continue
                        elif obj_id_hash % 10 == 9 and "test" not in self.data_split:
                            continue

                        if action_id == "0004":  # hand over
                            subject_alt_id = subject_id.split("_")[1]
                            subject_id = subject_id.split("_")[0]
                            if "_alt" in source:
                                subject_id, subject_alt_id = subject_alt_id, subject_id
                        else:
                            subject_alt_id = None

                        hand_pose, hand_shape, hand_tsl = get_hand_parameter(os.path.join(cur, f))
                        grasp_item = {
                            "cate_id": cat,
                            "seq_id": "_".join(grasp_cat_match[1:]),
                            "obj_id": obj_id,
                            "joints": None,
                            "verts": None,
                            "hand_pose": hand_pose,
                            "hand_shape": hand_shape,
                            "hand_tsl": hand_tsl,
                            "is_virtual": is_virtual,
                            "raw_obj_id": raw_obj_id,
                            "action_id": action_id,
                            "subject_id": subject_id,
                            "subject_alt_id": subject_alt_id,
                            "seq_ts": seq_ts,
                            "source": source,
                            "pass_stage": pass_stage,
                            "alt_grasp_item": None,
                        }
                        grasp_list.append(grasp_item)
            # * <<<<

        # * >>>> cal hand joints
        batch_hand_pose = []
        batch_hand_shape = []
        batch_hand_tsl = []
        for _, g in enumerate(grasp_list):
            batch_hand_pose.append(g["hand_pose"])
            batch_hand_shape.append(g["hand_shape"])
            batch_hand_tsl.append(g["hand_tsl"])
        batch_hand_shape = torch.from_numpy(np.stack(batch_hand_shape))
        batch_hand_pose = torch.from_numpy(np.stack(batch_hand_pose))
        batch_hand_tsl = np.stack(batch_hand_tsl)
        mano_output: MANOOutput = self.mano_layer(batch_hand_pose, batch_hand_shape)
        batch_hand_joints = mano_output.joints.numpy() + batch_hand_tsl[:, None, :]
        batch_hand_verts = mano_output.verts.numpy() + batch_hand_tsl[:, None, :]
        batch_hand_tsl = batch_hand_joints[:, CENTER_IDX]  # center idx from 0 to 9
        for i in range(len(grasp_list)):
            grasp_list[i]["joints"] = batch_hand_joints[i]
            grasp_list[i]["verts"] = batch_hand_verts[i]
            grasp_list[i]["hand_tsl"] = batch_hand_tsl[i]
        # * <<<<

        # * >>>> handle handover
        if "handover" in self.intent_mode:
            for i, g in tqdm(enumerate(grasp_list), total=len(grasp_list), desc="Process handover grasp"):
                if g["subject_alt_id"] is None:
                    continue
                for bidx in category_begin_idx:
                    if bidx <= i:
                        cat_begin_idx = bidx
                    else:
                        break
                for j, alt_g in enumerate(grasp_list[cat_begin_idx:]):
                    if (g["seq_ts"] == alt_g["seq_ts"] and g["obj_id"] == alt_g["obj_id"] and
                            g["pass_stage"] == alt_g["pass_stage"] and g["source"] != alt_g["source"]):
                        assert g["subject_id"] == alt_g["subject_alt_id"] and g["subject_alt_id"] == alt_g["subject_id"]
                        g["alt_grasp_item"] = {
                            "alt_joints": alt_g["joints"],
                            "alt_verts": alt_g["verts"],
                            "alt_hand_pose": alt_g["hand_pose"],
                            "alt_hand_shape": alt_g["hand_shape"],
                            "alt_hand_tsl": alt_g["hand_tsl"],
                        }
                        break
            grasp_list = list(filter(lambda x: x["action_id"] != "0004" or x["alt_grasp_item"] is not None, grasp_list))
        # * <<<<

        # * >>>> create obj warehouse
        suppress_trimesh_logging()
        self.obj_warehouse = {}
        obj_id_set = {g["obj_id"] for g in grasp_list}
        for oid in tqdm(obj_id_set, desc="Load obj model"):
            obj_path = get_obj_path(oid, data_dir, meta_dir, use_downsample=use_downsample_mesh)
            obj_trimesh = trimesh.load(obj_path, process=False, force="mesh", skip_materials=True)
            bbox_center = (obj_trimesh.vertices.min(0) + obj_trimesh.vertices.max(0)) / 2
            obj_trimesh.vertices = obj_trimesh.vertices - bbox_center
            self.obj_warehouse[oid] = obj_trimesh

        self.grasp_list = grasp_list
        self.data_dir = data_dir
        self.meta_dir = meta_dir

        if use_cache is True:
            cache = {"grasp_list": self.grasp_list, "obj_warehouse": self.obj_warehouse}
            with open(cache_path, "wb") as f:
                pickle.dump(cache, f)
            print(f"{self.name} cache saved to {cache_path}")

    def __len__(self):
        return len(self.grasp_list)

    def __getitem__(self, idx):
        grasp = self.grasp_list[idx]
        obj_mesh = self.obj_warehouse[grasp["obj_id"]]
        grasp["obj_verts"] = obj_mesh.vertices.astype(np.float32)
        grasp["obj_faces"] = obj_mesh.faces.astype(np.int32)
        if grasp["action_id"] == "0004":
            joints, verts, pose, shape, tsl = self.get_hand_over(idx)
            grasp["alt_joints"] = joints
            grasp["alt_verts"] = verts
            grasp["alt_hand_pose"] = pose
            grasp["alt_hand_shape"] = shape
            grasp["alt_hand_tsl"] = tsl
        return grasp

    def get_hand_over(self, idx):
        alt_grasp_item = self.grasp_list[idx]["alt_grasp_item"]
        return (
            alt_grasp_item["alt_joints"],
            alt_grasp_item["alt_verts"],
            alt_grasp_item["alt_hand_pose"],
            alt_grasp_item["alt_hand_shape"],
            alt_grasp_item["alt_hand_tsl"],
        )
