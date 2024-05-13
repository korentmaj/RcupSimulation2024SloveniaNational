"""
    SERS TEAM
    gps.py
"""

from data_models.vectors import Position2D
from robot.components.sensor import Sensor


class Gps(Sensor):
    def __init__(self, webots_device, time_step, coords_multiplier=1):
        super().__init__(webots_device, time_step)
        self.multiplier = coords_multiplier
        self.__prev_position = Position2D()
        self.position = self.get_position()

    def update(self):
        self.__prev_position = self.position
        self.position = self.get_position()

    def get_position(self):
        vals = self.device.getValues()
        return Position2D(vals[0] * self.multiplier, vals[2] * self.multiplier)

    def get_orientation(self):
        if self.__prev_position != self.position:
            accuracy = abs(self.position.get_distance_to(self.__prev_position))
            if accuracy > 0.001:
                angle = self.__prev_position.get_angle_to(self.position)
                angle.normalize()
                return angle
        return None
