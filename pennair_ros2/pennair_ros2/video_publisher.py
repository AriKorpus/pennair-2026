# Thin ROS wrapper: read the video file, publish one Image per frame.
import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class VideoPublisher(Node):

    def __init__(self):
        super().__init__('video_publisher')
        self.declare_parameter('video', '')
        self.declare_parameter('width', 0)          # 0 = native; 1280 is ~2x faster
        self.width = self.get_parameter('width').value
        self.cap = cv2.VideoCapture(self.get_parameter('video').value)
        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, 'image_raw', qos_profile_sensor_data)
        self.create_timer(1.0 / (self.cap.get(cv2.CAP_PROP_FPS) or 30.0), self.tick)

    def tick(self):
        ok, frame = self.cap.read()
        if not ok:                                  # loop back to the start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.cap.read()
        if not ok:
            return
        if self.width:
            h = round(frame.shape[0] * self.width / frame.shape[1])
            frame = cv2.resize(frame, (self.width, h), interpolation=cv2.INTER_AREA)
        msg = self.bridge.cv2_to_imgmsg(frame, 'bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(VideoPublisher())
    rclpy.shutdown()
