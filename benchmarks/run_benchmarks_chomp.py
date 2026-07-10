import subprocess
import time
import os
import sys

def run_benchmark(obstacle, cycles=10):
    print(f"============================================================")
    print(f"Starting benchmark with obstacle={obstacle}")
    print(f"============================================================")
    
    # Force kill everything before starting
    os.system('pkill -9 -f "gazebo|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager"')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(5)
    
    cmd = f"source install/setup.bash && ros2 launch franka_pick_place pick_place_chomp.launch.py world:=large with_obstacle:={obstacle} cycles:={cycles}"
    
    process = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Monitor output for completion
    cycles_completed = 0
    while True:
        line = process.stdout.readline()
        if not line:
            # Process exited?
            if process.poll() is not None:
                print("Process exited prematurely!")
                break
            continue
            
        # Optional: Print out cycles to show progress
        if "Cycle " in line and "completed" in line.lower():
            cycles_completed += 1
            print(f"[Progress] Completed cycle {cycles_completed}")
        elif "Saved metrics to" in line:
            print(f"[Success] {line.strip()}")
            break
            
    print(f"Benchmark with obstacle={obstacle} finished. Stopping launch process...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # Backup aggressive kill just in case
    os.system('pkill -9 -f "gazebo|gzserver|gzclient|move_group|robot_state_publisher|rviz2|pick_place_node|controller_manager" 2>/dev/null')
    os.system('killall -9 gzserver gzclient rviz2 2>/dev/null')
    time.sleep(3)

if __name__ == "__main__":
    print("Starting full benchmark suite for Phase 4 (CHOMP)...")
    run_benchmark('false', 10)
    run_benchmark('true', 10)
    print("All benchmarks completed successfully!")
