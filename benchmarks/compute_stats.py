import json
import sys
import numpy as np


def compute_metrics(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return

    segments_data = {}
    total_cycle_time = []
    sync_overhead = []
    pick_pos_acc = []
    pick_ori_acc = []
    place_pos_acc = []
    place_ori_acc = []

    first_try_success = 0
    retry_success = 0
    hard_failed = 0
    total_cycles = len(data)

    for cycle in data:
        cycle_failed = False
        had_retry = False
        cycle_plan_exec_sum = 0.0

        for seg_name, seg in cycle['segments'].items():
            if seg.get('hard_failure', False):
                cycle_failed = True
            if seg.get('attempts', 1) > 1:
                had_retry = True

            if seg_name not in segments_data:
                segments_data[seg_name] = {'plan_time': [], 'exec_time': [], 'attempts': [], 'path_length': []}

            p_time = seg.get('plan_time', 0.0)
            e_time = seg.get('exec_time', 0.0)
            segments_data[seg_name]['plan_time'].append(p_time)
            segments_data[seg_name]['exec_time'].append(e_time)
            segments_data[seg_name]['attempts'].append(seg.get('attempts', 1))
            segments_data[seg_name]['path_length'].append(seg.get('path_length', 0.0))
            cycle_plan_exec_sum += p_time + e_time

        if cycle_failed:
            hard_failed += 1
        elif had_retry:
            retry_success += 1
        else:
            first_try_success += 1

        if 'cycle_wall_time' in cycle and cycle_failed == False:
            total_cycle_time.append(cycle['cycle_wall_time'])
            sync_overhead.append(cycle['cycle_wall_time'] - cycle_plan_exec_sum)

        if 'accuracy' in cycle:
            if 'pick' in cycle['accuracy'] and isinstance(cycle['accuracy']['pick'], dict):
                pick_pos_acc.append(cycle['accuracy']['pick'].get('pos_error', 0.0))
                pick_ori_acc.append(cycle['accuracy']['pick'].get('ori_error', 0.0))
            if 'place' in cycle['accuracy'] and isinstance(cycle['accuracy']['place'], dict):
                place_pos_acc.append(cycle['accuracy']['place'].get('pos_error', 0.0))
                place_ori_acc.append(cycle['accuracy']['place'].get('ori_error', 0.0))

    print(f"Metrics for {file_path}")
    print("### Overall Cycle Metrics")
    print(f"- **Success Rate:** {first_try_success}/{total_cycles} first-try, {retry_success}/{total_cycles} with retries, {hard_failed}/{total_cycles} hard-failed")
    if total_cycle_time:
        print(f"- **Mean Cycle Time:** {np.mean(total_cycle_time):.2f}s (std: {np.std(total_cycle_time):.2f}s)")
        print(f"- **Sync/Overhead Time:** {np.mean(sync_overhead):.2f}s (std: {np.std(sync_overhead):.2f}s)")
    if pick_pos_acc:
        print(f"- **Pick Pos Accuracy Error:** {np.mean(pick_pos_acc):.6f}m")
        print(f"- **Pick Ori Accuracy Error:** {np.mean(pick_ori_acc):.6f}rad")
    if place_pos_acc:
        print(f"- **Place Pos Accuracy Error:** {np.mean(place_pos_acc):.6f}m")
        print(f"- **Place Ori Accuracy Error:** {np.mean(place_ori_acc):.6f}rad")
    print()
    print("### Segment Metrics")
    print("| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |")
    print("|---------|----------------------|----------------------|-----------------|-------------------------|")

    for seg_name in ['pre_grasp', 'approach', 'retreat', 'transit', 'place_approach', 'place_retreat']:
        if seg_name not in segments_data:
            continue
        d = segments_data[seg_name]
        print(f"| {seg_name} | {np.mean(d['plan_time']):.3f}s ± {np.std(d['plan_time']):.3f}s | "
              f"{np.mean(d['exec_time']):.3f}s ± {np.std(d['exec_time']):.3f}s | "
              f"{np.mean(d['attempts']):.1f} | {np.mean(d['path_length']):.2f}rad |")
    print("\n\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            compute_metrics(f)
    else:
        compute_metrics('src/franka_warehouse_planner/benchmarks/benchmark_default_rrtconnect_no_obstacle.json')
        compute_metrics('src/franka_warehouse_planner/benchmarks/benchmark_default_rrtconnect_with_obstacle.json')
