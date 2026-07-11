import os
from glob import glob
from setuptools import setup

package_name = 'franka_pick_place'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='vrobotics developer',
    maintainer_email='vrobotics-developer@vegam.co',
    description='Pick and place execution node for Franka warehouse simulation',
    license='Apache 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pick_place_node = franka_pick_place.pick_place_node:main',
            'pick_place_node_chomp = franka_pick_place.pick_place_node_chomp:main',
            'fast_detach_node = franka_pick_place.fast_detach_node:main'
        ],
    },
)
