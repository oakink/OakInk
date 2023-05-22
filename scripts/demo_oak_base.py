import argparse
import os
from typing import List

import open3d as o3d

from oikit.oak_base import OakBase
from oikit.oak_base import ObjectAffordanceKnowledge as OAK


def main(arg):
    oakbase = OakBase()

    # get all categories
    all_cates: List[str] = oakbase.categories.keys()

    # get all objects in a category
    cate_objs: List[OAK] = oakbase.get_objs_by_category("teapot")
    print(f"Category: teapot has {len(cate_objs)} instances")

    # get all objects that contain a specific attribute
    attr_objs: List[OAK] = oakbase.get_objs_by_attribute("observe_sth")

    test_obj: OAK = attr_objs[0]
    # get all the attributes that the object has:
    all_attrs_of_obj: List[str] = test_obj.part_attr_to_names.keys()
    print(f"Object: {test_obj} has attributes: {list(all_attrs_of_obj)}")

    # get the parts of the object that contain the specific attribute
    part_names: List[str] = test_obj.get_part_name_by_attribute("observe_sth")

    test_part_name = part_names[0]
    # get all the attributes that the part has:
    all_attrs_of_part: List[str] = test_obj.get_part_attribute_by_name(test_part_name)
    print(f"Part: {test_part_name} has attributes: {all_attrs_of_part}")

    # get the path of the part's segmentation point cloud
    part_seg_path: str = test_obj.part_name_to_segs[test_part_name]

    # visualize the part's segmentation point cloud
    obj_pc = o3d.io.read_point_cloud(part_seg_path)
    obj_pc.paint_uniform_color([0.4, 0.8, 0.95])
    o3d.visualization.draw_geometries([obj_pc])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo OakBase")
    parser.add_argument("--data_dir", type=str, default="data", help="environment variable 'OAKINK_DIR'")
    arg = parser.parse_args()
    os.environ["OAKINK_DIR"] = arg.data_dir
    main(arg)