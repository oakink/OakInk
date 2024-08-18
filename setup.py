from setuptools import setup, find_packages
import importlib
import os


def readme():
    readme_path = os.path.join(os.path.dirname(os.path.normpath(__file__)), "README.md")
    with open(readme_path, "r") as f:
        content = f.read()
    return content


def get_dep():
    req_txt = os.path.join(os.path.dirname(os.path.normpath(__file__)), "requirements.txt")
    with open(req_txt, "r") as f:
        content = f.read()

    res_default = [el for el in content.split("\n") if len(el) > 0 and "@git+" not in el]
    res_thirdparty = [el for el in content.split("\n") if len(el) > 0 and "@git+" in el]

    res_final = []
    for el in res_thirdparty:
        pkg = el.split("@git+")[0]
        try:
            importlib.import_module(pkg)
        except ImportError:
            res_final.append(el)

    res_final.extend(res_default)
    return res_final


get_dep()

setup(
    name="oikit",
    version="1.2.1",
    author="Lixin Yang",
    author_email="siriusyang@sjtu.edu.cn",
    description="OakInk tooKIT",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url=r"https://github.com/lixiny/OakInk.git",
    packages=find_packages(exclude=["data", "assets", "scripts", "docs"]),
    python_requires=">=3.8.0",
    install_requires=get_dep(),
)
