"""
    SERS TEAM
    wheel.py
"""


class Wheel:
    def __init__(self, wheel, max_velocity):
        self.maxVelocity = max_velocity
        self.wheel = wheel
        self.velocity = 0
        self.wheel.setPosition(float("inf"))
        self.wheel.setVelocity(0)

    def move(self, ratio):
        if ratio > 1:
            ratio = 1
        elif ratio < -1:
            ratio = -1
        self.velocity = ratio * self.maxVelocity
        self.wheel.setVelocity(self.velocity)
