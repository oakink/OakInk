import os
import json

CATEGORIES = [
    'pincer',
    'hammer',
    'power_drill',
    'can',
    'screwdriver',
    'squeeze_tube',
    'cup',
    'wrench',
    'game_controller',
    'camera',
    'headphones',
    'mouse',
    'frying_pan',
    'bowl',
    'trigger_sprayer',
    'mug',
    'binoculars',
    'lotion_bottle',
    'flashlight',
    'eyeglasses',
    'lightbulb',
    'marker',
    'toothbrush',
    'bottle',
    'cylinder_bottle',
    'wineglass',
    'teapot',
    'scissor',
    'knife',
]

ATTRIBUTE_PHRASES = [
    "contain_sth",
    "cover_sth",
    "pump_out_sth",
    "cut_sth",
    "stab_sth",
    "flow_out_sth",
    "flow_in_sth",
    "secure_sth",
    "tighten_sth",
    "loosen_sth",
    "control_sth",
    "clamp_sth",
    "brush_sth",
    "trigger_sth",
    "observe_sth",
    "illuminate_sth",
    "point_to_sth",
    "shear_sth",
    "attach_to_sth",
    "connect_to_sth",
    "knock_sth",
    "spray_sth",
    "draw_sth",
    "no_function",
    "held_by_hand",
    "pulled_by_hand",
    "pressed/unpressed_by_hand",
    "screwed/unscrewed_by_hand",
    "plugged/unplugged_by_hand",
    "squeezed/unsqueezed_by_hand",
]


class ObjectAffordanceKnowledge:

    def __init__(self, category, obj_id, n_parts, obj_dir, part_files):
        self.category = category
        self.obj_id = obj_id
        self.n_parts = n_parts
        self.obj_dir = obj_dir

        self.part_names = []
        self.part_name_to_segs = {}
        self.part_name_to_attrs = {}
        self.part_attr_to_names = {}

        for pf in part_files:
            assert pf.endswith(".ply") and pf.startswith("part_"), f"part file {pf} is not valid"
            pif = os.path.join(obj_dir, pf[:-4] + ".json")
            assert os.path.exists(pif), f"part info file {pif} does not exist"
            with open(pif, "r") as f:
                part_info = json.load(f)
            part_name = part_info["name"]  # str
            part_attrs = part_info["attr"]  # list of str

            self.part_names.append(part_name)
            self.part_name_to_segs[part_name] = os.path.join(obj_dir, pf)
            self.part_name_to_attrs[part_name] = part_attrs
            for attr in part_attrs:
                if attr not in self.part_attr_to_names:
                    self.part_attr_to_names[attr] = []
                self.part_attr_to_names[attr].append(part_name)

    def get_part_name_by_attribute(self, attribute):
        if attribute == "attach_to":
            part_name_list = []
            for attr in self.part_attr_to_names.keys():
                if attr.startswith("attach_to"):
                    part_name_list.extend(self.part_attr_to_names[attr])
        elif attribute == "connect_to":
            part_name_list = []
            for attr in self.part_attr_to_names.keys():
                if attr.startswith("connect_to"):
                    part_name_list.extend(self.part_attr_to_names[attr])
        else:
            part_name_list = self.part_attr_to_names[attribute]

        return part_name_list

    def get_part_attribute_by_name(self, name):
        return self.part_name_to_attrs[name]

    def __repr__(self):
        return f"cate:{self.category}--id:{self.obj_id}"


class OakBase:

    def __init__(self):
        self._data_dir = os.path.join(os.environ["OAKINK_DIR"], "OakBase")
        self.categories = {}
        self.attributes = {}
        for cate in os.listdir(self._data_dir):
            cate_dir = os.path.join(self._data_dir, cate)
            if not os.path.isdir(cate_dir):
                continue

            if cate not in self.categories:
                self.categories[cate] = []

            for obj_id in os.listdir(cate_dir):
                obj_dir = os.path.join(cate_dir, obj_id)
                if not os.path.isdir(obj_dir):
                    continue

                part_files = [pf for pf in os.listdir(obj_dir) if pf.endswith(".ply")]
                oak = ObjectAffordanceKnowledge(category=cate,
                                                obj_id=obj_id,
                                                n_parts=len(part_files),
                                                obj_dir=obj_dir,
                                                part_files=part_files)
                self.categories[cate].append(oak)

                attrs = list(oak.part_attr_to_names.keys())
                for attr in attrs:
                    if attr not in self.attributes:
                        self.attributes[attr] = []
                    self.attributes[attr].append(oak)

    def get_objs_by_category(self, category):
        return self.categories[category]

    def get_objs_by_attribute(self, attribute):
        if attribute == "attach_to":
            obj_list = []
            for attr in self.attributes.keys():
                if attr.startswith("attach_to"):
                    obj_list.extend(self.attributes[attr])
        elif attribute == "connect_to":
            obj_list = []
            for attr in self.attributes.keys():
                if attr.startswith("connect_to"):
                    obj_list.extend(self.attributes[attr])
        else:
            obj_list = self.attributes[attribute]

        return obj_list
