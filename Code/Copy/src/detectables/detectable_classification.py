"""
    SERS TEAM
    detectable_classification.py
"""

import math
import random

import numpy as np
import cv2 as cv

from detectables.victim_clasification import VictimClassifier
from detectables.color_filter import ColorFilter
from detectables.detectable_filter import NonFixtureFilter

from debug.settings import SHOW_DEBUG, SHOW_DETECTABLE_DEBUG, TUNE_FILTER


class FixtureType:
    def __init__(self, fixture_type, default_letter, ranges=None):
        self.fixture_type = fixture_type
        self.default_letter = default_letter
        self.ranges = ranges
    
    def is_fixture(self, colour_counts: dict):
        for color in self.ranges:
            if not self.ranges[color][0] <= colour_counts[color] <= self.ranges[color][1]:
                return False
        return True
            
class FixtureClasiffier:
    def __init__(self):
        self.victim_classifier = VictimClassifier()

        self.colors = ("black", "white", "yellow", "red")
        self.color_filters = {
            "black": ColorFilter(lower_hsv=(0, 0, 0), upper_hsv=(0, 0, 160)),
            "white": ColorFilter(lower_hsv=(0, 0, 170), upper_hsv=(255, 110, 208)),
            "yellow": ColorFilter(lower_hsv=(25, 170, 82), upper_hsv=(30, 255, 255)),
            "red": ColorFilter(lower_hsv=(134, 91, 155), upper_hsv=(175, 255, 204))           
        }
        self.wall_color_filter = ColorFilter((90, 44,  0), (95, 213, 158))
        self.min_fixture_height = 16
        self.min_fixture_width_factor = 0.8

        self.possible_fixture_letters = ["P", "O", "F", "C", "S", "H", "U"]

        self.fixture_types = (
            FixtureType("already_detected", "",  {"white": (5000,    math.inf), 
                                                  "black": (0,    0),
                                                  "red": (0,    0),
                                                  "yellow": (0,    0)
                                                  }),
            
            FixtureType("already_detected", "",  {"white": (0,    2000), 
                                                  "black": (0,    0),
                                                  "red": (0,    0),
                                                  "yellow": (0,    0)
                                                  }),

            FixtureType("organic_peroxide", "O", {"red":   (1,    math.inf), 
                                                  "yellow": (1,    math.inf)
                                                  }),

            FixtureType("flammable", "F",        {"white": (1,    math.inf), 
                                                  "red": (1,    math.inf)
                                                  }),

            FixtureType("victim",    "H",        {"white": (4500, math.inf), 
                                                  "black": (1000,  4000)
                                                  }),

            FixtureType("corrosive", "C",        {"white": (700,  4500), 
                                                  "black": (900, 3000)
                                                  }),

            FixtureType("poison",    "P",        {"white": (2000,  5000), 
                                                  "black": (100,    1000)
                                                  }),
        )

        self.non_fixture_filter = NonFixtureFilter()

    def get_wall_mask(self, image: np.ndarray):
        margin = 1
        raw_wall = self.wall_color_filter.filter(image)

        wall = np.ones(shape=(raw_wall.shape[0], raw_wall.shape[1] + margin * 2), dtype=np.uint8) * 255
        wall[:, margin: -margin] = raw_wall

        contents, _ = cv.findContours(wall, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        debug = np.copy(image)
        filled_wall = np.zeros_like(wall, dtype=np.bool_)

        for c in contents:
            this_cont = np.zeros_like(wall, dtype=np.uint8)
            cv.fillPoly(this_cont, [c,], 255)
            filled_wall += this_cont > 0

        filled_wall = filled_wall[:, margin:-margin]

        return filled_wall

    def sum_images(self, images):
        final_img = images[0]
        for index, image in enumerate(images):
            final_img += image
        final_img[final_img > 255] = 255
        return final_img

    def filter_fixtures(self, victims) -> list:
        final_victims = []
        for vic in victims:
            if vic["image"].shape[0] > self.min_fixture_height and vic["image"].shape[1] > self.min_fixture_height * self.min_fixture_width_factor:
                final_victims.append(vic)

        return final_victims

    def find_fixtures(self, image) -> list:
        
        image = np.rot90(image, k=3)
        if SHOW_DETECTABLE_DEBUG:
            cv.imshow("image", image)

        binary_images = []
        for f in self.color_filters.values():
            binary_images.append(f.filter(image))

        binary_image = self.sum_images(binary_images)
        walls_mask = self.get_wall_mask(image)
        non_fixture_by_color = self.non_fixture_filter.filter(image)
        binary_image *= (walls_mask + (non_fixture_by_color == 0))

        if SHOW_DETECTABLE_DEBUG:
            cv.imshow("binaryImage", binary_image)

        contours, _ = cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        final_victims = []
        contours, _ = cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        
        for c in contours:
            x, y, w, h = cv.boundingRect(c)
            final_victims.append({"image":image[y:y + h, x:x + w], "position":(x, y)})

        return self.filter_fixtures(final_victims)
    
    def get_bounding_rect_of_contours(self, contours):
        
        min_x = 0
        min_y = 0
        max_x = math.inf
        max_y = math.inf

        for c in contours:
            x, y, w, h = cv.boundingRect(c)
            min_x = min(x, min_x)
            min_y = min(y, min_y)
            max_x = max(x + w, max_x)
            max_y = max(y + h, max_y)

        return min_x, min_y, max_x, max_y

    def count_colors(self, image) -> dict:
        color_point_counts = {}

        for name, filter in self.color_filters.items():
            color_image = filter.filter(image)

            color_point_counts[name] = np.count_nonzero(color_image)

        return color_point_counts

    def classify_fixture(self, fixture) -> str:
        image = cv.resize(fixture["image"], (100, 100), interpolation=cv.INTER_AREA)

        color_point_counts = self.count_colors(image)
        
        if SHOW_DETECTABLE_DEBUG:
            print(color_point_counts)

        final_fixture_filter = None
        for filter in self.fixture_types:
            if filter.is_fixture(color_point_counts):
                final_fixture_filter = filter
                break

        if final_fixture_filter is None:
            letter = random.choice(self.possible_fixture_letters)

        elif final_fixture_filter.fixture_type == "victim":
            letter = self.victim_classifier.classify_victim(fixture)

        elif final_fixture_filter.fixture_type == "already_detected":
            letter = None

        else:
            letter = final_fixture_filter.default_letter

        if SHOW_DETECTABLE_DEBUG:
            print("[DETECTABLE]: ", letter)

        return letter
