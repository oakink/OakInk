<br />
<p align="center">
  <p align="center">
    <img src="docs/oakink_logo.png"" alt="Logo" width="30%">
  </p>
  <h2 align="center">A Large-scale Knowledge Repository for Understanding Hand-Object Interaction </h2>

  <p align="center">
    <a href="https://lixiny.github.io"><strong>Lixin Yang*</strong></a>
    ·
    <a href="https://kailinli.top"><strong>Kailin Li*</strong></a>
    ·
    <a href=""><strong>Xinyu Zhan*</strong></a>
    ·
    <strong>Fei Wu</strong>
    ·
    <a href="https://anran-xu.github.io"><strong>Anran Xu</strong></a>
    .
    <a href="https://liuliu66.github.io"><strong>Liu Liu</strong></a>
    ·
    <a href="https://mvig.sjtu.edu.cn"><strong>Cewu Lu</strong></a>
  </p>
  <h3 align="center">CVPR 2022</h3>

  <div align="center">
    <img src="docs/teaser.png" alt="Logo" width="100%">
  </div>
  <br/>

  <p align="center">
    <a href="https://arxiv.org/abs/2203.15709">
      <img src='https://img.shields.io/badge/Paper-green?style=for-the-badge&logo=adobeacrobatreader&logoColor=white&labelColor=66cc00&color=94DD15' alt='Paper PDF'>
    </a>
    <a href='https://oakink.net'>
      <img src='https://img.shields.io/badge/Project-orange?style=for-the-badge&logo=Google%20chrome&logoColor=white&labelColor=D35400' alt='Project Page'></a>
    <a href="https://www.youtube.com/watch?v=vNTdeXlLdU8"><img alt="youtube views" title="Subscribe to my YouTube channel" src="https://img.shields.io/badge/Video-red?style=for-the-badge&logo=youtube&labelColor=ce4630&logoColor=red"/></a>
  </p>
</p>



This repo contains the **OakInk data toolkit (oikit)** -- a Python package that provides data 
preprocessing, splitting, and visualization tools for the OakInk knowledge repository.   

OakInk contains three parts:
* **OakBase:** Object Affordance Knowledge (Oak) base, including objects' part-level segmentation and attributes.
* **OakInk-Image:** a video dataset with 3D hand-object pose and shape annotations.
* **OakInk-Shape:** a 3D interacting pose dataset with hand and object mesh models.


### Summary on OakInk

- It contains 3D models, part segmentation, and affordance labels of 1,800 common household objects.
- It records human grasps with 100 (from 1,800) objects based on their affordances.
  - It contains 792 multi-view video clips (230K images) complemented with annotation.
  - Images are from four third-person views.
  - It contains dynamic grasping and handover motions.
  - It includes 3D ground-truth for MANO and objects.
- It contains a total of 50k hand-object interaction pose pairs involving the 1,800 objects.
  - 1k are from the recording, 49K are done via interaction transfer. 


### Why use OakInk:
- For studying hand-object pose estimation and hand-held object reconstruction. 
- For generating grasping pose, motion or handover with objects. 
- For generating affordance-aware pose or motion for object manipulation.
- For transferring hand pose or motion to a new object.


### News



## Getting Started
Clone the repo 
  ```bash
  $ git clone https://github.com/lixiny/OakInk.git
  ```
- Install environment: see [`docs/install.md`](docs/install.md)  
- Get the datasets: see [`docs/datasets.md`](docs/datasets.md)
- FAQ: see [`docs/faq.md`](docs/faq.md)

## Load and Visualize


## Train using OakInk




# Download Datasets

1. Download the datasets (OakInk-Image and OakInk-Shape) from the [project site](http://www.oakink.net).
   Arrange all zip files into a directory: `path/to/OakInk` as follow:

   ```
    .
    ├── image
    │   ├── anno.zip
    │   ├── obj.zip
    │   └── stream_zipped
    │       ├── oakink_image_v2.z01
    │       ├── ...
    │       ├── oakink_image_v2.z10
    │       └── oakink_image_v2.zip
    └── shape
        ├── metaV2.zip
        ├── OakInkObjectsV2.zip
        ├── oakink_shape_v2.zip
        └── OakInkVirtualObjectsV2.zip
   ```

2. Extract the files.

- For the `image/anno.zip`, `image/obj.zip` and `shape/*.zip`, you can simply _unzip_ it at the same level of the `.zip` file:
  ```Shell
  $ unzip obj.zip
  ```
- For the 11 split zip files in `image/stream_zipped`, you need to _cd_ into the `image/` directory, run:
  ```Shell
  $ zip -F ./stream_zipped/oakink_image_v2.zip --out single-archive.zip
  ```
  This will combine the split zip files into a single .zip, at `image/single-archive.zip`. Finally, _unzip_ the combined archive:
  ```Shell
  $ unzip single-archive.zip
  ```
  After all the extractions are finished, you will have a your directory `path/to/OakInk` of the following structure:
  ```
  .
  ├── image
  │   ├── anno
  │   ├── obj
  │   └── stream_release_v2
  │       ├── A01001_0001_0000
  │       ├── ....
  │
  └── shape
      ├── metaV2
      ├── OakInkObjectsV2
      ├── oakink_shape_v2
      └── OakInkVirtualObjectsV2
  ```

3. Set the environment variable `$OAKINK_DIR` to your dataset folder:

   ```Shell
   $ export OAKINK_DIR=path/to/OakInk
   ```

4. Download `mano_v1_2.zip` from the [MANO website](https://mano.is.tue.mpg.de), unzip the file and create symlink in `assets` folder:
   ```Shell
   $ mkdir assets
   $ ln -s path/to/mano_v1_2 assets/
   ```

## Load Dataset and Visualize

we provide three scripts to provide basic usage for data loading and visualizing:

1. visualize OakInk-Image set on sequence level:
   ```Shell
   $ python scripts/viz_oakink_image_seq.py (--help)
   ```
2. use OakInkImage to load data_split: `all` and visualize:

   ```Shell
   $ python scripts/viz_oakink_image.py (--help)
   ```

3. visualize OakInk-Shape set with object category and subject intent
   ```Shell
   $ python scripts/viz_oakink_shape.py --categories teapot --intent_mode use (--help)
   ```

# Download Oak Base

Download the `OakBase.zip` (containing object parts segmentation and attributes) from the [project site](http://www.oakink.net). unzip it to `path/to/OakInk`. The directory structure should be like this:

```shell
  ├── image      # OakInk-Image dataset
  ├── shape      # OakInk-Shape dataset
  └── OakBase    # Oak Base
```

we provide demo script to show how to access the Oak Base:

```shell
$ python scripts/demo_oak_base.py --data_dir path/to/OakInk
```

# Citation

If you find OakInk dataset and **oikit** useful for your research, please considering cite us:

    @InProceedings{YangCVPR2022OakInk,
      author    = {Yang, Lixin and Li, Kailin and Zhan, Xinyu and Wu, Fei and Xu, Anran and Liu, Liu and Lu, Cewu},
      title     = {{OakInk}: A Large-Scale Knowledge Repository for Understanding Hand-Object Interaction},
      booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
      year      = {2022},
    }
