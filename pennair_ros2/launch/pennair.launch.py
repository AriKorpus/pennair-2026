from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('video', description='absolute path to the input video'),
        DeclareLaunchArgument('width', default_value='0',
                              description='downscale width; 0 keeps native, 1280 is ~2x faster'),
        Node(package='pennair_ros2', executable='video_publisher', output='screen',
             parameters=[{'video': LaunchConfiguration('video'),
                          'width': LaunchConfiguration('width')}]),
        Node(package='pennair_ros2', executable='shape_detector', output='screen'),
    ])
