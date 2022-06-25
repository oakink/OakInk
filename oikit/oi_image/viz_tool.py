import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

edge_list_hand = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]
vert_color_hand = np.array([
    [1.0, 0.0, 0.0],
    #
    [0.0, 0.4, 0.2],
    [0.0, 0.6, 0.3],
    [0.0, 0.8, 0.4],
    [0.0, 1.0, 0.5],
    #
    [0.0, 0.0, 0.4],
    [0.0, 0.0, 0.6],
    [0.0, 0.0, 0.8],
    [0.0, 0.0, 1.0],
    #
    [0.0, 0.4, 0.4],
    [0.0, 0.6, 0.6],
    [0.0, 0.8, 0.8],
    [0.0, 1.0, 1.0],
    #
    [0.4, 0.4, 0.0],
    [0.6, 0.6, 0.0],
    [0.8, 0.8, 0.0],
    [1.0, 1.0, 0.0],
    #
    [0.4, 0.0, 0.4],
    [0.6, 0.0, 0.6],
    [0.7, 0.0, 0.8],
    [1.0, 0.0, 1.0],
])
vert_color_hand = vert_color_hand[:, ::-1]
edge_color_hand = np.array([
    vert_color_hand[1, :],
    vert_color_hand[2, :],
    vert_color_hand[3, :],
    vert_color_hand[4, :],
    vert_color_hand[5, :],
    vert_color_hand[6, :],
    vert_color_hand[7, :],
    vert_color_hand[8, :],
    vert_color_hand[9, :],
    vert_color_hand[10, :],
    vert_color_hand[11, :],
    vert_color_hand[12, :],
    vert_color_hand[13, :],
    vert_color_hand[14, :],
    vert_color_hand[15, :],
    vert_color_hand[16, :],
    vert_color_hand[17, :],
    vert_color_hand[18, :],
    vert_color_hand[19, :],
    vert_color_hand[20, :],
])
vert_type_hand = [
    "star",
    "circle",
    "square",
    "triangle_up",
    "diamond",
    "circle",
    "square",
    "triangle_up",
    "diamond",
    "circle",
    "square",
    "triangle_up",
    "diamond",
    "circle",
    "square",
    "triangle_up",
    "diamond",
    "circle",
    "square",
    "triangle_up",
    "diamond",
]

edge_list_obj = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 0],
    [4, 5],
    [5, 6],
    [6, 7],
    [7, 4],
    [1, 5],
    [2, 6],
    [3, 7],
    [0, 4],
]


def caption_view(image, caption="This is a caption"):
    ncol = image.shape[1]
    canvas = np.ones((30, ncol, 3), dtype=np.uint8) * 255
    font = ImageFont.truetype("FreeMonoBold.ttf", size=20)
    canvas_pil = Image.fromarray(canvas)
    draw = ImageDraw.Draw(canvas_pil)
    draw.text((20, 5), caption, font=font, fill=(0, 0, 0))
    canvas = np.array(canvas_pil)
    res = np.concatenate([canvas, image], axis=0)
    return res


def draw_wireframe_hand(img, hand_joint_arr, hand_joint_mask):
    draw_wireframe(
        img,
        hand_joint_arr,
        edge_list=edge_list_hand,
        vert_color=vert_color_hand,
        edge_color=edge_color_hand,
        vert_type=vert_type_hand,
        vert_mask=hand_joint_mask,
    )


def draw_wireframe(img,
                   vert_list,
                   vert_color=np.array([200.0, 0.0, 0.0]),
                   edge_color=np.array([0.0, 0.0, 200.0]),
                   edge_list=edge_list_obj,
                   vert_size=3,
                   edge_size=1,
                   vert_type=None,
                   vert_mask=None):

    vert_list = np.asarray(vert_list)
    n_vert = len(vert_list)
    n_edge = len(edge_list)
    vert_color = np.asarray(vert_color)
    edge_color = np.asarray(edge_color)

    # expand edge color
    if edge_color.ndim == 1:
        edge_color = np.tile(edge_color, (n_edge, 1))

    # expand edge size
    if isinstance(edge_size, (int, float)):
        edge_size = [edge_size] * n_edge

    # # expand vert color
    if vert_color.ndim == 1:
        vert_color = np.tile(vert_color, (n_vert, 1))

    # expand vert size
    if isinstance(vert_size, (int, float)):
        vert_size = [vert_size] * n_vert

    # set default vert type
    if vert_type is None:
        vert_type = ["circle"] * n_vert

    # draw edge
    for edge_id, connection in enumerate(edge_list):
        if vert_mask is not None:
            if not vert_mask[int(connection[1])] or not vert_mask[int(connection[0])]:
                continue
        coord1 = vert_list[int(connection[1])]
        coord2 = vert_list[int(connection[0])]
        cv2.line(
            img,
            coord1.astype(np.int32),
            coord2.astype(np.int32),
            color=edge_color[edge_id] * 255,
            thickness=edge_size[edge_id],
        )

    for vert_id in range(vert_list.shape[0]):
        if vert_mask is not None:
            if not vert_mask[vert_id]:
                continue
        draw_type = vert_type[vert_id]
        # if vert_id in [1, 5, 9, 13, 17]:  # mcp joint
        if draw_type == "circle":
            cv2.circle(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                radius=vert_size[vert_id],
                color=vert_color[vert_id] * 255,
                thickness=cv2.FILLED,
            )
        # elif vert_id in [2, 6, 10, 14, 18]:  # proximal joints
        elif draw_type == "square":
            cv2.drawMarker(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                color=vert_color[vert_id] * 255,
                markerType=cv2.MARKER_SQUARE,
                markerSize=vert_size[vert_id] * 2,
            )
        # elif vert_id in [3, 7, 11, 15, 19]:  # distal joints:
        elif draw_type == "triangle_up":
            cv2.drawMarker(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                color=vert_color[vert_id] * 255,
                markerType=cv2.MARKER_TRIANGLE_UP,
                markerSize=vert_size[vert_id] * 2,
            )
        # elif vert_id in [4, 8, 12, 16, 20]:
        elif draw_type == "diamond":
            cv2.drawMarker(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                color=vert_color[vert_id] * 255,
                markerType=cv2.MARKER_DIAMOND,
                markerSize=vert_size[vert_id] * 2,
            )
        elif draw_type == "star":
            cv2.drawMarker(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                color=vert_color[vert_id] * 255,
                markerType=cv2.MARKER_STAR,
                markerSize=vert_size[vert_id] * 2,
            )
        else:
            # fallback
            cv2.circle(
                img,
                (int(vert_list[vert_id, 0]), int(vert_list[vert_id, 1])),
                radius=vert_size[vert_id],
                color=vert_color[vert_id] * 255,
                thickness=cv2.FILLED,
            )
