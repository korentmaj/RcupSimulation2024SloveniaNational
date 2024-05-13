"""
    SERS TEAM
    victim_classification.py
"""

from debug.settings import SHOW_DETECTABLE_DEBUG
import cv2 as cv
import numpy as np
import random
from detectables.color_filter import ColorFilter


class VictimClassifier:
    def __init__(self):
        self.white = 255
        self.victim_letter_filter = ColorFilter(lower_hsv=(0, 0, 0), upper_hsv=(0, 0, 130))
        self.top_image_reduction = 0
        self.horizontal_image_reduction = 1

        self.area_width = 10
        self.area_height = 30
        self.min_count_in_area = int(self.area_height * self.area_width * 0.2)

        self.areas = {
            "top": ((0, self.area_height), (self.area_width // -2, self.area_width // 2)),
            "middle": (
                (50 - self.area_height // 2, 50 + self.area_height // 2),
                (self.area_width // -2, self.area_width // 2)),
            "bottom": ((100 - self.area_height, 100), (self.area_width // -2, self.area_width // 2))
        }

        self.letters = {
            "H": [{'top': False, 'middle': True, 'bottom': False}],

            "S": [{'top': True, 'middle': True, 'bottom': True},
                  {'top': True, 'middle': False, 'bottom': True}],

            "U": [{'top': False, 'middle': False, 'bottom': True},
                  {'top': False, 'middle': False, 'bottom': False}],

        }

    def crop_white(self, binary_img):
        white = 255
        rows, cols = np.where(binary_img == white)
        if len(rows) == 0 or len(cols) == 0:
            return binary_img
        else:
            min_y, max_y = np.min(rows), np.max(rows)
            min_x, max_x = np.min(cols), np.max(cols)
            return binary_img[min_y:max_y + 1, min_x:max_x + 1]

    def isolate_victim(self, image):
        binary = self.victim_letter_filter.filter(image)
        letter = self.get_biggest_blob(binary)

        if SHOW_DETECTABLE_DEBUG:
            cv.imshow("thresh", binary)

        return letter

    def get_biggest_blob(self, binary_image: np.ndarray) -> np.ndarray:
        contours, _ = cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        max_size = 0
        biggest_blob = None
        for c0 in contours:
            x, y, w, h = cv.boundingRect(c0)

            if w * h > max_size:
                biggest_blob = binary_image[y:y + h, x:x + w]
                max_size = w * h

        return biggest_blob

    def classify_victim(self, victim):
        letter = self.isolate_victim(victim["image"])

        letter = cv.resize(letter, (100, 100), interpolation=cv.INTER_AREA)
        moments = cv.moments(letter)
        center = letter.shape[1] / 2
        offset = (moments["m10"] / moments["m00"] - center) * 1

        center -= offset
        center = round(center)

        if SHOW_DETECTABLE_DEBUG:
            cv.imshow("letra", letter)

        letter_color = cv.cvtColor(letter, cv.COLOR_GRAY2BGR)

        images = {
            "top": letter[self.areas["top"][0][0]:self.areas["top"][0][1],
                   self.areas["top"][1][0] + center:self.areas["top"][1][1] + center],
            "middle": letter[self.areas["middle"][0][0]:self.areas["middle"][0][1],
                      self.areas["middle"][1][0] + center:self.areas["middle"][1][1] + center],
            "bottom": letter[self.areas["bottom"][0][0]:self.areas["bottom"][0][1],
                      self.areas["bottom"][1][0] + center:self.areas["bottom"][1][1] + center]
        }

        if SHOW_DETECTABLE_DEBUG:
            cv.rectangle(letter_color, (self.areas["top"][1][0] + center, self.areas["top"][0][0]),
                         (self.areas["top"][1][1] + center, self.areas["top"][0][1]), (0, 255, 0), 1)
            cv.rectangle(letter_color, (self.areas["middle"][1][0] + center, self.areas["middle"][0][0]),
                         (self.areas["middle"][1][1] + center, self.areas["middle"][0][1]), (0, 0, 255), 1)
            cv.rectangle(letter_color, (self.areas["bottom"][1][0] + center, self.areas["bottom"][0][0]),
                         (self.areas["bottom"][1][1] + center, self.areas["bottom"][0][1]), (225, 0, 255), 1)
            cv.imshow("letter_color", letter_color)

        counts = {}
        for key in images.keys():
            count = 0
            for row in images[key]:
                for pixel in row:
                    if pixel == self.white:
                        count += 1

            counts[key] = count > self.min_count_in_area

        for letter_key in self.letters.keys():
            for template in self.letters[letter_key]:
                if counts == template:
                    print("[DETECTABLE]: ", letter_key)
                    return letter_key

        return random.choice(list(self.letters.keys()))
