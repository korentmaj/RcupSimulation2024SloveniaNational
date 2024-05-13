"""
    SERS TEAM
    a_star.py
"""

import numpy as np
import cv2 as cv


class AStarNode:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.p = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position
    
    def __repr__(self):
        return str(self.position)


class AStarAlgorithm:
    def __init__(self):
        self.adjacent = [[0, 1], [0, -1], [-1, 0], [1, 0], ]
        self.preference_weight = 50

    def get_preference(self, preference_grid, position):
        if preference_grid is None:
            return 0
        elif not (position[0] >= preference_grid.shape[0] or position[1] >= preference_grid.shape[1] or position[0] < 0 or position[1] < 0):
            return preference_grid[position[0], position[1]]
        else:
            return 0

    def a_star(self, grid: np.ndarray, start, end, preference_grid=None):
        debug_grid = np.zeros((grid.shape[0], grid.shape[1], 3), dtype=np.uint8)

        # Create start and end node
        start_node = AStarNode(None, list(start))
        start_node.g = start_node.h = start_node.f = 0
        
        if grid[start[0], start[1]]:
            print("[A*]: Start position is not traversable")

        end_node = AStarNode(None, list(end))

        if grid[end[0], end[1]]:
            print("[A*]: End position is not traversable")
            return []

        end_node.g = end_node.h = end_node.f = 0
        open_list = []
        closed_list = []

        open_list.append(start_node)

        while len(open_list) > 0:
            current_node = open_list[0]
            current_index = 0
            for index, item in enumerate(open_list):
                if item.f < current_node.f:
                    current_node = item
                    current_index = index
            open_list.pop(current_index)
            
            closed_list.append(current_node)
            if current_node == end_node:
                path = []
                current = current_node
                while current is not None:
                    path.append(current.position)
                    current = current.parent
                return path[::-1]

            children = []
            for adj in self.adjacent:
                node_position = [current_node.position[0] + adj[0], current_node.position[1] + adj[1]]
                if not (node_position[0] >= grid.shape[0] or node_position[1] >= grid.shape[1] or node_position[0] < 0 or node_position[1] < 0):
                    if grid[node_position[0], node_position[1]]:
                        continue

                new_node = AStarNode(current_node, node_position)
                children.append(new_node)

            for child in children:
                continue_loop = False
                for closed_child in closed_list:
                    if child == closed_child:
                        continue_loop = True
                        break

                child.g = current_node.g + 1
                child.h = ((child.position[0] - end_node.position[0]) ** 2) + (
                           (child.position[1] - end_node.position[1]) ** 2)
                
                child.p = self.get_preference(preference_grid, child.position) * self.preference_weight
                child.f = child.g + child.h + child.p

                for index, open_node in enumerate(open_list):
                    if child == open_node:
                        if child.p + child.g > open_node.p + open_node.g:
                            continue_loop = True
                            break

                if continue_loop:
                    continue

                open_list.append(child)

            for o in open_list:
                debug_grid[o.position[0], o.position[1]] = [0, 0, 255]

            cv.imshow("debug", debug_grid)
            cv.waitKey(1)
            
        return []
