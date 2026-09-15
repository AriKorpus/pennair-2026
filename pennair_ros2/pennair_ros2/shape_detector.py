# Thin ROS wrapper: hand each frame to algorithm.detect, publish what comes back.
# Positions are meters (REP-103) in the camera optical frame: X right, Y down, Z forward.
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Point, Pose, PoseArray
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray

from pennair_ros2 import algorithm

INCH = 0.0254


class ShapeDetector(Node):

    def __init__(self):
        super().__init__('shape_detector')
        self.bridge = CvBridge()
        self.centers = self.create_publisher(PoseArray, 'centers', 10)
        self.outlines = self.create_publisher(MarkerArray, 'outlines', 10)
        self.annotated = self.create_publisher(Image, 'image_annotated', 10)
        self.create_subscription(Image, 'image_raw', self.on_image, qos_profile_sensor_data)

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        h, w = frame.shape[:2]
        fx, fy = algorithm.focal(w)
        found = algorithm.detect(frame)

        def point(u, v, z):                         # pixel -> meters on the surface plane
            return Point(x=(u - w / 2) * z / fx * INCH,
                         y=(v - h / 2) * z / fy * INCH, z=z * INCH)

        poses = PoseArray(header=msg.header)
        marks = MarkerArray()
        marks.markers.append(Marker(header=msg.header, action=Marker.DELETEALL))
        for i, (outline, (x, y, z)) in enumerate(found):
            pose = Pose()
            pose.position.x, pose.position.y, pose.position.z = x * INCH, y * INCH, z * INCH
            pose.orientation.w = 1.0
            poses.poses.append(pose)

            mark = Marker(header=msg.header, ns='outline', id=i,
                          type=Marker.LINE_STRIP, action=Marker.ADD)
            mark.color.g = mark.color.a = mark.pose.orientation.w = 1.0
            mark.scale.x = 0.01
            mark.points = [point(u, v, z) for u, v in [*outline[:, 0, :], outline[0, 0]]]
            marks.markers.append(mark)

        self.centers.publish(poses)
        self.outlines.publish(marks)
        out = self.bridge.cv2_to_imgmsg(algorithm.draw(frame, found), 'bgr8')
        out.header = msg.header
        self.annotated.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ShapeDetector())
    rclpy.shutdown()
