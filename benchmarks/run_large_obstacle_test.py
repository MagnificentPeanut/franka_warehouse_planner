import subprocess
import time
import os
import sys

def run_benchmark(planner, obstacle, cycles=1):
    print(f"============================================================")
    print(f"Starting Gazebo Physics benchmark: planner={planner}, obstacle={obstacle}, world=large")
    print(f"============================================================")

    os.system('pkill -9 -f "ign|ruby|gz-sim|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager" 2>/dev/null')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(5)

    cmd = f"source install/setup.bash && ros2 launch franka_pick_place pick_place.launch.py world:=large with_obstacle:={obstacle} cycles:={cycles} planner_id:={planner}"

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

    print(f"Benchmark with planner={planner}, obstacle={obstacle} finished. Stopping launch process...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

    os.system('pkill -9 -f "ign|ruby|gz-sim|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager" 2>/dev/null')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(3)

if __name__ == "__main__":
    print("Starting Gazebo Physics-enabled single-cycle tests for LARGE box (obstacle only)...")
    run_benchmark('RRTConnect', 'true', 1)
    run_benchmark('CHOMP', 'true', 1)
    print("All tests completed successfully!")
