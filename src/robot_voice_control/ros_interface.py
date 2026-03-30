import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import time

class RobotRosInterface(Node):
    def __init__(self):
        super().__init__('robot_voice_bridge')
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._current_goal_handle = None
        self.location_map = {
            "거실": [1.0, 2.0, 0.0],
            "주방": [3.5, -1.0, 0.0],
            "침실": [-2.0, 1.5, 0.0]
        }

    def execute_command(self, command):
        action = command.get("action")
        self.get_logger().info(f"실행 시작: {action}")

        if action == "move_to":
            return self.send_move_goal(command.get("target"))
        elif action in ["pick", "place"]:
            # 팔 동작 중에도 취소 체크를 위해 1초씩 나눠서 대기 시뮬레이션
            for _ in range(3):
                if self._current_goal_handle == "CANCELLED": return False
                time.sleep(1.0)
            return True
        return True

    def send_move_goal(self, target_name):
        if target_name not in self.location_map:
            return False

        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            return False

        coords = self.location_map[target_name]
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.pose.position.x = float(coords[0])
        goal_msg.pose.pose.position.y = float(coords[1])
        goal_msg.pose.pose.orientation.w = 1.0

        send_goal_future = self._nav_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future)
        
        self._current_goal_handle = send_goal_future.result()
        if not self._current_goal_handle.accepted:
            return False

        result_future = self._current_goal_handle.get_result_async()
        
        # 결과가 나올 때까지 기다리면서 중단 요청이 있는지 체크
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if result_future.done():
                break
            if self._current_goal_handle == "CANCELLED":
                return False
        
        self._current_goal_handle = None
        return True

    def abort_all(self):
        """외부에서 긴급 중단 명령을 내릴 때 호출"""
        if self._current_goal_handle and self._current_goal_handle != "CANCELLED":
            self.get_logger().warn("🚨 긴급 중단 시퀀스 가동!")
            self._current_goal_handle.cancel_goal_async()
            self._current_goal_handle = "CANCELLED"
            return True
        return False
