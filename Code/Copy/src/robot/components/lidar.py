"""
    SERS TEAM
    lidar.py
"""

import math
import utils as utilities
from utils import divide_into_chunks
from robot.components.sensor import TimedSensor
from data_models.angle import Angle
from data_models.vectors import Vector2D


class Lidar(TimedSensor):
    def __init__(self, webots_device, time_step, step_counter, layers_used=range(4)):
        super().__init__(webots_device, time_step, step_counter)
        self.x = 0
        self.y = 0
        self.z = 0
        self.orientation = Angle(0)
        
        self.horizontal_fov = self.device.getFov()
        self.vertical_fov = self.device.getVerticalFov()

        self.horizontal_resolution = self.device.getHorizontalResolution()
        self.vertical_resolution = self.device.getNumberOfLayers()

        self.radian_per_detection_horizontally = self.horizontal_fov / self.horizontal_resolution
        self.radian_per_layer_vertically = self.vertical_fov / self.vertical_resolution

        self.rotation_offset = 0

        self.max_detection_distance = 0.06 * 8
        self.min_detection_distance = 0.06 * 0.6

        self.is_point_close = False
        self.is_point_close_threshold = 0.03
        self.is_point_close_range = (0, 360)

        self.distance_bias = 0.005

        self.layers_used = layers_used
        self.__point_cloud = None
        self.__out_of_bounds_point_cloud = None
        self.__distance_detections = None

    def get_point_cloud(self):
        if self.step_counter.check():
            return self.__point_cloud

    def get_out_of_bounds_point_cloud(self):
        if self.step_counter.check():
            return self.__out_of_bounds_point_cloud
        
    def get_detections(self):
        if self.step_counter.check():
            return self.__distance_detections

    def set_orientation(self, angle):
        self.orientation = angle

    def update(self):
        super().update()

        if self.step_counter.check():
            self.__update_point_clouds()


    def __update_point_clouds(self):
        self.is_point_close = False

        self.__point_cloud = []
        self.__out_of_bounds_point_cloud = []
        self.__distance_detections = []

        total_depth_array = self.device.getRangeImage()
        total_depth_array = divide_into_chunks(total_depth_array, self.horizontal_resolution)
        
        for layer_number, layer_depth_array in enumerate(total_depth_array):
            if layer_number not in self.layers_used:
                continue

            vertical_angle = layer_number * self.radian_per_layer_vertically + self.vertical_fov / 2
            horizontal_angle = self.rotation_offset + ((2 * math.pi) - self.orientation.radians)

            for item in layer_depth_array:
                if item >= self.max_detection_distance or item == float("inf") or item == float("inf") *-1:
                    distance = self.__normalize_distance(self.max_detection_distance, vertical_angle)
                    point = utilities.get_coordinates_from_radians(horizontal_angle, distance)
                    self.__out_of_bounds_point_cloud.append(self.__normalize_point(point))

                else:
                    if item >= self.min_detection_distance:
                        distance = self.__normalize_distance(item, vertical_angle)
                        point = utilities.get_coordinates_from_radians(horizontal_angle, distance)
                        self.__point_cloud.append(self.__normalize_point(point))

                        v = Vector2D(Angle(horizontal_angle), distance)
                        v.direction = Angle(math.pi) - v.direction
                        v.direction.normalize()
                        self.__distance_detections.append(v)

                        if self.__in_range_for_close_point(horizontal_angle) and distance < self.is_point_close_threshold:
                            self.is_point_close = True

                horizontal_angle += self.radian_per_detection_horizontally
        
        if len(self.__out_of_bounds_point_cloud) == 0:
            self.__out_of_bounds_point_cloud = [[0, 0]]
        
        if len(self.__point_cloud) == 0:
            self.__point_cloud = [[0, 0]]
    
    def __in_range_for_close_point(self, horizontal_angle):
        return utilities.degrees_to_rads(self.is_point_close_range[0]) > horizontal_angle > utilities.degrees_to_rads(self.is_point_close_range[1])
    
    def __normalize_distance(self, distance, vertical_angle):
        distance = distance * math.cos(vertical_angle)
        distance += self.distance_bias
        return distance

    def __normalize_point(self, point):
            return [point[0], point[1] * -1]
