import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import time

class RobotRosInterface(Node):
    def __init__(self, namespace=''):
        """네임스페이스를 지원하는 ROS2 인터페이스"""
        # Node 생성 시 namespace를 지정하면 모든 토픽/액션에 자동으로 접두어가 붙습니다.
        super().__init__('robot_voice_bridge', namespace=namespace)
        
        self.get_logger().info(f"🤖 ROS2 인터페이스 초기화 (Namespace: '{namespace}')")
        
        # Action 이름 'navigate_to_pose'는 네임스페이스가 있다면 자동으로 '/ns/navigate_to_pose'가 됩니다.
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
            for _ in range(3):
                if self._current_goal_handle == "CANCELLED": return False
                time.sleep(1.0)
            return True
        return True

    def send_move_goal(self, target_name):
        if target_name not in self.location_map:
            self.get_logger().error(f"알 수 없는 장소: {target_name}")
            return False

        # 서버 대기 (네임스페이스가 포함된 경로로 대기함)
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(f"Nav2 서버를 찾을 수 없습니다: {self._nav_client._action_name}")
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
        
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if result_future.done():
                break
            if self._current_goal_handle == "CANCELLED":
                return False
        
        self._current_goal_handle = None
        return True

    def abort_all(self):
        if self._current_goal_handle and self._current_goal_handle != "CANCELLED":
            self.get_logger().warn("🚨 긴급 중단 시퀀스 가동!")
            self._current_goal_handle.cancel_goal_async()
            self._current_goal_handle = "CANCELLED"
            return True
        return False
