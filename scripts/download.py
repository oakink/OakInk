import os
from termcolor import colored, cprint
try:
    import gdown
except ImportError:
    os.system("pip install gdown")
    import gdown

oakink_latest_release = [
    "OakBase.zip",
    "image/obj.zip"
    "image/stream_zipped",
    "shape/metaV2.zip",
    "shape/oakink_shape_v2.zip",
    "shape/OakInkObjectsV2.zip",
    "shape/OakInkVirtualObjectsV2.zip",
]


def main():
    oakink_dir = os.environ["OAKINK_DIR"]
    assert oakink_dir is not None, "Please set environment variable 'OAKINK_DIR'"
    input(colored(f"\nOAKIND_DIR at {oakink_dir}, press ENTER to continue", "yellow"))

    zipped_dir = os.path.join(oakink_dir, "zipped")
    os.makedirs(zipped_dir, exist_ok=True)

    with open("docs/gdrive_ids.json", "r") as f:
        gdrive_ids = f.read()

    for fname in oakink_latest_release:
        fid = gdrive_ids[fname]
        output = os.path.join(zipped_dir, fname)
        if "stream_zipped" in fname:  # download folder
            os.makedirs(output, exist_ok=True)
            gdown.download_folder(f"https://drive.google.com/drive/folders/{fid}", output=output, quiet=False)
        else:
            os.makedirs(os.path.dirname(output), exist_ok=True)
            gdown.download(f"https://drive.google.com/uc?id={fid}", output=output, quiet=False)

    msg = ("After downloading all the data, you need to fill out the online form:\n\n"
           "\t https://forms.gle/g6QEmmCeZYLGaVe29"
           "\n\nto get the annotation file: image/anno_v2.1.zip")
    print(msg)


if __name__ == "__main__":
    main()
