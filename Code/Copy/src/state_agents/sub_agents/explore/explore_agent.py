"""
    SERS TEAM
    explore_agent.py
"""

import numpy as np
from state_agents.interface import SubagentInterface
from data_models.vectors import Position2D
from mapping.map_controller import Mapper
from state_agents.navigation.navigator import PathFinder
from state_agents.sub_agents.explore.explore_position import PositionFinder


class GoToNonDiscoveredAgent(SubagentInterface):
    def __init__(self, mapper: Mapper):
        self.__path_finder = PathFinder(mapper)
        self.__position_finder = PositionFinder(mapper)
    
    def update(self, force_calculation=False) -> None:
        self.__position_finder.update(force_calculation=self.__do_force_position_finder() or force_calculation)

        if self.__position_finder.target_position_exists():
            target = self.__position_finder.get_target_position()
            self.__path_finder.update(target_position=np.array(target), force_calculation=force_calculation)

    def get_target_position(self) -> Position2D:
        return self.__path_finder.get_next_position()    
    
    def __do_force_position_finder(self) -> bool:
        return self.__path_finder.is_path_finished() or self.__path_finder.path_not_found
    
    def target_position_exists(self) -> bool:
        return self.__position_finder.target_position_exists()
        