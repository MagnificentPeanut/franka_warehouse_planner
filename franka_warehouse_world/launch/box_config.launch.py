# Copyright (c) 2026 Franka test workspace
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Convenience wrapper to launch one of the two box configurations.

Starts Gazebo with the selected box size and optionally MoveIt + RViz.
Only ONE box configuration is active per run.

Box configurations:
  small  ->  200 x 300 x 400 mm  (warehouse_boxes_200x300x400.sdf)
  large  ->  200 x 400 x 400 mm  (warehouse_boxes_200x400x400.sdf)

Usage examples::

    # 200 x 300 x 400 mm box, Gazebo + MoveIt + RViz
    ros2 launch franka_warehouse_world box_config.launch.py box:=small

    # 200 x 400 x 400 mm box, Gazebo only (no MoveIt)
    ros2 launch franka_warehouse_world box_config.launch.py box:=large moveit:=false

    # 200 x 300 x 400 mm box, no RViz in either Gazebo or MoveIt launch
    ros2 launch franka_warehouse_world box_config.launch.py box:=small rviz:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

# Map the user-facing 'box' argument to the world key used by warehouse.launch.py.
# Both keys match the WORLDS dict in warehouse.launch.py:
#   small -> warehouse_boxes_200x300x400.sdf  (200x300x400 mm)
#   large -> warehouse_boxes_200x400x400.sdf  (200x400x400 mm)
BOX_CONFIGS = {
    'small': '200 x 300 x 400 mm',
    'large': '200 x 400 x 400 mm',
}


def generate_launch_description():
    pkg = FindPackageShare('franka_warehouse_world')

    # ---- Launch arguments ------------------------------------------------
    box_arg = DeclareLaunchArgument(
        'box',
        default_value='small',
        description=(
            "Box configuration to load. Exactly one is active per run.\n"
            "  small -> 200 x 300 x 400 mm  (warehouse_boxes_200x300x400.sdf)\n"
            "  large -> 200 x 400 x 400 mm  (warehouse_boxes_200x400x400.sdf)"
        ),
    )
    moveit_arg = DeclareLaunchArgument(
        'moveit',
        default_value='true',
        description='true/false: also start MoveIt (move_group + RViz planning display).',
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='true/false: show RViz in the MoveIt launch.',
    )
    gripper_arg = DeclareLaunchArgument(
        'load_gripper',
        default_value='false',
        description='true/false: mount an end effector.',
    )
    ee_id_arg = DeclareLaunchArgument(
        'ee_id',
        default_value='franka_hand',
        description="End-effector: 'franka_hand' (finger gripper) or 'cobot_pump' (vacuum suction).",
    )
    robot_type_arg = DeclareLaunchArgument(
        'robot_type',
        default_value='fr3',
        description='Franka robot variant: fr3, fp3, or fer.',
    )
    controller_arg = DeclareLaunchArgument(
        'controller',
        default_value='fr3_arm_controller',
        description='Gazebo ros2_control controller to load.',
    )

    # ---- Gazebo warehouse sim -------------------------------------------
    # Passes 'box' directly as 'world' — both use the same small/large keys.
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg, 'launch', 'warehouse.launch.py'])
        ),
        launch_arguments={
            'world':        LaunchConfiguration('box'),
            'robot_type':   LaunchConfiguration('robot_type'),
            'load_gripper': LaunchConfiguration('load_gripper'),
            'franka_hand':  LaunchConfiguration('ee_id'),
            'controller':   LaunchConfiguration('controller'),
            # Disable RViz in the Gazebo launch when MoveIt is starting — MoveIt
            # brings its own, richer RViz with MotionPlanning display.
            'rviz':         'false',
        }.items(),
    )

    # ---- MoveIt (move_group + planning scene + RViz) --------------------
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg, 'launch', 'moveit.launch.py'])
        ),
        launch_arguments={
            'world':        LaunchConfiguration('box'),
            'load_gripper': LaunchConfiguration('load_gripper'),
            'ee_id':        LaunchConfiguration('ee_id'),
            'rviz':         LaunchConfiguration('rviz'),
            'use_sim_time': 'true',
        }.items(),
        condition=IfCondition(LaunchConfiguration('moveit')),
    )

    return LaunchDescription([
        box_arg,
        moveit_arg,
        rviz_arg,
        gripper_arg,
        ee_id_arg,
        robot_type_arg,
        controller_arg,
        gazebo_launch,
        moveit_launch,
    ])
