from glob import glob

from setuptools import setup

package_name = "pennair_ros2"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Ari Korpus",
    maintainer_email="arikorpus26@gmail.com",
    description="Shape detection and 3D localisation for the PennAIR 2024 challenge.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "video_publisher = pennair_ros2.video_publisher:main",
            "shape_detector = pennair_ros2.shape_detector:main",
        ],
    },
)
