# franka_pick_place

Autonomous pick-and-place of the warehouse box using MoveIt, with a switchable
motion planner and an optional collision obstacle.

- **Default planner:** `pick_place_node` plans with MoveIt's default
  `RRTConnectConfigDefault`.
- **Planner integration:** `pick_place_node_chomp` runs the same
  pick-and-place cycle with **CHOMP** instead.
- **Collision avoidance:** `with_obstacle:=true` adds a static
  0.1 × 0.1 × 0.50 m obstacle centred at (x=0.45, y=0.0, z=0.25) m — between
  the pick and place poses, in both the MoveIt planning scene and the live
  Gazebo world — that the nominal transit path would otherwise pass through.

Both nodes run identical pick → transit → place cycles and log the same
metrics (see below), enabling a like-for-like comparison.

## Run

```bash
# Terminal 1: Gazebo sim
ros2 launch franka_warehouse_world warehouse.launch.py world:=small rviz:=false
# Terminal 2: MoveIt (move_group + RViz)
ros2 launch franka_warehouse_world moveit.launch.py world:=small
# Terminal 3: pick-and-place, attaching to the already-running sim/MoveIt
ros2 launch franka_pick_place pick_place.launch.py world:=small launch_sim:=false planner_id:=RRTConnect cycles:=10
```

Or all-in-one (starts Gazebo + MoveIt + the pick-place node together):

```bash
ros2 launch franka_pick_place pick_place.launch.py world:=small planner_id:=RRTConnect with_obstacle:=false cycles:=10
```

### Launch arguments (`pick_place.launch.py`)

| Argument | Default | Description |
|---|---|---|
| `world` | `small` | `small` (200×300×400 mm box) or `large` (200×400×400 mm box). |
| `planner_id` | `RRTConnect` | `RRTConnect` (default MoveIt planner) or `CHOMP`. Selects both the pick-place executable (`pick_place_node` / `pick_place_node_chomp`) and the matching MoveIt launch file (`moveit.launch.py` / `moveit_chomp.launch.py`). |
| `with_obstacle` | `false` | Adds the collision obstacle to both the Gazebo world and the MoveIt planning scene. |
| `cycles` | `3` | Number of pick-and-place cycles to run before exiting. |
| `launch_sim` | `true` | `true` starts Gazebo + MoveIt here (all-in-one); `false` assumes they're already running in separate terminals (use this when following the 3-terminal flow above). |
| `controller` | `fr3_arm_controller` | Joint trajectory controller name, passed through to the Gazebo sim. |

`fast_detach_node` is launched alongside the pick-place node; it exists to
work around a Gazebo `DetachableJoint` startup race (see below) and needs no
configuration.

## Metrics and benchmarking

Each run logs per-cycle metrics (planning time, execution time, retry
attempts, path length, pick/place pose and orientation error) to
`benchmarks/benchmark_gazebo_physics_<planner>_<world>_<obstacle-suffix>.json`.
By default a node **refuses to overwrite an existing results file**; pass
`overwrite_results:=true` as a node parameter to replace it intentionally.

See [`benchmarks/run_benchmarks_gazebo_physics.py`](../benchmarks/run_benchmarks_gazebo_physics.py)
to drive a full sweep of planner × obstacle conditions unattended, and
[`benchmarks/benchmark_results_gazebo_physics_verified.md`](../benchmarks/benchmark_results_gazebo_physics_verified.md)
for the write-up of results.

## Notes on the Gazebo box attachment

The box is picked up via a suction gripper (`cobot_pump`) modeled as a Gazebo
`DetachableJoint` plugin, toggled by publishing to `/box/attach` /
`/box/detach`. `fast_detach_node` spams `/box/detach` at startup (at 100 Hz,
on the system clock) until a `/tmp/stop_early_detach` flag file appears —
this clears any box attachment left over from a previous aborted run, before
Gazebo's own `/clock` is necessarily publishing yet. The pick-place node
writes that flag file once its MoveIt services are confirmed ready.
