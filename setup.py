from setuptools import setup, find_packages
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
    res = [el for el in content.split("\n") if len(el) > 0]
    return res


setup(
    name="oakink",
    version="1.0.0",
    author="Lixin Yang",
    author_email="siriusyang@sjtu.edu.cn",
    description="OakInk",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url=r"https://github.com/lixiny/OakInk.git",
    packages=find_packages(exclude=["data", "assets"]),
    python_requires=">=3.8.0",
    install_requires=get_dep(),
)
