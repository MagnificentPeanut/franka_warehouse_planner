#!/bin/bash
pkill -f ros2; pkill -f gazebo; pkill -f ruby; sleep 2
source /opt/ros/humble/setup.bash && source install/setup.bash
LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 MESA_GLSL_VERSION_OVERRIDE=450 ros2 launch franka_warehouse_world box_config.launch.py box:=small moveit:=false rviz:=false > /dev/null 2>&1 &
PP_PID=$!
sleep 15
echo "Before moving:"
ign model -m box -p
# We attach it
ros2 topic pub --once /box/attach std_msgs/msg/Empty
sleep 1
# And lift the arm up manually using ros2 control or just check if attachment changes behavior.
# Wait, without moveit, arm won't move.
pkill -f ros2; pkill -f gazebo; pkill -f ruby
