# Shows /image_annotated in a window. Proves the detector's output topic is live.
import rclpy
import cv2
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class Viewer(Node):
    def __init__(self):
        super().__init__('viewer')
        self.bridge = CvBridge()
        self.create_subscription(Image, 'image_annotated', self.on_image, qos_profile_sensor_data)

    def on_image(self, msg):
        cv2.imshow('detections', self.bridge.imgmsg_to_cv2(msg, 'bgr8'))
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(Viewer())
    rclpy.shutdown()
