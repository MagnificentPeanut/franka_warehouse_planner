Metrics for src/franka_warehouse_planner/benchmarks/benchmark_default_rrtconnect_small_no_obstacle.json
### Overall Cycle Metrics
- **Success Rate:** 10/10 first-try, 0/10 with retries, 0/10 hard-failed
- **Mean Cycle Time:** 30.27s (std: 2.72s)
- **Sync/Overhead Time:** 10.40s (std: 0.12s)
- **Pick Pos Accuracy Error:** 0.000001m
- **Pick Ori Accuracy Error:** 0.000566rad
- **Place Pos Accuracy Error:** 0.004809m
- **Place Ori Accuracy Error:** 0.020767rad

### Segment Metrics
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 0.058s ± 0.015s | 4.269s ± 0.854s | 1.0 | 3.49rad |
| approach | 0.052s ± 0.002s | 2.404s ± 0.088s | 1.0 | 1.04rad |
| retreat | 0.052s ± 0.002s | 2.449s ± 0.127s | 1.0 | 1.03rad |
| transit | 0.073s ± 0.024s | 5.114s ± 1.134s | 1.0 | 4.57rad |
| place_approach | 0.052s ± 0.001s | 2.905s ± 1.614s | 1.0 | 1.88rad |
| place_retreat | 0.053s ± 0.002s | 2.380s ± 0.070s | 1.0 | 1.06rad |



Metrics for src/franka_warehouse_planner/benchmarks/benchmark_default_rrtconnect_small_with_obstacle.json
### Overall Cycle Metrics
- **Success Rate:** 7/10 first-try, 3/10 with retries, 0/10 hard-failed
- **Mean Cycle Time:** 35.04s (std: 4.00s)
- **Sync/Overhead Time:** 10.68s (std: 0.45s)
- **Pick Pos Accuracy Error:** 0.000001m
- **Pick Ori Accuracy Error:** 0.000483rad
- **Place Pos Accuracy Error:** 0.000077m
- **Place Ori Accuracy Error:** 0.000476rad

### Segment Metrics
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 0.055s ± 0.005s | 4.377s ± 2.747s | 1.0 | 3.93rad |
| approach | 0.052s ± 0.001s | 2.439s ± 0.116s | 1.0 | 1.09rad |
| retreat | 0.052s ± 0.002s | 2.493s ± 0.204s | 1.0 | 1.13rad |
| transit | 0.119s ± 0.080s | 9.627s ± 2.033s | 1.3 | 9.54rad |
| place_approach | 0.052s ± 0.002s | 2.563s ± 0.235s | 1.0 | 1.14rad |
| place_retreat | 0.053s ± 0.002s | 2.474s ± 0.157s | 1.0 | 1.12rad |



Metrics for src/franka_warehouse_planner/benchmarks/benchmark_chomp_small_no_obstacle.json
### Overall Cycle Metrics
- **Success Rate:** 1/1 first-try, 0/1 with retries, 0/1 hard-failed
- **Mean Cycle Time:** 54.31s (std: 0.00s)
- **Sync/Overhead Time:** 10.32s (std: 0.00s)
- **Pick Pos Accuracy Error:** 0.000622m
- **Pick Ori Accuracy Error:** 0.001185rad
- **Place Pos Accuracy Error:** 0.000001m
- **Place Ori Accuracy Error:** 0.000486rad

### Segment Metrics
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 11.480s ± 0.000s | 4.005s ± 0.000s | 1.0 | 2.84rad |
| approach | 0.054s ± 0.000s | 4.724s ± 0.000s | 1.0 | 0.92rad |
| retreat | 0.051s ± 0.000s | 3.267s ± 0.000s | 1.0 | 0.92rad |
| transit | 10.487s ± 0.000s | 4.511s ± 0.000s | 1.0 | 2.35rad |
| place_approach | 0.053s ± 0.000s | 2.891s ± 0.000s | 1.0 | 0.88rad |
| place_retreat | 0.051s ± 0.000s | 2.416s ± 0.000s | 1.0 | 0.88rad |



Metrics for src/franka_warehouse_planner/benchmarks/benchmark_chomp_with_obstacle.json
### Overall Cycle Metrics
- **Success Rate:** 0/1 first-try, 0/1 with retries, 1/1 hard-failed

### Segment Metrics
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 24.454s ± 0.000s | 0.000s ± 0.000s | 3.0 | 0.00rad |



