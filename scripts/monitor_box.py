import subprocess
import time
import re

def get_box_pose():
    try:
        result = subprocess.run(['ign', 'model', '-m', 'box', '-p'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            m = re.search(r'\[([\d\.-]+)\s+([\d\.-]+)\s+([\d\.-]+)', result.stdout)
            if m:
                return [float(x) for x in m.groups()]
    except Exception:
        pass
    return None

start_time = time.time()
max_z = 0.0
poses = []

print("Monitoring box pose...")
while time.time() - start_time < 300: # monitor for 5 minutes max
    pose = get_box_pose()
    if pose:
        poses.append(pose)
        z = pose[2]
        if z > max_z:
            max_z = z
        print(f"Time {time.time()-start_time:.1f}s | Box pose: X={pose[0]:.3f}, Y={pose[1]:.3f}, Z={pose[2]:.3f}")
    time.sleep(2)

print(f"Max Z reached: {max_z:.3f}")
