# OakInk Datasets

## Table of content

- [Download full OakInk](#download-full-oakink)
- [Data documentation](data_doc.md)
- [Data splitting](processing.md)
- [Data visualization](visualize.md)


## Download full OakInk 
Setup your `$OAKINK_DIR` to a large storage, e.g.
```bash
$ export OAKINK_DIR=/storage/data/OakInk
$ echo $OAKINK_DIR
/storage/data/OakInk
``` 

Download three parts of OakInk: **OakBase**, **OakInk-Image**, and **OakInk-Shape** from the [project site](http://www.oakink.net).  
Arrange all zip files into the directory: `$OAKINK_DIR/zipped` as follow:

```bash
├── OakBase.zip
├── image
│   ├── anno_v2_1.zip # Access via Google Forms
│   ├── obj.zip
│   └── stream_zipped
│       ├── oakink_image_v2.z01
│       └── ...
└── shape
    ├── metaV2.zip
    ├── OakInkObjectsV2.zip
    ├── oakink_shape_v2.zip
    └── OakInkVirtualObjectsV2.zip
```
After download, verify the checksum:
```bash
$ python verify_checksum.py
```
and unzip all the files:  
[7zip](https://www.7-zip.org/download.html) is required. Install it via `sudo apt install p7zip-full`

```bash
$ python unzip_all.py
```

After unzipping, the directory structure should look like this:
```bash
├── OakBase
├── image
│   ├── anno
│   ├── obj
│   └── stream_release_v2
└── shape
    ├── metaV2
    ├── OakInkObjectsV2
    ├── oakink_shape_v2
    └── OakInkVirtualObjectsV2
```


## Data documentation

What's inside data folder
```bash
OAKINK_DIR/ : ROOT
OAKINK_DIR/OakBase/ : OakBase root
OAKINK_DIR/OakBase/binoculars/ : category (binoculars) root
   binoculars_0/ : obj instance
      part_*.json : part-level attributes
      part_*.ply : part-level obj pointcloud
   binoculars_1/
   ..                
..

OAKINK_DIR/image/: OakInk-Image root





```