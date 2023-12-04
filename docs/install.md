
# Installation

## Get started
We test the installation with general requirements:
* Ubuntu 20.04 or newer
* Python >= 3.8
* CUDA >= 11.1
* PyTorch >= 1.9.1

There are two different ways to use **oikit**, i.e. **_stand-alone_** and **_import-as-package_**.

- The **_stand-alone_** will create an isolated conda env called: `oakink`, all the dependencies will be set up in this env.   
If you are new to OakInk, use _stand-alone_ installation.
- The **_import-as-package_** will install **oikit** as a package in your current conda env.  
We suppose that python, cudatookit, and pytorch have already been installed. 

### stand-alone
```bash
$ conda env create -f environment.yaml
$ conda activate oakink
$ pip install -r requirements.txt
```

This environment provide you a base environment to load and visualize the OakInk dataset.

> :warning: In this case, you need to use the **oikit** inside the OakInk directory.  

### import-as-package (recommended)

In most cases, you want to use **oikit** in other conda env.
To be able to import **oikit**, you need:

1. activate the destination env (we suppose that python, cudatookit, and pytorch have already been installed)
2. cd to the `OakInk` directory and run: `pip install .`


## Get MANO asset

Get the MANO hand model `mano_v1_2.zip` from the [MANO website](https://mano.is.tue.mpg.de).  
1. click **`Download`** on the top menu, this requires register & login.
2. on the Download page, navigate to **Models & Code** section, and click `Models & Code`.  

Unzip `mano_v1_2.zip` and copy it into the `assets` folder.