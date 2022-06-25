import os
import argparse
import random
import cv2
from oikit.oi_image.oi_image import OakInkImage
from oikit.oi_image.viz_tool import draw_wireframe, draw_wireframe_hand, caption_view
from termcolor import cprint


def main(arg):

    oiset = OakInkImage(data_split=arg.data_split, mode_split=arg.mode_split)

    sample_idxs = list(range(len(oiset)))
    random.shuffle(sample_idxs)
    print("Press any key to continue viewing")
    for i in sample_idxs:
        image = oiset.get_image(i)
        joints_2d = oiset.get_joints_2d(i)
        corners_2d = oiset.get_corners_2d(i)
        draw_wireframe_hand(image, joints_2d, None)
        draw_wireframe(image, vert_list=corners_2d)

        image = caption_view(image, caption=f":: test")
        cv2.imshow("x", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.waitKey(0)

    print("EXIT")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="OakInkImage visualization")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    parser.add_argument("--data_split",
                        type=str,
                        default="all",
                        choices=["all", "train", "test", "val"],
                        help="training data split")
    parser.add_argument("--mode_split",
                        type=str,
                        default="default",
                        choices=["default", "object", "subject"],
                        help="training mode split, see paper for more details")
    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)