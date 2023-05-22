import os
import argparse
import json


def main(arg):
    split_key = {
        "default": "split0",
        "subject": "split1",
        "object": "split2",
        "handobject": "split0_ho",
    }[arg.mode_split]

    if arg.data_split == "train+val":
        split_file = os.path.join(arg.data_dir, "image", "anno", "split", split_key, "seq_train.json")
    elif arg.data_split == "train":
        split_file = os.path.join(
            arg.data_dir, "image", "anno", "split_train_val", split_key, "example_split_train.json"
        )
    elif arg.data_split == "val":
        split_file = os.path.join(arg.data_dir, "image", "anno", "split_train_val", split_key, "example_split_val.json")
    else:  # arg.data_split "test"
        split_file = os.path.join(arg.data_dir, "image", "anno", "split", split_key, "seq_test.json")

    with open(split_file, "r") as f:
        info_list = json.load(f)

    tuple_list = set()
    for info_item in info_list:
        pk, sid, fid, vid = info_item
        index_tuple = (pk, sid, fid)
        if index_tuple not in tuple_list:
            tuple_list.add(index_tuple)
    index_list = sorted(tuple_list)

    res = []
    for index_tuple in index_list:
        pk, sid, fid = index_tuple
        for vid in range(4):
            res.append((pk, sid, fid, vid))

    save_prefix = os.path.join(arg.data_dir, "image", "anno_mv")
    os.makedirs(save_prefix, exist_ok=True)
    if arg.data_split == "train+val":
        save_file = os.path.join(save_prefix, "split", split_key, "seq_train.json")
    elif arg.data_split == "train":
        save_file = os.path.join(save_prefix, "split_train_val", split_key, "example_split_train.json")
    elif arg.data_split == "val":
        save_file = os.path.join(save_prefix, "split_train_val", split_key, "example_split_val.json")
    else:  # arg.data_split "test"
        save_file = os.path.join(save_prefix, "split", split_key, "seq_test.json")
    dir_save = os.path.dirname(save_file)
    os.makedirs(dir_save, exist_ok=True)

    with open(save_file, "w") as f:
        json.dump(res, f)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ex sp for mv")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    parser.add_argument(
        "--data_split",
        type=str,
        choices=["train+val", "test", "train", "val"],
        required=True,
        help="training data split",
    )
    parser.add_argument(
        "--mode_split",
        type=str,
        choices=["subject", "object"],
        required=True,
        help="training mode split, see paper for more details",
    )
    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)
