#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty
import os
import sys
import time

class FastDetach(Node):
    def __init__(self):
        super().__init__('fast_detach')
        self.pub = self.create_publisher(Empty, '/box/detach', 10)
        
        # Ensure stale flag file is deleted at startup
        flag_file = '/tmp/stop_early_detach'
        if os.path.exists(flag_file):
            try:
                os.remove(flag_file)
                self.get_logger().info(f'Deleted stale flag file {flag_file}')
            except Exception as e:
                self.get_logger().warn(f'Failed to delete stale flag file {flag_file}: {e}')
                
        self.get_logger().info('Fast detach node started, waiting 2s for Gazebo to load...')
        time.sleep(2.0)
        # Publish at 100Hz using System clock (so it fires even before Gazebo publishes /clock)
        self.timer = self.create_timer(0.01, self.timer_callback, clock=rclpy.clock.Clock(clock_type=rclpy.clock.ClockType.SYSTEM_TIME))
        self.get_logger().info('Spamming /box/detach until flag is found.')

    def timer_callback(self):
        if os.path.exists('/tmp/stop_early_detach'):
            self.get_logger().info('Stop flag /tmp/stop_early_detach found, exiting fast detach node.')
            sys.exit(0)
        self.get_logger().info("Published detach", throttle_duration_sec=1.0)
        self.pub.publish(Empty())

def main(args=None):
    rclpy.init(args=args)
    node = FastDetach()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
