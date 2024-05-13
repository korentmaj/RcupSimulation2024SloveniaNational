"""
    SERS TEAM
    robot.py
"""

from controller import Robot as WebotsRobot
from flow.stepper import Stepper
from data_models.angle import Angle
from data_models.vectors import Position2D, Vector2D
from robot.components.wheel import Wheel
from robot.components.camera import Camera
from robot.components.lidar import Lidar
from robot.components.gps import Gps
from robot.components.gyroscope import Gyroscope
from robot.components.communicator import Communicator
from robot.pose_controller import PoseManager
from robot.drive_base import DriveBase, Criteria


class Robot:
    def __init__(self, time_step):
        self.time_step = time_step
        self.__start_time = 0
        self.__time = 0

        self.diameter = 0.074
        self.robot = WebotsRobot()

        self.gps = Gps(self.robot.getDevice("gps"), self.time_step)
        self.gyroscope = Gyroscope(self.robot.getDevice("gyro"), 1, self.time_step)
        self.pose_manager = PoseManager(self.gps, self.gyroscope)

        lidar_interval = 6
        self.lidar = Lidar(webots_device=self.robot.getDevice("lidar"),
                           time_step=self.time_step * lidar_interval,
                           step_counter=Stepper(lidar_interval),
                           layers_used=(2,))

        self.camera_distance_from_center = 0.0310
        camera_interval = 3
        self.center_camera = Camera(webots_device=self.robot.getDevice("camera1"),
                                    time_step=self.time_step * camera_interval,
                                    step_counter=Stepper(camera_interval),
                                    orientation=Angle(0, Angle.DEGREES),
                                    distance_from_center=self.camera_distance_from_center)
        
        self.right_camera = Camera(webots_device=self.robot.getDevice("camera2"),
                                   time_step=self.time_step * camera_interval,
                                   step_counter=Stepper(camera_interval),
                                   orientation=Angle(270, Angle.DEGREES),
                                   distance_from_center=self.camera_distance_from_center)
        
        self.left_camera = Camera(webots_device=self.robot.getDevice("camera3"),
                                  time_step=self.time_step * camera_interval,
                                  step_counter=Stepper(camera_interval),
                                  orientation=Angle(90, Angle.DEGREES),
                                  distance_from_center=self.camera_distance_from_center,
                                  rotate180=True)

        self.communicator = Communicator(self.robot.getDevice("emitter"), self.robot.getDevice("receiver"), self.time_step)
        max_wheel_speed = 6.28
        self.drive_base = DriveBase(left_wheel=Wheel(self.robot.getDevice("wheel1 motor"), max_wheel_speed),
                                    right_wheel=Wheel(self.robot.getDevice("wheel2 motor"), max_wheel_speed),
                                    max_wheel_velocity=max_wheel_speed)

    def update(self):
        self.__time = self.robot.getTime()
        self.pose_manager.update(self.drive_base.get_wheel_average_angular_velocity(), 
                                 self.drive_base.get_wheel_velocity_difference())

        self.drive_base.orientation = self.orientation
        self.drive_base.position = self.position
        self.lidar.set_orientation(self.orientation)
        self.lidar.update()
        self.right_camera.update(self.orientation)
        self.left_camera.update(self.orientation)
        self.center_camera.update(self.orientation)

    def do_loop(self):
        return self.robot.step(self.time_step) != -1
    
    def set_start_time(self):
        self.__start_time = self.robot.getTime()

    @property
    def time(self):
        return self.__time - self.__start_time

    @property
    def max_wheel_speed(self):
        return self.drive_base.max_wheel_velocity

    def move_wheels(self, left_ratio, right_ratio):
        self.drive_base.move_wheels(left_ratio, right_ratio)

    def rotate_to_angle(self, angle, direction=Criteria.CLOSEST):
        return self.drive_base.rotate_to_angle(Angle(angle, Angle.DEGREES), direction)
    
    def rotate_slowly_to_angle(self, angle, direction=Criteria.CLOSEST):
        return self.drive_base.rotate_slowly_to_angle(angle, direction)

    def move_to_coords(self, target_pos):
        return self.drive_base.move_to_position(Position2D(target_pos[0], target_pos[1]))

    @property
    def point_is_close(self) -> bool:
        return self.lidar.is_point_close

    def get_point_cloud(self):
        return self.lidar.get_point_cloud()

    def get_out_of_bounds_point_cloud(self):
        return self.lidar.get_out_of_bounds_point_cloud()

    def get_lidar_detections(self):
        return self.lidar.get_detections()

    def get_camera_images(self):
        if self.center_camera.step_counter.check():
            return [self.right_camera.get_image(), 
                    self.center_camera.get_image(), 
                    self.left_camera.get_image()]
        
    def get_last_camera_images(self):
        return [self.right_camera.get_last_image(),
                self.center_camera.get_last_image(),
                self.left_camera.get_last_image()]

    @property
    def position(self):
        return self.pose_manager.position
    
    @property
    def raw_position(self):
        return self.pose_manager.raw_position
    
    @property
    def previous_position(self):
        return self.pose_manager.previous_position
    
    @property
    def position_offsets(self):
        return self.pose_manager.position_offsets
    
    @position_offsets.setter
    def position_offsets(self, value):
        self.pose_manager.position_offsets = value
    
    @property
    def orientation(self):
        return self.pose_manager.orientation
    
    @property
    def previous_orientation(self):
        return self.pose_manager.previous_orientation
    
    @property
    def auto_decide_orientation_sensor(self):
        return self.pose_manager.automatically_decide_orientation_sensor
    
    @auto_decide_orientation_sensor.setter
    def auto_decide_orientation_sensor(self, value):
        self.pose_manager.automatically_decide_orientation_sensor = value

    @property
    def orientation_sensor(self):
        return self.pose_manager.orientation_sensor
    
    @orientation_sensor.setter
    def orientation_sensor(self, value):
        self.pose_manager.orientation_sensor = value
    
    @property
    def GPS(self):
        return PoseManager.GPS
    
    @property
    def GYROSCOPE(self):
        return PoseManager.GYROSCOPE

    def is_shaky(self):
        return self.pose_manager.is_shaky()
    