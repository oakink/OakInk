import os
import argparse
import random
import cv2
import numpy as np
from oikit.oi_image.oi_image_mv import OakInkImageMV
from oikit.oi_image.viz_tool import draw_wireframe, draw_wireframe_hand, caption_view
from termcolor import cprint
from tqdm import tqdm
import pickle


def extract_cam_extr(oiset, idx):
    general_info_path = os.path.join(oiset._data_dir, "image", "anno", "general_info", f"{oiset.info_str_list[idx]}.pkl")
    with open(general_info_path, "rb") as f:
        general_info = pickle.load(f)
    cam_extr = general_info["cam_extr"].numpy().astype(np.float32)
    return cam_extr


def main(arg):

    oiset = OakInkImageMV(data_split=arg.data_split, mode_split=arg.mode_split)
    save_prefix = os.path.join("./data/image/anno_packed_mv", arg.mode_split, arg.data_split)
    os.makedirs(save_prefix, exist_ok=True)

    print("Got # of samples:", len(oiset))
    sample_idxs = list(range(len(oiset)))
    for i in tqdm(sample_idxs):
        # cam_intr, hand_j, hand_v, mano_pose, mano_shape, obj_transf, sample_status
        info_str = oiset.info_str_list[i]
        cam_intr = oiset.get_cam_intr(i)
        hand_j = oiset.get_joints_3d(i)
        hand_v = oiset.get_verts_3d(i)
        mano_pose = oiset.get_mano_pose(i)
        mano_shape = oiset.get_mano_shape(i)
        obj_transf = oiset.get_obj_transf(i)
        sample_status = oiset.get_sample_status(i)
        cam_extr = extract_cam_extr(oiset, i)
        packed = {
            "cam_extr": cam_extr,
            "cam_intr": cam_intr,
            "hand_j": hand_j,
            "hand_v": hand_v,
            "mano_pose": mano_pose,
            "mano_shape": mano_shape,
            "obj_transf": obj_transf,
            "sample_status": sample_status,
        }
        save_file = f"{info_str}.pkl"
        save_filepath = os.path.join(save_prefix, save_file)
        with open(save_filepath, "wb") as f:
            pickle.dump(packed, f)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="OakInkImage visualization")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    parser.add_argument(
        "--data_split",
        type=str,
        default="all",
        choices=["all", "train+val", "test", "train", "val"],
        help="training data split",
    )
    parser.add_argument(
        "--mode_split",
        type=str,
        default="default",
        choices=["default", "object", "subject", "handobject"],
        help="training mode split, see paper for more details",
    )
    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)
