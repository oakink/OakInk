import json

A = "data/image/anno_mv/split/split1/seq_train.json"
B = "data/image/anno_mv/split/split1/seq_test.json"

with open(A, 'r') as f:
    _a_list = json.load(f)
a_list = [tuple(el) for el in _a_list]

with open(B, 'r') as f:
    _b_list = json.load(f)
b_list = [tuple(el) for el in _b_list]

set(a_list).intersection(set(b_list))