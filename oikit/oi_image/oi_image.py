import json
import os
import pickle

import imageio
import numpy as np
import trimesh
from oikit.common import quat_to_aa, quat_to_rotmat, rotmat_to_aa
from oikit.common import suppress_trimesh_logging

from .utils import load_object, load_object_by_id, persp_project

ALL_INTENT = {
    "use": "0001",
    "hold": "0002",
    "liftup": "0003",
    "handover": "0004",
}
ALL_INTENT_REV = {_v: _k for _k, _v in ALL_INTENT.items()}


def decode_seq_cat(seq_cat):
    field_list = seq_cat.split("_")
    obj_id = field_list[0]
    action_id = field_list[1]
    if action_id == "0004":
        subject_id = tuple(field_list[2:4])
    else:
        subject_id = (field_list[2],)
    return obj_id, action_id, subject_id


class OakInkImage:

    @staticmethod
    def _get_info_list(data_dir, split_key, data_split):
        if data_split == "train+val":
            info_list = json.load(open(os.path.join(data_dir, "image", "anno", "split", split_key, "seq_train.json")))
        elif data_split == "train":
            info_list = json.load(
                open(os.path.join(data_dir, "image", "anno", "split_train_val", split_key, "example_split_train.json")))
        elif data_split == "val":
            info_list = json.load(
                open(os.path.join(data_dir, "image", "anno", "split_train_val", split_key, "example_split_val.json")))
        else:  # data_split == "test":
            info_list = json.load(open(os.path.join(data_dir, "image", "anno", "split", split_key, "seq_test.json")))
        return info_list

    @staticmethod
    def _get_info_str(info_item):
        info_str = "__".join([str(x) for x in info_item])
        info_str = info_str.replace("/", "__")
        return info_str

    @staticmethod
    def _get_handover_info(info_list):
        hand_over_map = {}
        hand_over_index_list = []
        for idx, info_item in enumerate(info_list):
            info = info_item[0]
            seq_cat, _ = info.split("/")
            _, action_id, _ = decode_seq_cat(seq_cat)
            if action_id != "0004":
                continue
            sub_id = info_item[1]
            alt_sub_id = 1 if sub_id == 0 else 0  # flip sub_id to get alt_sub_id
            alt_info_item = (info_item[0], alt_sub_id, info_item[2], info_item[3])
            hand_over_map[tuple(info_item)] = alt_info_item
            hand_over_index_list.append(idx)
        # sanity check: all alt_info_item should be in hand_over_map
        for alt_info_item in hand_over_map.values():
            assert alt_info_item in hand_over_map, str(alt_info_item)
        # TODO: extra filter, like to limit for subject_id 0/1
        return hand_over_map, hand_over_index_list

    def __init__(self, data_split="all", mode_split="default", enable_handover=False) -> None:
        self._name = "OakInkImage"
        self._data_split = data_split
        self._mode_split = mode_split
        assert "OAKINK_DIR" in os.environ, "environment variable 'OAKINK_DIR' is not set"
        self._enable_handover = enable_handover
        if self._enable_handover:
            assert self._data_split == "all", "handover need to be enabled in all split"

        self._data_dir = os.environ["OAKINK_DIR"]
        if self._data_split == "all":
            self.info_list = json.load(open(os.path.join(self._data_dir, "image", "anno", "seq_all.json")))
        elif self._mode_split == "default":
            self.info_list = self._get_info_list(self._data_dir, "split0", self._data_split)
        elif self._mode_split == "subject":
            self.info_list = self._get_info_list(self._data_dir, "split1", self._data_split)
        elif self._mode_split == "object":
            self.info_list = self._get_info_list(self._data_dir, "split2", self._data_split)
        else:  # self._mode_split == "handobject":
            self.info_list = self._get_info_list(self._data_dir, "split0_ho", self._data_split)

        self.info_str_list = []
        for info in self.info_list:
            info_str = "__".join([str(x) for x in info])
            info_str = info_str.replace("/", "__")
            self.info_str_list.append(info_str)

        # load obj
        suppress_trimesh_logging()

        self.obj_mapping = {}
        obj_root = os.path.join(self._data_dir, "image", "obj")
        all_obj_fn = sorted(os.listdir(obj_root))
        for obj_fn in all_obj_fn:
            obj_id = os.path.splitext(obj_fn)[0]
            obj_model = load_object(obj_root, obj_fn)
            self.obj_mapping[obj_id] = obj_model

        self.framedata_color_name = [
            "north_east_color",
            "south_east_color",
            "north_west_color",
            "south_west_color",
        ]

        self._image_size = (848, 480)  # (W, H)
        self._hand_side = "right"

        # seq status
        with open(os.path.join(self._data_dir, "image", "anno", "seq_status.json"), "r") as f:
            self.seq_status = json.load(f)

        # handover
        if self._enable_handover:
            self.handover_info, self.handover_sample_index_list = self._get_handover_info(self.info_list)
            self.handover_info_list = list(self.handover_info.keys())
        else:
            self.handover_info, self.handover_sample_index_list = None, None
            self.handover_info_list = None

    def __len__(self):
        return len(self.info_list)

    def get_image_path(self, idx):
        info = self.info_list[idx]
        # compute image path
        offset = os.path.join(info[0], f"{self.framedata_color_name[info[3]]}_{info[2]}.png")
        image_path = os.path.join(self._data_dir, "image", "stream_release_v2", offset)
        return image_path

    def get_image(self, idx):
        path = self.get_image_path(idx)
        image = np.array(imageio.imread(path, pilmode="RGB"), dtype=np.uint8)
        return image

    def get_cam_intr(self, idx):
        cam_path = os.path.join(self._data_dir, "image", "anno", "cam_intr", f"{self.info_str_list[idx]}.pkl")
        with open(cam_path, "rb") as f:
            cam_intr = pickle.load(f)
        return cam_intr

    def get_joints_3d(self, idx):
        joints_path = os.path.join(self._data_dir, "image", "anno", "hand_j", f"{self.info_str_list[idx]}.pkl")
        with open(joints_path, "rb") as f:
            joints_3d = pickle.load(f)
        return joints_3d

    def get_verts_3d(self, idx):
        verts_path = os.path.join(self._data_dir, "image", "anno", "hand_v", f"{self.info_str_list[idx]}.pkl")
        with open(verts_path, "rb") as f:
            verts_3d = pickle.load(f)
        return verts_3d

    def get_joints_2d(self, idx):
        cam_intr = self.get_cam_intr(idx)
        joints_3d = self.get_joints_3d(idx)
        return persp_project(joints_3d, cam_intr)

    def get_verts_2d(self, idx):
        cam_intr = self.get_cam_intr(idx)
        verts_3d = self.get_verts_3d(idx)
        return persp_project(verts_3d, cam_intr)

    def get_mano_pose(self, idx):
        general_info_path = os.path.join(self._data_dir, "image", "anno", "general_info",
                                         f"{self.info_str_list[idx]}.pkl")
        with open(general_info_path, "rb") as f:
            general_info = pickle.load(f)
        raw_hand_anno = general_info["hand_anno"]

        raw_hand_pose = (raw_hand_anno["hand_pose"]).reshape((16, 4))  # quat (16, 4)
        _wrist, _remain = raw_hand_pose[0, :], raw_hand_pose[1:, :]
        cam_extr = general_info["cam_extr"]  # SE3 (4, 4))
        extr_R = cam_extr[:3, :3]  # (3, 3)

        wrist_R = extr_R.matmul(quat_to_rotmat(_wrist))  # (3, 3)
        wrist = rotmat_to_aa(wrist_R).unsqueeze(0).numpy()  # (1, 3)
        remain = quat_to_aa(_remain).numpy()  # (15, 3)
        hand_pose = np.concatenate([wrist, remain], axis=0)  # (16, 3)

        return hand_pose.astype(np.float32)

    def get_mano_shape(self, idx):
        general_info_path = os.path.join(self._data_dir, "image", "anno", "general_info",
                                         f"{self.info_str_list[idx]}.pkl")
        with open(general_info_path, "rb") as f:
            general_info = pickle.load(f)
        raw_hand_anno = general_info["hand_anno"]
        hand_shape = raw_hand_anno["hand_shape"].numpy().astype(np.float32)
        return hand_shape

    def get_obj_idx(self, idx):
        info = self.info_list[idx][0]
        seq_cat, _ = info.split("/")
        obj_id, _, _ = decode_seq_cat(seq_cat)
        return obj_id

    def get_obj_faces(self, idx):
        obj_id = self.get_obj_idx(idx)
        return np.asarray(self.obj_mapping[obj_id].faces).astype(np.int32)

    def get_obj_transf(self, idx):
        obj_transf_path = os.path.join(self._data_dir, "image", "anno", "obj_transf", f"{self.info_str_list[idx]}.pkl")
        with open(obj_transf_path, "rb") as f:
            obj_transf = pickle.load(f)
        return obj_transf.astype(np.float32)

    def get_obj_verts_3d(self, idx):
        obj_verts = self.get_obj_verts_can(idx)
        obj_transf = self.get_obj_transf(idx)
        obj_rot = obj_transf[:3, :3]
        obj_tsl = obj_transf[:3, 3]
        obj_verts_transf = (obj_rot @ obj_verts.transpose(1, 0)).transpose(1, 0) + obj_tsl
        return obj_verts_transf

    def get_obj_verts_2d(self, idx):
        obj_verts_3d = self.get_obj_verts_3d(idx)
        cam_intr = self.get_cam_intr(idx)
        return persp_project(obj_verts_3d, cam_intr)

    def get_obj_verts_can(self, idx):
        obj_id = self.get_obj_idx(idx)
        obj_verts = np.asarray(self.obj_mapping[obj_id].vertices).astype(np.float32)
        return obj_verts

    def get_corners_3d(self, idx):
        obj_corners = self.get_corners_can(idx)
        obj_transf = self.get_obj_transf(idx)
        obj_rot = obj_transf[:3, :3]
        obj_tsl = obj_transf[:3, 3]
        obj_corners_transf = (obj_rot @ obj_corners.transpose(1, 0)).transpose(1, 0) + obj_tsl
        return obj_corners_transf

    def get_corners_2d(self, idx):
        obj_corners = self.get_corners_3d(idx)
        cam_intr = self.get_cam_intr(idx)
        return persp_project(obj_corners, cam_intr)

    def get_corners_can(self, idx):
        obj_id = self.get_obj_idx(idx)
        obj_mesh = self.obj_mapping[obj_id]
        obj_corners = trimesh.bounds.corners(obj_mesh.bounds)
        return obj_corners

    def get_sample_status(self, idx):
        info = self.info_list[idx][0]
        status = self.seq_status[info]
        return status

    def get_intent_mode(self, idx):
        info_item = self.info_list[idx]
        info = info_item[0]
        seq_cat, _ = info.split("/")
        _, action_id, _ = decode_seq_cat(seq_cat)
        intent_mode = ALL_INTENT_REV[action_id]
        return intent_mode

    def get_hand_over(self, idx):
        if self.handover_info is None:
            return None
        info_item = tuple(self.info_list[idx])
        if info_item not in self.handover_info:
            return None

        info = info_item[0]
        status = self.seq_status[info]
        seq_cat, _ = info.split("/")
        _, action_id, _ = decode_seq_cat(seq_cat)
        intent_mode = ALL_INTENT_REV[action_id]

        alt_info_item = self.handover_info[info_item]
        # load by alt_info
        alt_res = self.load_by_info(alt_info_item)
        # rename to alt
        res = {
            "sample_status": status,
            "intent_mode": intent_mode,
        }
        for _k, _v in alt_res.items():
            res[f"alt_{_k}"] = _v
        return res

    def load_by_info(self, info_item):
        info = info_item[0]
        status = self.seq_status[info]
        seq_cat, _ = info.split("/")
        _, action_id, _ = decode_seq_cat(seq_cat)
        intent_mode = ALL_INTENT_REV[action_id]

        info_str = self._get_info_str(info_item)
        joints_path = os.path.join(self._data_dir, "image", "anno", "hand_j", f"{info_str}.pkl")
        with open(joints_path, "rb") as f:
            joints_3d = pickle.load(f)
        verts_path = os.path.join(self._data_dir, "image", "anno", "hand_v", f"{info_str}.pkl")
        with open(verts_path, "rb") as f:
            verts_3d = pickle.load(f)
        return {
            "sample_status": status,
            "intent_mode": intent_mode,
            "joints": joints_3d,
            "verts": verts_3d,
        }


class OakInkImageSequence(OakInkImage):

    def __init__(self, seq_id, view_id, enable_handover=False) -> None:

        self.framedata_color_name = [
            "north_east_color",
            "south_east_color",
            "north_west_color",
            "south_west_color",
        ]
        view_name = self.framedata_color_name[view_id]
        self._name = f"OakInkImage_{seq_id}_{view_name}"

        assert "OAKINK_DIR" in os.environ, "environment variable 'OAKINK_DIR' is not set"
        self._data_dir = os.environ["OAKINK_DIR"]
        info_list_all = json.load(open(os.path.join(self._data_dir, "image", "anno", "seq_all.json")))

        seq_cat, seq_timestamp = seq_id.split("/")
        self.info_list = [info for info in info_list_all if (info[0] == seq_id and info[3] == view_id)]

        # deal with two hand cases.
        self.info_list.sort(key=lambda x: x[1] * 1000 + x[2])

        self.info_str_list = []
        for info in self.info_list:
            info_str = "__".join([str(x) for x in info])
            info_str = info_str.replace("/", "__")
            self.info_str_list.append(info_str)

        self.obj_id, self.intent_id, self.subject_id = decode_seq_cat(seq_cat)
        # load obj
        self.obj_mapping = {}
        suppress_trimesh_logging()
        obj_root = os.path.join(self._data_dir, "image", "obj")
        self.obj_model = load_object_by_id(self.obj_id, obj_root)
        self.obj_mapping[self.obj_id] = self.obj_model

        self._image_size = (848, 480)  # (W, H)
        self._hand_side = "right"

        self._enable_handover = enable_handover
        # seq status
        with open(os.path.join(self._data_dir, "image", "anno", "seq_status.json"), "r") as f:
            self.seq_status = json.load(f)

        # handover
        if self._enable_handover:
            self.handover_info, self.handover_sample_index_list = self._get_handover_info(self.info_list)
            self.handover_info_list = list(self.handover_info.keys())
        else:
            self.handover_info, self.handover_sample_index_list = None, None
            self.handover_info_list = None
