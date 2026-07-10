"""Pick-and-place launch file.

Two usage modes
---------------
1. **Standalone / all-in-one** (default, ``launch_sim:=true``):
   Starts Gazebo (with software rendering) + MoveIt + the pick-place node.
   Used by ``test_pick_place.sh`` and automated tests.

   ros2 launch franka_pick_place pick_place.launch.py world:=small

2. **Node-only** (``launch_sim:=false``):
   Assumes Gazebo and MoveIt are already running in separate terminals and
   just starts the pick-place node against them. Use this when you launched:
     Terminal 1: warehouse.launch.py   (Gazebo, software rendering)
     Terminal 2: moveit.launch.py      (MoveIt + RViz, no software rendering)

   ros2 launch franka_pick_place pick_place.launch.py world:=small launch_sim:=false
"""

import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
    GroupAction,
    PushEnvironment,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    warehouse_dir = get_package_share_directory('franka_warehouse_world')

    # ── Arguments ────────────────────────────────────────────────────────────
    world_arg    = DeclareLaunchArgument('world',      default_value='small')
    cycles_arg   = DeclareLaunchArgument('cycles',     default_value='3')
    obstacle_arg = DeclareLaunchArgument('with_obstacle', default_value='false')
    launch_sim_arg = DeclareLaunchArgument(
        'launch_sim', default_value='true',
        description=(
            'true  = start Gazebo + MoveIt here (all-in-one mode). '
            'false = connect to already-running Gazebo/MoveIt terminals.'
        ))
    controller_arg = DeclareLaunchArgument('controller', default_value='fr3_arm_controller')

    world      = LaunchConfiguration('world')
    cycles     = LaunchConfiguration('cycles')
    launch_sim = LaunchConfiguration('launch_sim')

    controller = LaunchConfiguration('controller')

    # ── Software rendering env-vars (only relevant for Gazebo child process) ─
    # Set before the Gazebo include so child processes inherit them.
    # Harmless for MoveIt/RViz which use a different renderer.
    sw_render_env = [
        SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE',       '1'),
        SetEnvironmentVariable('MESA_GL_VERSION_OVERRIDE',    '4.5'),
        SetEnvironmentVariable('MESA_GLSL_VERSION_OVERRIDE',  '450'),
    ]

    # ── Gazebo simulation (optional) ─────────────────────────────────────────
    # Launched only when launch_sim:=true. Software rendering env-vars above
    # will be inherited. rviz:=false because MoveIt launches its own RViz below.
    warehouse_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(warehouse_dir, 'launch', 'warehouse.launch.py')),
        launch_arguments={
            'world':         world,
            'rviz':          'false',
            'load_gripper':  'true',
            'franka_hand':   'cobot_pump',
            'controller':    controller,
        }.items(),
        condition=IfCondition(launch_sim),
    )

    # ── MoveIt + RViz (optional) ──────────────────────────────────────────────
    # MoveIt's RViz uses ogre1 and runs fine without software rendering.
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(warehouse_dir, 'launch', 'moveit.launch.py')),
        launch_arguments={
            'world':         world,
            'load_gripper':  'true',
            'ee_id':         'cobot_pump',
            'rviz':          'true',
        }.items(),
        condition=IfCondition(launch_sim),
    )

    # ── Pick-and-place node ───────────────────────────────────────────────────
    pick_place_node = Node(
        package='franka_pick_place',
        executable='pick_place_node',
        name='pick_place_node',
        output='screen',
        parameters=[{
            'use_sim_time': launch_sim,
            'world':  world,
            'cycles': cycles,
            'with_obstacle': LaunchConfiguration('with_obstacle'),
            'config': os.path.join(warehouse_dir, 'config', 'scene.yaml'),
        }],
    )

    # When launch_sim:=true  → wait 25 s for Gazebo + MoveIt to initialise.
    # When launch_sim:=false → wait  5 s (services already up, just need DDS).
    pick_place_with_sim = TimerAction(
        period=25.0,
        actions=[pick_place_node],
        condition=IfCondition(launch_sim),
    )
    pick_place_node_only = TimerAction(
        period=5.0,
        actions=[pick_place_node],
        condition=UnlessCondition(launch_sim),
    )

    return LaunchDescription([
        world_arg,
        cycles_arg,
        obstacle_arg,
        launch_sim_arg,
        controller_arg,

        # Isolate software rendering to Gazebo only
        GroupAction(
            actions=[
                PushEnvironment(),
                *sw_render_env,
                warehouse_launch,
            ]
        ),

        moveit_launch,
        pick_place_with_sim,
        pick_place_node_only,
    ])
