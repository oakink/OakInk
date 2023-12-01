import os
import argparse
import random
import cv2
from oikit.oi_image import OakInkImage
from oikit.oi_image.viz_tool import draw_wireframe, draw_wireframe_hand, caption_view
from termcolor import cprint

def main(arg):
    oiset = OakInkImage(data_split=arg.data_split, mode_split=arg.mode_split, enable_handover=True)
    print(oiset.get_intent_mode(0))
    print(oiset.handover_sample_index_list[0])
    print(oiset.get_intent_mode(1896))
    _handover = oiset.get_hand_over(1896)
    print(list(_handover.keys()))

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
