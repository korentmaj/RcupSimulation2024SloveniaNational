"""
    SERS TEAM
    main.py
"""

from actuator.actuator import Actuator
from mapping.map_controller import Mapper
from robot.robot import Robot


def main():
    robot = Robot(time_step=32)
    mapper = Mapper(tile_size=0.12, robot_diameter=robot.diameter, camera_distance_from_center=robot.diameter/2)
    actuator = Actuator(mapper, robot)
    actuator.run()


main()
