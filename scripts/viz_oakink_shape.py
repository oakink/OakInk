import argparse
import os
import numpy as np
from oikit.oi_shape import OakInkShape
from oikit.oi_shape.utils import viz_dataset
from termcolor import cprint


def main(arg):
    oi_shape = OakInkShape(category=arg.categories, intent_mode=arg.intent_mode, data_split=arg.data_split)
    viz_dataset(oi_shape)

    print("EXIT")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="OakInkImage sequence-level visualization")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    parser.add_argument("--categories", type=str, default="teapot", help="list of object categories")
    parser.add_argument("--intent_mode", type=str, default="use", help="intent mode, list of intents")
    parser.add_argument("--data_split",
                        type=str,
                        default="train",
                        choices=["train", "test", "val"],
                        help="training data split")

    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)
