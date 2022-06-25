import trimesh
import logging


def suppress_trimesh_logging():
    logger = logging.getLogger("trimesh")
    logger.setLevel(logging.ERROR)