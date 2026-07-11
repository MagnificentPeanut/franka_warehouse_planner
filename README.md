# franka-warehouse-sim

A Gazebo (Ignition Fortress) warehouse test environment for the Franka **fr3**,
built on top of `franka_ros2`. It provides:

- **`franka_warehouse_world`** — worlds with a table + mounted arm + a single
  box, launch files for the sim, and a MoveIt planning-scene publisher.
This is a **single meta repo**: the whole Franka stack is vendored directly
(no submodules) — `franka_ros2` and `franka_description` carry the sim-specific
changes (force/torque sensor state export in the Gazebo gravity-compensation
system, and rviz configs), alongside `libfranka` and `olvx`. One plain clone
gives the whole workspace `src`.

## Setup

Requires ROS 2 Humble + `ros-dev-tools` (`rosdep`, `colcon`).

```bash
# clone directly as your workspace src/
git clone https://github.com/ranikinnal44/franka-warehouse-sim.git ~/franka_ws/src

cd ~/franka_ws
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
source install/setup.bash
```

> Two apt packages are only needed by `franka_mobile_sensors` (not the
> warehouse sim): `ros-humble-realsense2-description`,
> `ros-humble-sick-safetyscanners2`.

## Run

```bash
# Terminal 1 — Gazebo sim (small = 200x300x400 mm box, large = 200x400x400 mm)
ros2 launch franka_warehouse_world warehouse.launch.py world:=large rviz:=false
# Terminal 2 — MoveIt: move_group + RViz + planning scene (table + box)
ros2 launch franka_warehouse_world moveit.launch.py world:=large
```

See [`franka_warehouse_world/README.md`](franka_warehouse_world/README.md) for
details on the worlds, the arm mounting, and the MoveIt integration.

## Pick-and-place, planner comparison, and benchmarks

**`franka_pick_place`** builds on the sim above to run autonomous
pick-and-place cycles with a switchable motion planner
(default MoveIt `RRTConnect` or **CHOMP**) and an optional collision obstacle:

```bash
# Terminal 1: Gazebo sim
ros2 launch franka_warehouse_world warehouse.launch.py world:=small rviz:=false
# Terminal 2: MoveIt (move_group + RViz)
ros2 launch franka_warehouse_world moveit.launch.py world:=small
# Terminal 3: pick-and-place
ros2 launch franka_pick_place pick_place.launch.py world:=small launch_sim:=false planner_id:=RRTConnect cycles:=10
```

See [`franka_pick_place/README.md`](franka_pick_place/README.md) for launch
arguments (planner selection, obstacle, cycle count) and
[`benchmarks/benchmark_results_gazebo_physics_verified.md`](benchmarks/benchmark_results_gazebo_physics_verified.md)
for the RRTConnect vs. CHOMP benchmark results (success rate, planning time,
path quality, collision-avoidance behaviour) across both box sizes and
obstacle conditions.

## Contents / provenance

All packages are vendored in-repo. Provenance:

| Component | Source |
|-----------|--------|
| `franka_warehouse_world` | this repo (Apache-2.0) |
| `franka_ros2` | `frankarobotics` v2.5.0 + warehouse-sim changes |
| `franka_description` | `frankarobotics` 2.8.0 + rviz change |
| `libfranka` | `frankarobotics` 0.20.4 (unmodified) |
| `olvx_descriptions_module` | `olive-robotics` main (unmodified) |
