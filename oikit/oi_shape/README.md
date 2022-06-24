# OakInk-Shape

To visualize the OakInk-Shape part, please follow the instructions below.

Step 1:

* Download [metaV2](xxx), [oakink_shape_v2](xxx), and the two object files (including [real](xxxx) and [virtual](xxxx)]). Then, unzip the files and put them into the `data` directory.
* Download [mano](xxxx) following the official instructions. Then, put it into the `assets` directory.

Step 2:

Install the environment.

Step 3:

Run `python oikit/oi_shape/oi_shape.py`. (Please make sure you have a visualizer window open.)

You can change the code in the `oi_shape.py` to visualize a part of the OakInk-Shape.

For example, use the following code to visualize the grapes on `pens` with a `handover` intent under `train` data split.

```python
    dataset: OakInkShape = OakInkShape(category="pen", intent_mode="handover", data_split="train")
```