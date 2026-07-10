#!/bin/bash
pkill -f ros2; pkill -f gazebo; pkill -f ruby; sleep 2
source /opt/ros/humble/setup.bash && source install/setup.bash
LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 MESA_GLSL_VERSION_OVERRIDE=450 ros2 launch franka_pick_place pick_place.launch.py world:=small cycles:=1 > /tmp/pick_place.log 2>&1 &
PP_PID=$!
sleep 150
kill -9 $PP_PID
pkill -f ros2; pkill -f gazebo; pkill -f ruby
cat /tmp/pick_place_metrics_small.json
