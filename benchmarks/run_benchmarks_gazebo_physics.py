import subprocess
import time
import os
import sys

def run_benchmark(planner, obstacle, world='small', cycles=10):
    print(f"============================================================")
    print(f"Starting Gazebo Physics benchmark: planner={planner}, obstacle={obstacle}, world={world}")
    print(f"============================================================")
    # Force kill everything before starting
    os.system('pkill -9 -f "ign|ruby|gz-sim|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager" 2>/dev/null')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(5)
    cmd = f"source install/setup.bash && ros2 launch franka_pick_place pick_place.launch.py world:={world} with_obstacle:={obstacle} cycles:={cycles} planner_id:={planner}"
    process = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    cycles_completed = 0
    while True:
        line = process.stdout.readline()
        if line:
            print(f"[ROS] {line.strip()}")
            sys.stdout.flush()
        if not line:
            if process.poll() is not None:
                print("Process exited prematurely!")
                break
            continue
        if "Cycle " in line and "completed" in line.lower():
            cycles_completed += 1
            print(f"[Progress] Completed cycle {cycles_completed}")
        elif "Saved metrics to" in line:
            print(f"[Success] {line.strip()}")
            break
    print(f"Benchmark with planner={planner}, obstacle={obstacle}, world={world} finished. Stopping launch process...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    os.system('pkill -9 -f "ign|ruby|gz-sim|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager" 2>/dev/null')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(3)

if __name__ == "__main__":
    print("Starting Gazebo Physics-enabled benchmark suite for LARGE box...")
    run_benchmark('RRTConnect', 'false', world='large', cycles=10)
    run_benchmark('RRTConnect', 'true', world='large', cycles=10)
    run_benchmark('CHOMP', 'false', world='large', cycles=10)
    run_benchmark('CHOMP', 'true', world='large', cycles=10)
    print("All large-box physics-enabled benchmarks completed successfully!")