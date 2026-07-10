#!/bin/bash
pkill -f ros2; pkill -f gazebo; pkill -f ruby; sleep 2
source /opt/ros/humble/setup.bash && source install/setup.bash
LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 MESA_GLSL_VERSION_OVERRIDE=450 ros2 launch franka_warehouse_world warehouse.launch.py world:=small rviz:=false load_gripper:=true franka_hand:=cobot_pump > /tmp/gazebo.log 2>&1 &
GAZEBO_PID=$!
sleep 15
ros2 launch franka_warehouse_world moveit.launch.py world:=small load_gripper:=true ee_id:=cobot_pump > /tmp/moveit.log 2>&1 &
MOVEIT_PID=$!
sleep 15
ros2 service list | grep -E "plan_kinematic_path|compute_cartesian_path" > /tmp/services.log
kill $MOVEIT_PID $GAZEBO_PID
pkill -f ros2; pkill -f gazebo; pkill -f ruby
cat /tmp/services.log
