"""
    SERS TEAM
    return_agent.py
"""

import numpy as np
from data_models.vectors import Position2D
from state_agents.interface import SubagentInterface
from mapping.map_controller import Mapper
from state_agents.navigation.navigator import PathFinder


class ReturnToStartAgent(SubagentInterface):
    def __init__(self, mapper: Mapper) -> None:
        self.__mapper = mapper
        self.__pathfinder = PathFinder(self.__mapper)

    def update(self, force_calculation) -> None:
        self.__pathfinder.update(np.array(self.__mapper.start_position), force_calculation=force_calculation)

    def get_target_position(self) -> Position2D:
        return self.__pathfinder.get_next_position()

    def target_position_exists(self) -> bool:
        return self.__mapper.start_position is not None
