import hashlib

import os
import re

import numpy as np
import torch
import trimesh
from manotorch.manolayer import ManoLayer, MANOOutput
from oikit.oi_shape.oi_utils import (
    ALL_CAT,
    ALL_SPLIT,
    ALL_INTENT,
    CENTER_IDX,
    to_list,
    check_valid,
    get_hand_parameter,
    get_obj_path,
    vis_dataset,
)

from tqdm import tqdm


class OakInkShape:
    def __init__(
        self,
        data_split=ALL_SPLIT,
        intent_mode=list(ALL_INTENT),
        category=ALL_CAT,
        data_root="./data/",
        oi_shape_root="./data/oakink_shape_v2",
        mano_assets_root="assets/mano_v1_2",
        meta_root="./data/metaV2",
    ):
        self.name = "OakInkShape"

        self.data_split = to_list(data_split)
        self.categories = to_list(category)
        self.intent_mode = to_list(intent_mode)
        assert (
            check_valid(self.data_split, ALL_SPLIT)
            and check_valid(self.categories, ALL_CAT)
            and check_valid(self.intent_mode, list(ALL_INTENT))
        ), "invalid data split, category, or intent!"

        self.intent_idx = [ALL_INTENT[i] for i in self.intent_mode]
        self.data_root_dir = oi_shape_root

        self.mano_layer = ManoLayer(center_idx=0, mano_assets_root=mano_assets_root)
        # * >>>> filter with regex
        grasp_list = []
        category_begin_idx = []
        seq_cat_matcher = re.compile(r"(.+)/(.{6})_(.{4})_([_0-9]+)/([\-0-9]+)")
        for cat in tqdm(self.categories):
            real_matcher = re.compile(rf"({cat}/(.{{6}})/.{{10}})/hand_param\.pkl$")
            virtual_matcher = re.compile(rf"({cat}/(.{{6}})/.{{10}})/(.{{6}})/hand_param\.pkl$")
            path = os.path.join(self.data_root_dir, cat)
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
                        source = open(os.path.join(self.data_root_dir, re_match[0][0], "source.txt")).read()
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
        for g in tqdm(grasp_list):
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
            for i, g in tqdm(enumerate(grasp_list)):
                if g["subject_alt_id"] is None:
                    continue
                for bidx in category_begin_idx:
                    if bidx <= i:
                        cat_begin_idx = bidx
                    else:
                        break
                for j, alt_g in enumerate(grasp_list[cat_begin_idx:]):
                    if (
                        g["seq_ts"] == alt_g["seq_ts"]
                        and g["obj_id"] == alt_g["obj_id"]
                        and g["pass_stage"] == alt_g["pass_stage"]
                        and g["source"] != alt_g["source"]
                    ):
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
        self.obj_warehouse = {}
        obj_id_set = {g["obj_id"] for g in grasp_list}
        for oid in tqdm(obj_id_set):
            obj_trimesh = trimesh.load(
                get_obj_path(oid, data_root, meta_root), process=False, force="mesh", skip_materials=True
            )
            bbox_center = (obj_trimesh.vertices.min(0) + obj_trimesh.vertices.max(0)) / 2
            obj_trimesh.vertices = obj_trimesh.vertices - bbox_center

            obj_holder = {
                "verts": np.asfarray(obj_trimesh.vertices, dtype=np.float32),  # V, in object canonical space
                "faces": obj_trimesh.faces.astype(np.int32),  # F, paired with V
            }
            self.obj_warehouse[oid] = obj_holder

        self.grasp_list = grasp_list

    def __len__(self):
        return len(self.grasp_list)

    def __getitem__(self, idx):
        grasp = self.grasp_list[idx]
        obj_holder = self.obj_warehouse[grasp["obj_id"]]
        grasp["obj_verts"] = obj_holder["verts"]
        grasp["obj_faces"] = obj_holder["faces"]
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


if __name__ == "__main__":

    # list all grasps
    dataset: OakInkShape = OakInkShape()

    # list the handover intent grasps on the pen in train split
    # dataset: OakInkShape = OakInkShape(category="pen", intent_mode="handover", data_split="train")

    # list the handover && use intent grasps on the pen && mug in train && val split
    # dataset: OakInkShape = OakInkShape(category=["pen", "mug"], intent_mode=["handover", "use"], data_split=["train", "val"])

    print(len(dataset))

    # visualize grasp
    vis_dataset(dataset)
