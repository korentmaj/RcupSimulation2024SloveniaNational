"""
    SERS TEAM
    gyroscope.py
"""

from data_models.angle import Angle
from robot.components.sensor import Sensor
import copy


class Gyroscope(Sensor):
    def __init__(self, webots_device, index, time_step):
        super().__init__(webots_device, time_step)
        self.index = index
        self.orientation = Angle(0)
        self.angular_velocity = Angle(0)
        self.previous_angular_velocity = Angle(0)

    def update(self):
        time_elapsed = self.time_step / 1000
        sensor_y_value = self.device.getValues()[self.index]
        self.previous_angular_velocity = copy.copy(self.angular_velocity)
        self.angular_velocity = Angle(sensor_y_value * time_elapsed)
        self.orientation += self.angular_velocity
        self.orientation.normalize()

    def get_angular_velocity(self):
        return abs(self.angular_velocity)

    def get_orientation(self):
        return self.orientation
    
    def set_orientation(self, angle):
        self.orientation = angle
