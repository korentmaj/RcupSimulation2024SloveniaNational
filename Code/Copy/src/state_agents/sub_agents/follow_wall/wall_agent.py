"""
    SERS TEAM
    wall_agent.py
"""

import numpy as np
from data_models.vectors import Position2D
from state_agents.interface import SubagentInterface
from mapping.map_controller import Mapper
from state_agents.sub_agents.follow_wall.wall_position import PositionFinder
from state_agents.navigation.navigator import PathFinder


class FollowWallsAgent(SubagentInterface):
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper
        self.__position_finder = PositionFinder(mapper)
        self.__pathfinder = PathFinder(mapper)

    def update(self, force_calculation=False):
        self.__position_finder.update(force_calculation=force_calculation)

        if self.__position_finder.target_position_exists():
            target = self.__position_finder.get_target_position()
            self.__pathfinder.update(np.array(target), force_calculation)  

    def get_target_position(self) -> Position2D:
        return self.__pathfinder.get_next_position()
    
    def target_position_exists(self) -> bool:
        return self.__position_finder.target_position_exists()
