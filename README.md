<br />
<p align="center">
  <p align="center">
    <img src="docs/oakink_logo.png"" alt="Logo" width="40%">
  </p>

<h1 align="center">A Large-scale Knowledge Repository for Understanding Hand-Object Interaction </h1>

  <p align="center">
    <strong>CVPR, 2022</strong>
    <br />
    <a href="https://lixiny.github.io"><strong>Lixin Yang*</strong></a>
    ·
    <a href="https://kailinli.top"><strong>Kailin Li*</strong></a>
    ·
    <a href=""><strong>Xinyu Zhan*</strong></a>
    ·
    <a href=""><strong>Fei Wu</strong></a>
    ·
    <a href="https://anran-xu.github.io"><strong>Anran Xu</strong></a>
    .
    <a href="https://liuliu66.github.io"><strong>Liu Liu</strong></a>
    ·
    <a href="https://mvig.sjtu.edu.cn"><strong>Cewu Lu</strong></a>
    <br />
    \star = equal contribution
  </p>

  <p align="center">
  <a href='https://openaccess.thecvf.com/content/CVPR2022/html/Yang_OakInk_A_Large-Scale_Knowledge_Repository_for_Understanding_Hand-Object_Interaction_CVPR_2022_paper.html'>
      <img src='https://img.shields.io/badge/Paper-PDF-yellow?style=flat&logo=googlescholar&logoColor=blue' alt='Paper PDF'>
    </a>
    <a href='https://arxiv.org/abs/2203.15709' style='padding-left: 0.5rem;'>
      <img src='https://img.shields.io/badge/ArXiv-PDF-green?style=flat&logo=arXiv&logoColor=green' alt='ArXiv PDF'>
    </a>
    <a href='https://oakink.net' style='padding-left: 0.5rem;'>
      <img src='https://img.shields.io/badge/Project-Page-blue?style=flat&logo=Google%20chrome&logoColor=blue' alt='Project Page'>
    <a href='https://www.youtube.com/watch?v=vNTdeXlLdU8' style='padding-left: 0.5rem;'>
      <img src='https://img.shields.io/badge/Youtube-Video-red?style=flat&logo=youtube&logoColor=red' alt='Youtube Video'>
    </a>
  </p>
</p>
<br />

This repo contains OakInk Toolkit **oikit** -- a Python package that provides data loading and visualization tools for the OakInk-Image, OakInk-Shape dataset and Oak base.

# Installation

We test the installation with:  
<a href="https://releases.ubuntu.com/20.04/">
<img alt="Ubuntu" src="https://img.shields.io/badge/Ubuntu-20.04-green?logo=ubuntu&logoColor=yelgreenlow">
</a>
<a href="https://developer.nvidia.com/cuda-11.1.0-download-archive">
<img alt="PyTorch" src="https://img.shields.io/badge/CUDA-11.1-yellow?logo=nvidia&logoColor=yellow">
</a>
<a href="">
<img alt="Python" src="https://img.shields.io/badge/Python-3.8-yellow?logo=python&logoColor=yellow">
</a>
<a href="https://pytorch.org/get-started/locally/">
<img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-1.9.1-yellow?logo=pytorch&logoColor=red">
</a>

First, clone the repo:

```Shell
$ git clone https://github.com/lixiny/OakInk.git
$ cd OakInk
```

There are two different ways to use **oikit** in your project: **_stand-alone_** and **_import-as-package_**.

## stand-alone

For a good practice to use python package, we recommend users to use `conda` environment.  
The **_stand-alone_** mode will create an isolated `conda` env called: `oakink`:

```Shell
$ conda env create -f environment.yaml
$ pip install -r requirements.txt
```

## import-as-package (recommended)

In most cases, users want to use **oikit** in other `conda` env.  
To be able to import **oikit**, you need:

1. activate the destination env (we suppose that python, cudatookit, and pytorch have already been installed)
2. go to your `OakInk` directory and run:

```Shell
$ pip install .
```

To test the installation is complete, run:

```Shell
$ python -c "from oikit.oi_image import OakInkImage"
```

no error, no worry. Now you can use **oikit** in this env.

# Download Datasets

1. Download the datasets (OakInk-Image and OakInk-Shape) from the [project site](http://www.oakink.net). 
   Arrange all zip files into a directory: `path/to/data` as follow:

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
  After all the extractions are finished, you will have a your directory `path/to/data` of the following structure:
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
   $ export OAKINK_DIR=path/to/data
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
Download the `OakBase.zip` (containing object parts segmentation and attributes) from the [project site](http://www.oakink.net). unzip it to `path/to/data`. The directory structure should be like this:
``` shell
  ├── image      # OakInk-Image dataset
  ├── shape      # OakInk-Shape dataset
  └── OakBase    # Oak Base
```

we provide demo script to show how to access the Oak Base:
``` shell
$ python scripts/demo_oak_base.py --data_dir path/to/data
```




# Citation

If you find OakInk dataset and **oikit** useful for your research, please considering cite us:

    @InProceedings{YangCVPR2022OakInk,
      author    = {Yang, Lixin and Li, Kailin and Zhan, Xinyu and Wu, Fei and Xu, Anran and Liu, Liu and Lu, Cewu},
      title     = {{OakInk}: A Large-Scale Knowledge Repository for Understanding Hand-Object Interaction},
      booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
      year      = {2022},
    }
