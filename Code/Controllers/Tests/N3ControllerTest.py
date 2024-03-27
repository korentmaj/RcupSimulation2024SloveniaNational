# N3ControllerTest
# Jebi se Potocnik
from typing import Optional

import debug
from devices.devices import GPS, InertialUnit, Motor
from utils import Angle


class Drivetrain:
    def __init__(self, left_motor: Motor, right_motor: Motor, imu: InertialUnit, gps: GPS) -> None:
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.imu = imu
        self.gps = gps

        assert self.left_motor.time_step == self.right_motor.time_step == self.imu.time_step == self.gps.time_step
        self.time_step = self.left_motor.time_step

        self.target_rotation: Optional[Angle] = None
        self.target_velocity = 0

        # Motor velocity is set in angular velocity (rotation speed in radians per second), in limited range
        self.max_motor_velocity = min(self.left_motor.max_velocity, self.right_motor.max_velocity)

        # Erebus robot is very simple from the real-physics perspective and do not require the
        # use of PID controllers - moreover, motors have built-in angular velocity control.
        self.k_omega_to_velocity = 5  # Ratio (motor rad/s) / (robot m/s)
        self.k_omega_to_rotation = 1  # Ratio (motor rad/s) / (robot rad/s)

    def clamp_motor_velocity(self, velocity: Angle) -> Angle:
        return Angle(min(max(velocity, -self.max_motor_velocity), self.max_motor_velocity))

    def set_motor_velocity(self, left_or_both: Angle, right: Angle = None) -> None:
        """Set target angular velocity in rad/s (ω) for both wheels or each wheel separately"""
        self.left_motor.velocity = self.clamp_motor_velocity(left_or_both)
        self.right_motor.velocity = self.clamp_motor_velocity(right if (right is not None) else left_or_both)

    @property
    def velocity(self) -> float:
        """Current velocity (m/s)"""
        return self.gps.speed

    @velocity.setter
    def velocity(self, velocity: float) -> None:
        """Set new target velocity (m/s)"""
        self.target_velocity = velocity

    @property
    def rotation(self) -> Angle:
        """Current rotation angle"""
        return self.imu.yaw

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        """Set new target rotation angle"""
        self.target_rotation = Angle(rotation)  # Wrap in angle to normalize

    @property
    def rotated(self) -> bool:
        """Check if target rotation has been reached"""
        return abs(self.rotation.rotation_to(self.target_rotation).deg) < 1

    def __call__(self) -> None:
        """Update internal states - shall be called once every timestep"""
        velocity = self.velocity
        rotation = self.rotation

        # Fix for the first call (rotation cannot be retrieved in __init__ because no simulation step has been done yet)
        if self.target_rotation is None:
            self.target_rotation = rotation

        # Calculate error
        error_rotation = self.target_rotation.rotation_to(rotation)

        # Calculate motor omega
        mv_moving = self.target_velocity * self.k_omega_to_velocity
        mv_rotating = error_rotation * self.k_omega_to_rotation

        # Because math angle convention is used, rotating in the positive angle direction means rotating
        # counter-clockwise - left motor rotates with negative velocity, right motor with positive.
        left_velocity = mv_moving - mv_rotating
        right_velocity = mv_moving + mv_rotating

        self.set_motor_velocity(left_velocity, right_velocity)

        # TODO: Detect being stuck, do not just bluntly increase speed

        if debug.MOVEMENT:
            yaw, pitch, roll = self.imu.yaw_pitch_roll
            pos = self.gps.position
            print(f"X|Y  {pos.x:.4f} | {pos.y:.4f}", end="    ")
            print(f"Y|P|R  {yaw.deg:.3f} | {pitch.deg:.3f} | {roll.deg:.3f}", end="    ")
            print(f"av|tv|nms  {velocity:.6f} | {self.target_velocity:.3f} | {mv_moving:.3f}", end="    ")
            print(f"ar|tr|dr|nrs  {rotation.deg:.3f} | {self.target_rotation.deg:.3f}  | {error_rotation.deg:.3f}"
                  f" | {mv_rotating:.3f}", end="    ")
            print(f"lm|rm  {left_velocity:.3f}/{left_velocity.deg:.3f} | {right_velocity:.3f}/{right_velocity.deg:.3f}", end="    ")

