import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import numpy as np
import transforms3d as t3d
from collections.abc import Iterable, Sized
from opendr.camera import ProjectPoints
from opendr.renderer import ColoredRenderer
from opendr.lighting import LambertianPointLight


class OpenDRRenderer(object):

    def __init__(self, img_size=256, flength=500.0):  # 822.79041):  #
        self.w = img_size
        self.h = img_size
        self.flength = flength

    def __call__(
        self,
        verts,
        faces,
        cam_intrinsics,
        img=None,
        do_alpha=False,
        far=None,
        near=None,
        vertex_color=None,
        img_size=None,
        R=None,
    ):
        """
        cam is 3D [fx, fy, px, py]
        """
        # deal with image size
        if img is not None:
            h, w = img.shape[:2]
        elif img_size is not None:
            h = img_size[0]
            w = img_size[1]
        else:
            h = self.h
            w = self.w

        # deal with verts and faces; if both np array, then ok
        # if both are lists / tuple, need to combine them and do offset
        # also vc, if appliciable
        if isinstance(verts, np.ndarray) and isinstance(faces, np.ndarray):
            # support only one mesh
            final_verts = verts
            final_faces = faces
            if vertex_color is not None:
                if vertex_color.ndim == 1:
                    final_vertex_color = np.repeat(vertex_color[None, ...], len(verts), axis=0)
                else:
                    final_vertex_color = vertex_color
            else:
                final_vertex_color = None
        elif (isinstance(verts, Iterable) and isinstance(verts, Sized) and isinstance(faces, Iterable) and
              isinstance(faces, Sized)):
            # support multiple mesh
            assert len(verts) == len(faces), f"verts and faces do not match, got {len(verts)} and {len(faces)}"

            final_faces = []
            n_mesh = len(verts)
            curr_offset = 0  # offset of vert ids, alter faces
            for mesh_id in range(n_mesh):
                final_faces.append(faces[mesh_id] + curr_offset)
                curr_offset += len(verts[mesh_id])

            final_verts = np.concatenate(verts, axis=0)
            final_faces = np.concatenate(final_faces, axis=0)
            if vertex_color is not None:
                # it is tricky here, as we may need to repeat color
                # iterate and check
                # possible to optimize 2 loops into one if some one is willing to
                final_vertex_color = []
                for mesh_id in range(n_mesh):
                    if vertex_color[mesh_id].ndim == 1:
                        final_vertex_color.append(
                            np.repeat(vertex_color[mesh_id][None, ...], len(verts[mesh_id]), axis=0))
                    else:
                        final_vertex_color.append(vertex_color[mesh_id])
                final_vertex_color = np.concatenate(final_vertex_color, axis=0)
            else:
                final_vertex_color = None
        else:
            raise NotImplementedError(
                f"opendr do not support verts and faces, got type {type(verts)} and {type(faces)}")

        dist = np.zeros(5)
        dist = dist.flatten()
        M = np.eye(4)

        # get R, t from M (has to be world2cam)
        if R is None:
            R = M[:3, :3]
        ax, angle = t3d.axangles.mat2axangle(R)
        rt = ax * angle
        rt = rt.flatten()
        t = M[:3, 3]

        if cam_intrinsics is None:
            cam_intrinsics = np.array([[500, 0, 128], [0, 500, 128], [0, 0, 1]])

        pp = np.array([cam_intrinsics[0, 2], cam_intrinsics[1, 2]])
        f = np.array([cam_intrinsics[0, 0], cam_intrinsics[1, 1]])

        use_cam = ProjectPoints(
            rt=rt,
            t=t,
            f=f,
            c=pp,
            k=dist  # camera translation  # focal lengths  # camera center (principal point)
        )  # OpenCv distortion params

        if near is None:
            near = np.maximum(np.min(final_verts[:, 2]) - 25, 0.1)
        if far is None:
            far = np.maximum(np.max(final_verts[:, 2]) + 25, 25)

        imtmp = render_model(
            final_verts,
            final_faces,
            w,
            h,
            use_cam,
            do_alpha=do_alpha,
            img=img,
            far=far,
            near=near,
            color=final_vertex_color,
        )

        return (imtmp * 255).astype("uint8")


def simple_renderer(rn, verts, faces, yrot=np.radians(120), color=None):
    # Rendered model color
    rn.set(v=verts, f=faces, vc=color, bgcolor=np.ones(3))
    albedo = rn.vc

    # Construct front Light
    rn.vc = LambertianPointLight(
        f=rn.f,
        v=rn.v,
        num_verts=len(rn.v),
        light_pos=_rotateY(np.array([0, -100, -100]), yrot),
        vc=albedo,
        light_color=np.array([0.8, 0.8, 0.8]),
    )

    # Construct Back Light (on back right corner)
    rn.vc += LambertianPointLight(
        f=rn.f,
        v=rn.v,
        num_verts=len(rn.v),
        light_pos=_rotateY(np.array([-200, -100, -100]), yrot),
        vc=albedo,
        light_color=np.array([0.7, 0.7, 0.7]),
    )

    # Construct Left Light  # back
    rn.vc += LambertianPointLight(
        f=rn.f,
        v=rn.v,
        num_verts=len(rn.v),
        light_pos=_rotateY(np.array([300, 10, 300]), yrot),
        vc=albedo,
        light_color=np.array([0.8, 0.8, 0.8]),
    )

    # Construct Right Light  # front
    rn.vc += LambertianPointLight(
        f=rn.f,
        v=rn.v,
        num_verts=len(rn.v),
        light_pos=_rotateY(np.array([-500, 500, 1000]), yrot),
        vc=albedo,
        light_color=np.array([0.8, 0.8, 0.8]),
    )

    return rn.r


def _create_renderer(w=640, h=480, rt=np.zeros(3), t=np.zeros(3), f=None, c=None, k=None, near=0.5, far=10.0):

    f = np.array([w, w]) / 2.0 if f is None else f
    c = np.array([w, h]) / 2.0 if c is None else c
    k = np.zeros(5) if k is None else k

    rn = ColoredRenderer()

    rn.camera = ProjectPoints(rt=rt, t=t, f=f, c=c, k=k)
    rn.frustum = {"near": near, "far": far, "height": h, "width": w}
    return rn


def _rotateY(points, angle):
    """Rotate the points by a specified angle."""
    ry = np.array([[np.cos(angle), 0.0, np.sin(angle)], [0.0, 1.0, 0.0], [-np.sin(angle), 0.0, np.cos(angle)]])
    return np.dot(points, ry)


def render_model(verts, faces, w, h, cam, near=0.5, far=25, img=None, do_alpha=False, color=None):
    rn = _create_renderer(w=w, h=h, near=near, far=far, rt=cam.rt, t=cam.t, f=cam.f, c=cam.c)

    # Uses img as background, otherwise white background.
    if img is not None:
        rn.background_image = img / 255.0 if img.max() > 1 else img

    if color is None:
        color = np.array([102, 209, 243]) / 255.0  # light blue

    imtmp = simple_renderer(rn, verts, faces, color=color)

    return imtmp


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
