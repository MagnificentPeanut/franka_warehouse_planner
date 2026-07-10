# Benchmark Results

This document contains the collected performance metrics for different planning pipelines in the Franka warehouse pick-and-place simulation.

---

## 1. Default Planner Baseline (RRTConnect)
**Dataset Date**: 2026-07-09
**Configuration**: Standard `fr3` MoveIt configuration, `geometric::RRTConnect` planner. Software rendering enabled.
**Cycles Tested**: 10 cycles per condition.

### Condition A: No Obstacles
The workspace contains only the robotic arm, the table, the pick location, and the place location.

**Overall Cycle Metrics**
- **Success Rate**: 10/10 first-try (100%), 0/10 with retries, 0/10 hard-failed
- **Mean Cycle Time**: 30.37s (std: 2.24s)
- **Sync/Overhead Time**: 10.40s (std: 0.07s)
- **Pick Pos Accuracy Error**: 0.000311m
- **Pick Ori Accuracy Error**: 0.000740rad
- **Place Pos Accuracy Error**: 0.000318m
- **Place Ori Accuracy Error**: 0.000711rad

**Segment Metrics**
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 0.053s ± 0.002s | 4.380s ± 1.437s | 1.0 | 3.65rad |
| approach | 0.052s ± 0.001s | 2.950s ± 0.552s | 1.0 | 1.06rad |
| retreat | 0.051s ± 0.001s | 2.319s ± 0.128s | 1.0 | 1.03rad |
| transit | 0.068s ± 0.033s | 4.748s ± 1.712s | 1.0 | 4.14rad |
| place_approach | 0.051s ± 0.001s | 2.782s ± 0.567s | 1.0 | 1.08rad |
| place_retreat | 0.052s ± 0.002s | 2.463s ± 0.263s | 1.0 | 1.07rad |

*(Note: The overhead was calculated directly from the recorded data by subtracting the sum of all segment plan + execution times from the total recorded cycle wall-time. This confirms that Segment Total (~19.97s) + Sync/Overhead (~10.40s) ≈ Mean Cycle Time (30.37s).)*

---

### Condition B: With Obstacle (Tall Box)
A tall bounding box is spawned directly between the pick location and the place location, forcing the planner to compute collision-free arcs over or around it.

**Overall Cycle Metrics**
- **Success Rate**: 6/10 first-try (60%), 4/10 with retries (40%), 0/10 hard-failed
- **Mean Cycle Time**: 32.89s (std: 1.74s)
- **Sync/Overhead Time**: 10.70s (std: 0.43s)
- **Pick Pos Accuracy Error**: 0.000315m
- **Pick Ori Accuracy Error**: 0.000659rad
- **Place Pos Accuracy Error**: 0.000312m
- **Place Ori Accuracy Error**: 0.000580rad

**Segment Metrics**
| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 0.052s ± 0.001s | 4.303s ± 1.451s | 1.0 | 4.70rad |
| approach | 0.052s ± 0.002s | 2.623s ± 0.554s | 1.0 | 1.15rad |
| retreat | 0.052s ± 0.002s | 2.215s ± 0.278s | 1.0 | 1.14rad |
| transit | 0.083s ± 0.034s | 7.671s ± 0.957s | 1.4 | 9.48rad |
| place_approach | 0.052s ± 0.002s | 2.698s ± 0.554s | 1.0 | 1.09rad |
| place_retreat | 0.052s ± 0.001s | 2.339s ± 0.277s | 1.0 | 1.08rad |

*(Note: The overhead was calculated directly from the recorded data by subtracting the sum of all segment plan + execution times from the total recorded cycle wall-time. This confirms that Segment Total (~22.19s) + Sync/Overhead (~10.70s) ≈ Mean Cycle Time (32.89s).)*

---
## Summary of Findings (RRTConnect)
- **Obstacle Impact**: The presence of the obstacle significantly impacted the `transit` segment (moving from pick to place). 
    - The path length increased from ~4.14 rad to ~9.48 rad.
    - First-try success dropped to 60%, with the planner needing ~1.4 attempts on average to find a valid trajectory for the transit segment.
- **Speed**: RRTConnect solves planning extremely fast (~0.05s - 0.09s), but the resulting trajectories are long and complex (joint space variations up to 9.5 rad) leading to execution times taking multiple seconds.
- **Accuracy**: Final pick and place positional accuracies were excellent (< 0.5 mm error), primarily due to Cartesian path solving for the approach segments instead of OMPL.

---

# Phase 5: CHOMP Integration

## Benchmark Configuration
- **Total Cycles per Condition**: 10
- **Hardware Profile**: Default simulated parameters, Franka Emika FR3.
- **Controller**: `fr3_arm_controller` (JointTrajectoryController)
- **Planner**: `CHOMP`
- **Pick/Place Logic**: Same standard state machine, using `/compute_ik` to convert Cartesian Pose goals into Joint State goals for CHOMP.

---

### Condition A: No Obstacle (Default Scene)

**Overall Cycle Metrics**
- **Success Rate**: 8/10 first-try (80%), 0/10 with retries (0%), 2/10 hard-failed (20%)
- **Mean Cycle Time**: 37.37s (std: 1.78s)
- **Sync/Overhead Time**: 10.00s (std: 0.11s)
- **Pick Pos Accuracy Error**: 0.000313m
- **Pick Ori Accuracy Error**: 0.000843rad
- **Place Pos Accuracy Error**: 0.000302m
- **Place Ori Accuracy Error**: 0.000732rad

**Segment Metrics**

| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 9.701s ± 5.940s | 0.387s ± 0.919s | 1.4 | 0.28rad |
| approach | 0.052s ± 0.001s | 2.640s ± 0.596s | 1.0 | 0.90rad |
| retreat | 0.053s ± 0.002s | 2.082s ± 0.097s | 1.0 | 0.90rad |
| transit | 6.844s ± 0.338s | 3.433s ± 0.062s | 1.0 | 2.35rad |
| place_approach | 0.052s ± 0.001s | 2.646s ± 0.603s | 1.0 | 0.90rad |
| place_retreat | 0.051s ± 0.001s | 2.294s ± 0.239s | 1.0 | 0.91rad |

*(Note: The overhead was calculated directly from the recorded data by subtracting the sum of all segment plan + execution times from the total recorded cycle wall-time. This confirms that Segment Total (~27.37s) + Sync/Overhead (~10.00s) ≈ Mean Cycle Time (37.37s).)*

---

### Condition B: With Obstacle (Tall Box)

**Overall Cycle Metrics**
- **Success Rate**: 0/10 first-try (0%), 0/10 with retries (0%), 10/10 hard-failed (100%)

**Segment Metrics**

| Segment | Plan Time (Mean±Std) | Exec Time (Mean±Std) | Attempts (Mean) | Path Length (Mean, rad) |
|---------|----------------------|----------------------|-----------------|-------------------------|
| pre_grasp | 23.445s ± 0.792s | 0.000s ± 0.000s | 3.0 | 0.00rad |

---
## Summary of Findings (CHOMP)
- **Obstacle Impact**: CHOMP failed completely in the presence of the obstacle. N=10 out of 10 cycles failed during the `pre_grasp` phase, unable to resolve collision-free joint-space goals within the configured parameters or compute IK solutions that CHOMP could utilize around the obstacle.
- **Performance**: Compared to RRTConnect, CHOMP had significantly higher planning times in the unoccluded scenario (`pre_grasp` took ~9.7s compared to RRTConnect's ~0.05s).
