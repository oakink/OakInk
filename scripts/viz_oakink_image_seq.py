import argparse
import json
import os

import cv2
import numpy as np
from oikit.oi_image.oi_image import OakInkImageSequence
from oikit.oi_image.viz_tool import caption_view, draw_wireframe, draw_wireframe_hand
from oikit.oi_image.utils import persp_project
from termcolor import cprint


def viz_a_seq(oi_seq: OakInkImageSequence):
    for i in range(len(oi_seq)):
        image = oi_seq.get_image(i)
        joints_2d = oi_seq.get_joints_2d(i)
        corners_2d = oi_seq.get_corners_2d(i)
        cam_intr = oi_seq.get_cam_intr(i)

        draw_wireframe_hand(image, joints_2d, hand_joint_mask=None)
        draw_wireframe(image, vert_list=corners_2d)

        hand_over_info = oi_seq.get_hand_over(i)
        if hand_over_info is not None:
            alt_joints_3d = hand_over_info["alt_joints"]
            alt_joints_2d = persp_project(alt_joints_3d, cam_intr)
            draw_wireframe_hand(image, alt_joints_2d, hand_joint_mask=None)

        image = caption_view(image, caption=f"::{oi_seq._name}")
        cv2.imshow("temp/x.png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.waitKey(0)
    return


def main(arg):
    info_list_all = json.load(open(os.path.join(arg.data_dir, "image", "anno", "seq_all.json")))
    seq_id_list = list(set([info[0] for info in info_list_all]))

    if arg.viz_all_seq:
        for seq_id in seq_id_list:
            view_id = np.random.randint(4)
            oi_seq = OakInkImageSequence(seq_id=seq_id, view_id=view_id, enable_handover=True)
            cprint(f"viz_all: {oi_seq._name}", "yellow")
            viz_a_seq(oi_seq)
    else:
        # viz one seq
        oi_seq = OakInkImageSequence(seq_id=arg.seq_id, view_id=arg.view_id, enable_handover=True)
        cprint(f"viz_one: {oi_seq._name}", "yellow")
        viz_a_seq(oi_seq)

    print("EXIT")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="OakInkImage sequence-level visualization")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    parser.add_argument("--viz_all_seq", action="store_true", help="visualize all sequences")
    parser.add_argument("--seq_id",
                        type=str,
                        default="A01001_0003_0001/2021-09-26-20-01-24",
                        help="sequence id, see OAKINK_DIR/image/anno/seq_status.json")
    parser.add_argument("--view_id", type=int, default=0, choices=[0, 1, 2, 3], help="view id (camera id), int: 0-3")
    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)
