import json
import os
from tqdm import tqdm
from termcolor import cprint
from glob import glob
from hashlib import sha256


def main():
    oakink_dir = os.environ["OAKINK_DIR"]
    assert oakink_dir is not None, "Please set environment variable 'OAKINK_DIR'"

    zipped_dir = os.path.join(oakink_dir, "zipped")
    fnames = glob(os.path.join(zipped_dir, "**/*"), recursive=True)
    fnames = [f for f in fnames if os.path.isfile(f)]  # remove dir names

    with open(os.path.join("docs", "checksum.json"), "r") as f:
        gt_checksum = json.load(f)

    pbar = tqdm(fnames)
    for fn in pbar:
        if not (".zip" in fn or ".z0" in fn):
            continue
        if "stream_release_v2_combined.zip" in fn:
            continue
        pbar.set_description(f"Processing {fn}")
        with open(fn, "rb") as f:
            data = f.read()
        hashcode = sha256(data).hexdigest()
        fkey = fn.replace(zipped_dir, "").strip(os.sep)

        if fkey not in gt_checksum:
            cprint(f"Warning: file {fkey} not in assets/checksum.json", "blue")
            continue

        if hashcode != gt_checksum[fkey]:
            cprint(f"Error: file {fkey} has different checksum: {hashcode}", "red")


if __name__ == "__main__":
    main()
