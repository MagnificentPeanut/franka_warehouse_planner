#!/usr/bin/env python3

import os
import sys
import yaml
import time
import json
import math
import statistics
import tf2_ros
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup

from std_msgs.msg import Empty
from geometry_msgs.msg import Pose, PoseStamped, Point
from shape_msgs.msg import SolidPrimitive
from moveit_msgs.srv import GetMotionPlan, GetCartesianPath, GetPlanningScene, GetStateValidity, GetPositionIK
from moveit_msgs.action import ExecuteTrajectory
from moveit_msgs.msg import (
    MotionPlanRequest, WorkspaceParameters, Constraints, PositionConstraint,
    OrientationConstraint, BoundingVolume, PlanningScene, AttachedCollisionObject,
    CollisionObject, AllowedCollisionMatrix, AllowedCollisionEntry,
    PositionIKRequest, JointConstraint
)
from control_msgs.action import FollowJointTrajectory


class PickPlaceNodeChomp(Node):
    def __init__(self):
        super().__init__('pick_place_node_chomp')

        self.world = self.declare_parameter('world', 'small').value
        self.cycles = self.declare_parameter('cycles', 10).value
        self.with_obstacle = self.declare_parameter('with_obstacle', False).value
        config_path = self.declare_parameter('config', '').value

        if not config_path:
            self.get_logger().error('Config path missing')
            sys.exit(1)

        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)

        self.box_cfg = self.cfg['worlds'][self.world]
        self.box_size = self.box_cfg['box_size']
        self.box_start_xy = self.box_cfg['box_xy']
        self.box_cfg = self.cfg['worlds'][self.world]
        self.get_logger().info(f"USING BOX CONFIG FOR WORLD '{self.world}': {self.box_cfg}")
        self.pick_target_xy = self.cfg.get('pick_target_xy', [0.45, -0.3])
        self.table = self.cfg['table']
        self.place_target_xy = self.cfg.get('place_target_xy', [0.45, 0.3])

        # Link names
        self.planning_frame = 'fr3_link0'
        self.arm_group = 'fr3_arm'
        self.tip_link = 'fr3_cobot_pump_tcp'
        self.collision_link = 'fr3_cobot_pump'

        # Publishers
        self.attach_pub = self.create_publisher(Empty, '/box/attach', 10)
        self.detach_pub = self.create_publisher(Empty, '/box/detach', 10)
        self.scene_pub = self.create_publisher(
            PlanningScene, 'planning_scene', 10)

        self.get_scene_srv = self.create_client(
            GetPlanningScene, 'get_planning_scene')
        self.validity_srv = self.create_client(
            GetStateValidity, 'check_state_validity')
        while not self.get_scene_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for get_planning_scene service...')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        cb_group = MutuallyExclusiveCallbackGroup()

        # Services & Actions
        self.plan_srv = self.create_client(
            GetMotionPlan, '/plan_kinematic_path', callback_group=cb_group)
        self.cartesian_srv = self.create_client(
            GetCartesianPath, '/compute_cartesian_path', callback_group=cb_group)
        self.ik_srv = self.create_client(
            GetPositionIK, '/compute_ik', callback_group=cb_group)
        self.exec_action = ActionClient(
            self, ExecuteTrajectory, '/execute_trajectory', callback_group=cb_group)

        self.wait_for_services()

        # Stats
        self.metrics = []

    def get_sim_time(self):
        return self.get_clock().now().nanoseconds / 1e9

    def wait_for_services(self):
        self.get_logger().info('Waiting for MoveIt services...')
        while not self.plan_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('plan_srv not available, waiting...')
        while not self.cartesian_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('cartesian_srv not available, waiting...')
        while not self.validity_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('validity_srv not available, waiting...')
        while not self.get_scene_srv.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('get_planning_scene not available, waiting...')
        while not self.exec_action.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('exec_action not available, waiting...')
        self.get_logger().info('All MoveIt services ready!')

        # Clear any lingering attached objects from previous aborted runs
        self.get_logger().info('Clearing scene state and waiting 5 seconds before starting...')
        self.detach_pub.publish(Empty())
        self.update_box_pose("detach", self.box_start_xy, self.box_size[2]/2.0)
        
        if self.with_obstacle:
            self.spawn_obstacle()
            
        time.sleep(5.0)

    def _get_pose(self, x, y, z):
        p = PoseStamped()
        p.header.frame_id = self.planning_frame
        p.pose.position.x = float(x)
        p.pose.position.y = float(y)
        p.pose.position.z = float(z)
        p.pose.orientation.x = 1.0  # Pointing straight down in base frame
        p.pose.orientation.y = 0.0
        p.pose.orientation.z = 0.0
        p.pose.orientation.w = 0.0
        return p

    def plan_to_pose(self, target_pose):
        req = GetMotionPlan.Request()
        req.motion_plan_request.group_name = self.arm_group
        req.motion_plan_request.start_state.is_diff = True
        req.motion_plan_request.workspace_parameters.header.frame_id = self.planning_frame
        req.motion_plan_request.workspace_parameters.min_corner.x = -1.0
        req.motion_plan_request.workspace_parameters.min_corner.y = -1.0
        req.motion_plan_request.workspace_parameters.min_corner.z = -1.0
        req.motion_plan_request.workspace_parameters.max_corner.x = 1.0
        req.motion_plan_request.workspace_parameters.max_corner.y = 1.0
        req.motion_plan_request.workspace_parameters.max_corner.z = 2.0
        req.motion_plan_request.planner_id = 'CHOMP'

        # Compute IK first to get a joint state goal, since CHOMP needs joint space goals
        ik_req = GetPositionIK.Request()
        ik_req.ik_request.group_name = self.arm_group
        ik_req.ik_request.robot_state.is_diff = True
        ik_req.ik_request.avoid_collisions = True
        ik_req.ik_request.pose_stamped = target_pose
        ik_req.ik_request.timeout.sec = 2

        if not self.ik_srv.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("IK service not available")
            return None

        ik_res = self.ik_srv.call(ik_req)
        if ik_res.error_code.val != 1:
            self.get_logger().error(f"IK failed with error code {ik_res.error_code.val}")
            return None

        # Create JointConstraints from IK solution
        c = Constraints()
        joint_names = ik_res.solution.joint_state.name
        joint_positions = ik_res.solution.joint_state.position
        
        for name, pos in zip(joint_names, joint_positions):
            if name.startswith('fr3_joint'):
                jc = JointConstraint()
                jc.joint_name = name
                jc.position = pos
                jc.tolerance_above = 0.01
                jc.tolerance_below = 0.01
                jc.weight = 1.0
                c.joint_constraints.append(jc)

        req.motion_plan_request.goal_constraints.append(c)
        req.motion_plan_request.allowed_planning_time = 5.0
        req.motion_plan_request.max_velocity_scaling_factor = 0.5
        req.motion_plan_request.max_acceleration_scaling_factor = 0.5

        t0 = time.time()
        future = self.plan_srv.call_async(req)
        timeout_t = self.get_sim_time() + 10.0
        while not future.done():
            if self.get_sim_time() > timeout_t:
                self.get_logger().error("plan_srv timeout!")
                return None, 0.0
            time.sleep(0.05)
        res = future.result()
        t1 = time.time()
        plan_duration = t1 - t0
        self.get_logger().info(f"[plan_to_pose] Raw start: {t0:.4f}, Raw end: {t1:.4f}, Duration: {plan_duration:.4f}")

        if res and res.motion_plan_response.error_code.val == 1:  # SUCCESS
            return res.motion_plan_response.trajectory, plan_duration
        else:
            code = res.motion_plan_response.error_code.val if res else 'None'
        self.get_logger().error(f"Planning failed with code {code}")
        return None, plan_duration

    def plan_cartesian(self, target_pose):
        req = GetCartesianPath.Request()
        req.header.frame_id = self.planning_frame
        req.start_state.is_diff = True
        req.group_name = self.arm_group
        req.link_name = self.tip_link
        req.waypoints.append(target_pose.pose)
        req.max_step = 0.01
        req.jump_threshold = 0.0
        req.avoid_collisions = False  # Ignore collisions for the final 15cm approach/retreat

        t0 = time.time()
        future = self.cartesian_srv.call_async(req)
        timeout_t = self.get_sim_time() + 10.0
        while not future.done():
            if self.get_sim_time() > timeout_t:
                self.get_logger().error("cartesian_srv timeout!")
                return None, 0.0
            time.sleep(0.05)
        res = future.result()
        t1 = time.time()
        plan_duration = t1 - t0
        self.get_logger().info(f"[plan_cartesian] Raw start: {t0:.4f}, Raw end: {t1:.4f}, Duration: {plan_duration:.4f}")

        if res and res.fraction >= 0.999:
            return res.solution, plan_duration
        else:
            frac = res.fraction if res else 'None'
        self.get_logger().error(f"Cartesian planning incomplete: {frac}")
        return None, plan_duration

    def execute_trajectory(self, trajectory):
        goal = ExecuteTrajectory.Goal()
        goal.trajectory = trajectory
        self.exec_action.wait_for_server()
        future = self.exec_action.send_goal_async(goal)
        timeout_t = self.get_sim_time() + 5.0
        while not future.done():
            if self.get_sim_time() > timeout_t:
                self.get_logger().error("exec_action send_goal timeout!")
                return False
            time.sleep(0.05)
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Execution goal rejected")
            return False
        res_future = goal_handle.get_result_async()
        timeout_t = self.get_sim_time() + 30.0
        while not res_future.done():
            if self.get_sim_time() > timeout_t:
                self.get_logger().error("execution timeout!")
                return False
            time.sleep(0.05)
        res = res_future.result().result
        error_code = res.error_code.val
        if error_code != 1:
            self.get_logger().error(f"execute_trajectory failed with error code: {error_code}")
        return error_code == 1

    def set_acm(self, allow_collision):
        req = GetPlanningScene.Request()
        req.components.components = req.components.ALLOWED_COLLISION_MATRIX
        future = self.get_scene_srv.call_async(req)
        while not future.done():
            time.sleep(0.05)
        res = future.result()

        acm = res.scene.allowed_collision_matrix

        # We need to add or update the exception between self.collision_link and 'box'
        if self.collision_link not in acm.entry_names:
            acm.entry_names.append(self.collision_link)
            new_entry = AllowedCollisionEntry()
            # Must have the same length as entry_names!
            new_entry.enabled = [False] * len(acm.entry_names)
            acm.entry_values.append(new_entry)

            # Pad all existing entries with False for the new row/column
            for entry in acm.entry_values[:-1]:
                entry.enabled.append(False)

        if 'box' not in acm.entry_names:
            acm.entry_names.append('box')
            new_entry = AllowedCollisionEntry()
            new_entry.enabled = [False] * len(acm.entry_names)
            acm.entry_values.append(new_entry)
            for entry in acm.entry_values[:-1]:
                entry.enabled.append(False)

        if 'table' not in acm.entry_names:
            acm.entry_names.append('table')
            new_entry = AllowedCollisionEntry()
            new_entry.enabled = [False] * len(acm.entry_names)
            acm.entry_values.append(new_entry)
            for entry in acm.entry_values[:-1]:
                entry.enabled.append(False)

        # Set the matrix value
        idx1 = acm.entry_names.index(self.collision_link)
        idx2 = acm.entry_names.index('box')
        idx_table = acm.entry_names.index('table')

        acm.entry_values[idx1].enabled[idx2] = allow_collision
        acm.entry_values[idx2].enabled[idx1] = allow_collision

        acm.entry_values[idx2].enabled[idx_table] = allow_collision
        acm.entry_values[idx_table].enabled[idx2] = allow_collision

        scene = PlanningScene()
        scene.is_diff = True
        scene.allowed_collision_matrix = acm
        self.scene_pub.publish(scene)
        time.sleep(0.5)

    def spawn_obstacle(self):
        scene = PlanningScene()
        scene.is_diff = True
        
        obs = CollisionObject()
        obs.header.frame_id = self.planning_frame
        obs.id = 'part3_obstacle'
        obs.operation = CollisionObject.ADD
        
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [0.1, 0.1, 0.55]
        obs.primitives.append(primitive)
        
        p = Pose()
        p.position.x = 0.45
        p.position.y = 0.0
        p.position.z = 0.275
        p.orientation.w = 1.0
        obs.primitive_poses.append(p)
        
        scene.world.collision_objects.append(obs)
        self.scene_pub.publish(scene)
        self.get_logger().info("Spawned Part 3 collision obstacle")
        time.sleep(0.5)

    def update_box_pose(self, action, current_xy, z_height):
        scene = PlanningScene()
        scene.is_diff = True
        scene.robot_state.is_diff = True

        box = CollisionObject()
        box.header.frame_id = self.planning_frame
        box.id = 'box'

        if action == "attach":
            # Remove from world
            box.operation = CollisionObject.REMOVE
            scene.world.collision_objects.append(box)

            # Attach to robot
            aco = AttachedCollisionObject()
            aco.link_name = self.collision_link
            aco.object.id = 'box'
            aco.object.operation = CollisionObject.ADD

            # touch_links: links physically allowed to contact the attached object.
            # Without this, MoveIt detects a self-collision between the box and
            # fr3_cobot_pump (the attachment link), which makes the post-grasp
            # start state invalid and blocks all subsequent planning.
            aco.touch_links = [
                'fr3_cobot_pump',
                'fr3_cobot_pump_tcp',
                'fr3_link8',
                'fr3_link7',
            ]
            scene.robot_state.attached_collision_objects.append(aco)
            self.scene_pub.publish(scene)
            # Wait longer after attach so MoveIt's planning scene integrates the
            # attached object and touch_links before the next planning call.
            time.sleep(1.5)
            # early return; don't fall through to the general sleep(0.5) below
            return

        elif action == "detach":
            # Detach from robot
            aco = AttachedCollisionObject()
            aco.link_name = self.collision_link
            aco.object.id = 'box'
            aco.object.operation = CollisionObject.REMOVE
            scene.robot_state.attached_collision_objects.append(aco)
            
            # Add back to world at new pose
            box.operation = CollisionObject.ADD
            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.BOX
            primitive.dimensions = [self.box_size[0],
                                    self.box_size[1], self.box_size[2]]
            box.primitives.append(primitive)
    
            p = Pose()
            p.position.x = float(current_xy[0])
            p.position.y = float(current_xy[1])
            p.position.z = float(z_height)
            p.orientation.w = 1.0
            
            box.primitive_poses.append(p)
            scene.world.collision_objects.append(box)
    
            self.scene_pub.publish(scene)
            time.sleep(0.5)
    
    def _get_box_pose_from_scene(self):
        req = GetPlanningScene.Request()
        req.components.components = req.components.WORLD_OBJECT_GEOMETRY | req.components.ROBOT_STATE_ATTACHED_OBJECTS
        future = self.get_scene_srv.call_async(req)
        timeout_t = self.get_sim_time() + 5.0
        while not future.done():
            if self.get_sim_time() > timeout_t:
                return None
            time.sleep(0.05)
        res = future.result()
        for obj in res.scene.world.collision_objects:
            if obj.id == 'box' and len(obj.primitive_poses) > 0:
                p = obj.primitive_poses[0]
                return [p.position.x, p.position.y, p.position.z, p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w]
        for attached in res.scene.robot_state.attached_collision_objects:
            if attached.object.id == 'box':
                return "ATTACHED"
        return None

    def _analyze_trajectory(self, traj, is_cartesian):
        pts = traj.joint_trajectory.points
        waypoints = len(pts)
        if waypoints < 2:
            return {"path_length": 0.0, "waypoints": waypoints, "vel_variance": 0.0, "collision_free": True}
    
        path_length = 0.0
        velocities = []
        for i in range(1, waypoints):
            diff = [abs(pts[i].positions[j] - pts[i-1].positions[j])
                for j in range(len(pts[i].positions))]
            path_length += sum(diff)
    
        for pt in pts:
            if pt.velocities:
                avg_vel = sum([abs(v) for v in pt.velocities]) / len(pt.velocities)
                velocities.append(avg_vel)
    
        vel_var = 0.0
        if len(velocities) > 1:
            vel_var = statistics.variance(velocities)
    
        collision_free = True
        sample_indices = set(range(0, waypoints, max(1, waypoints // 5)))
        sample_indices.add(waypoints - 1)
        for idx in sample_indices:
            req = GetStateValidity.Request()
            req.robot_state.joint_state.name = traj.joint_trajectory.joint_names
            req.robot_state.joint_state.position = pts[idx].positions
            req.group_name = self.arm_group
            future = self.validity_srv.call_async(req)
            timeout = self.get_sim_time() + 2.0
            while not future.done():
                if self.get_sim_time() > timeout:
                    break
                time.sleep(0.05)
            if future.done():
                res = future.result()
                if not res.valid:
                    collision_free = False
                    break
    
        return {
            "path_length": path_length,
            "waypoints": waypoints,
            "vel_variance": vel_var,
            "collision_free": collision_free
        }
    
    def _verify_accuracy(self, target_xy, target_z):
        try:
            trans = self.tf_buffer.lookup_transform(
                'fr3_link0', 'fr3_cobot_pump_tcp',
                rclpy.time.Time(), timeout=rclpy.duration.Duration(seconds=2.0)
            )
            dist = math.sqrt(
                (trans.transform.translation.x - target_xy[0])**2 +
                (trans.transform.translation.y - target_xy[1])**2 +
                (trans.transform.translation.z - target_z)**2
            )
            q_target = [1.0, 0.0, 0.0, 0.0]
            q_tcp = [
                trans.transform.rotation.x,
                trans.transform.rotation.y,
                trans.transform.rotation.z,
                trans.transform.rotation.w
            ]
            dot = sum(x*y for x, y in zip(q_target, q_tcp))
            dot = max(-1.0, min(1.0, dot))
            ori_dist = 2 * math.acos(abs(dot))
            return {"pos_error": dist, "ori_error": ori_dist}
        except Exception as e:
            self.get_logger().error(f"TF verification failed: {e}")
            return {"pos_error": -1.0, "ori_error": -1.0}
    
    def run_cycle(self):
        hover_height = self.box_size[2] + 0.15
        grasp_height = self.box_size[2] + 0.005
    
        locs = [self.box_start_xy, self.place_target_xy]
        current_loc_idx = 0
    
        def execute_segment(name, plan_func, target_pose, max_retries=3, is_cartesian=False):
            segment_data = {"name": name, "attempts": 0,
                            "success": False, "hard_failure": False, "plan_time": 0.0,
                            "exec_time": 0.0, "wait_time": 0.0}
            for r in range(max_retries):
                segment_data["attempts"] = r + 1
                traj, p_time = plan_func(target_pose)
                segment_data["plan_time"] += p_time
                
                if traj:
                    analysis = self._analyze_trajectory(traj, is_cartesian)
                    segment_data.update(analysis)
                    
                    exec_t0 = time.time()
                    success = self.execute_trajectory(traj)
                    exec_t1 = time.time()
                    
                    if success:
                        segment_data["success"] = True
                        segment_data["exec_time"] += (exec_t1 - exec_t0)
                        # Allow robot to physically settle before next plan to avoid
                        # "start point deviates from current robot state" errors
                        time.sleep(0.5)
                        segment_data["wait_time"] += 0.5
                        return segment_data
                    else:
                        segment_data["exec_time"] += (exec_t1 - exec_t0)
                self.get_logger().warn(
                    f"[{name}] Failed, retrying ({r+1}/{max_retries})...")
                time.sleep(1.0)
                segment_data["wait_time"] += 1.0
            
            segment_data["hard_failure"] = True
            return segment_data
    
        for i in range(self.cycles):
            self.get_logger().info(f"--- Cycle {i+1} ---")
            cycle_start = self.get_sim_time()
            cycle_wall_start = time.time()
            cycle_metrics = {"cycle": i+1, "segments": {},
                             "poses": {}, "accuracy": {}, "overhead_wait_time": 0.0}
            # 1. PRE-GRASP
            target_xy = locs[current_loc_idx]
            pre_grasp = self._get_pose(target_xy[0], target_xy[1], hover_height)
            seg_res = execute_segment("pre_grasp", self.plan_to_pose, pre_grasp)
            cycle_metrics["segments"]["pre_grasp"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            # 2. APPROACH
            grasp = self._get_pose(target_xy[0], target_xy[1], grasp_height)
            self.set_acm(True)
            seg_res = execute_segment(
            "approach", self.plan_cartesian, grasp, is_cartesian=True)
            cycle_metrics["segments"]["approach"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            cycle_metrics["accuracy"]["pick"] = self._verify_accuracy(
            target_xy, grasp_height)
    
            # 3. ATTACH
            self.attach_pub.publish(Empty())
            self.update_box_pose("attach", target_xy, grasp_height)
            self.get_logger().info("Attached box")
            time.sleep(0.5)
            cycle_metrics["overhead_wait_time"] += 2.0  # 1.5 in attach + 0.5 here
            cycle_metrics["poses"]["post_attach"] = self._get_box_pose_from_scene()
    
            # 4. RETREAT
            seg_res = execute_segment(
            "retreat", self.plan_cartesian, pre_grasp, is_cartesian=True)
            cycle_metrics["segments"]["retreat"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            self.set_acm(False)
    
            # Update targets for place
            current_loc_idx = 1 - current_loc_idx
            target_xy = locs[current_loc_idx]
    
            # 5. TRANSIT
            pre_place = self._get_pose(target_xy[0], target_xy[1], hover_height)
            seg_res = execute_segment("transit", self.plan_to_pose, pre_place)
            cycle_metrics["segments"]["transit"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            # 6. PLACE APPROACH
            place = self._get_pose(target_xy[0], target_xy[1], grasp_height)
            self.set_acm(True)
            seg_res = execute_segment(
            "place_approach", self.plan_cartesian, place, is_cartesian=True)
            cycle_metrics["segments"]["place_approach"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            cycle_metrics["accuracy"]["place"] = self._verify_accuracy(
            target_xy, grasp_height)
    
            # 7. DETACH
            self.detach_pub.publish(Empty())
            self.update_box_pose("detach", target_xy, self.box_size[2]/2.0)
            self.get_logger().info("Detached box")
            time.sleep(0.5)
            cycle_metrics["overhead_wait_time"] += 1.0  # 0.5 in detach + 0.5 here
            cycle_metrics["poses"]["post_detach"] = self._get_box_pose_from_scene()
    
            # 8. RETREAT
            seg_res = execute_segment(
            "place_retreat", self.plan_cartesian, pre_place, is_cartesian=True)
            cycle_metrics["segments"]["place_retreat"] = seg_res
            if not seg_res["success"]:
                self.metrics.append(cycle_metrics)
                continue
    
            self.set_acm(False)
            cycle_metrics["cycle_time"] = self.get_sim_time() - cycle_start
            cycle_metrics["cycle_wall_time"] = time.time() - cycle_wall_start
            self.metrics.append(cycle_metrics)
    
        # Log metrics
        obs_str = "with_obstacle" if self.with_obstacle else "no_obstacle"
        filename = f"src/franka_warehouse_planner/benchmarks/benchmark_chomp_{self.world}_{obs_str}.json"
        
        with open(filename, "w") as f:
            json.dump(self.metrics, f, indent=4)
        self.get_logger().info(f"Saved metrics to {filename}")
    
    
def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNodeChomp()

    import threading
    t = threading.Thread(target=node.run_cycle)
    t.start()

    rclpy.spin(node)

    t.join()
    node.destroy_node()
    rclpy.shutdown()
    
    
if __name__ == '__main__':
    main()
