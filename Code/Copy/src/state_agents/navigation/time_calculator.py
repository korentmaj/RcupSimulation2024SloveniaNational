"""
    SERS TEAM
    time_calculator.py
"""

import numpy as np
from mapping.map_controller import Mapper
from algorithms.efficient_a_star import AStarAlgorithm
from algorithms.bfs import NavigatingBFSAlgorithm


class PathTimeCalculator:
    def __init__(self, mapper: Mapper, factor: float, exponent: float):
        self.__a_star = AStarAlgorithm()
        self.__closest_free_point_finder = NavigatingBFSAlgorithm(lambda x: x == 0, lambda x: True)

        self.__mapper = mapper

        self.factor = factor
        self.exponent = exponent

    def calculate(self, target_position: np.ndarray):
        n = self.__calculate_path_length(target_position)
        return n * self.factor + n ** self.exponent

    def __calculate_path_length(self, target_position):
        target_grid_index = self.__mapper.pixel_grid.coordinates_to_grid_index(target_position)
        self.__mapper.pixel_grid.expand_to_grid_index(target_grid_index)

        start_array_index = self.__mapper.pixel_grid.coordinates_to_array_index(self.__mapper.robot_position)
        start_array_index = self.__get_closest_traversable_array_index(start_array_index)

        target_array_index = self.__mapper.pixel_grid.coordinates_to_array_index(target_position)
        target_array_index = self.__get_closest_traversable_array_index(target_array_index)
        a_star_path = self.__a_star.a_star(self.__mapper.pixel_grid.arrays["traversable"],
                                           start_array_index,
                                           target_array_index,
                                           self.__mapper.pixel_grid.arrays["navigation_preference"])

        return len(a_star_path)

    def __get_closest_traversable_array_index(self, array_index):
        if self.__mapper.pixel_grid.arrays["traversable"][array_index[0], array_index[1]]:
            return self.__closest_free_point_finder.bfs(found_array=self.__mapper.pixel_grid.arrays["traversable"],
                                                        traversable_array=self.__mapper.pixel_grid.arrays[
                                                            "traversable"],
                                                        start_node=array_index)[0]
        else:
            return array_index
