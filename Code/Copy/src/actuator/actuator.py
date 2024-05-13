"""
    SERS TEAM
    actuator.py
"""

from data_models.angle import Angle
from data_models.vectors import Position2D
from flow.sequencer import Sequencer
from flow.state_machine import StateMachine
from flow.delay import DelayController
from flow.stepper import Stepper
from actuator.freeze_recognition import FreezeRecognition
from robot.robot import Robot
from robot.drive_base import Criteria as RotationCriteria
from mapping.map_controller import Mapper
from state_agents.state_agent import Agent
from detectables.detectable_classification import FixtureClasiffier
from matrix_finalizer.final_creation import FinalMatrixCreator
from utils import ColorFilterTuner
from detectables.color_filter import ColorFilter
from debug.settings import SHOW_DEBUG, DO_SLOW_DOWN, SLOW_DOWN_S, DO_SAVE_DETECTABLE_DEBUG, SAVE_DETECTABLE_DEBUG_DIRECTORY, \
    TUNE_FILTER
import time
import numpy as np
import cv2 as cv


class Actuator:
    def __init__(self, mapper: Mapper, robot: Robot) -> None:
        self.agent = Agent(mapper)
        self.mapper = mapper
        self.robot = robot

        self.delay_manager = DelayController()
        self.stuck_detector = FreezeRecognition()

        self.state_machine = StateMachine("init")
        self.state_machine.create_state("init", self.state_init, {"explore"})
        self.state_machine.create_state("explore", self.state_explore, {"end", "report_fixture", "send_map", "stuck"})
        self.state_machine.create_state("end", self.state_end)
        # self.state_machine.create_state("detect_fixtures", self.state_detect_fixtures, {"explore", "report_fixture"})
        self.state_machine.create_state("report_fixture", self.state_report_fixture, {"explore", "send_map"})
        self.state_machine.create_state("send_map", self.state_send_map, {"explore", "end"})
        self.state_machine.create_state("stuck", self.state_stuck, {"explore", "send_map", "end"})

        self.sequencer = Sequencer(reset_function=self.delay_manager.reset_delay)
        self.fixture_detector = FixtureClasiffier()
        self.final_matrix_creator = FinalMatrixCreator(mapper.tile_size, mapper.pixel_grid.resolution)

        self.mapping_enabled = False
        self.victim_reporting_enabled = False

        self.seq_print = self.sequencer.make_simple_event(print)
        self.seq_move_wheels = self.sequencer.make_simple_event(self.robot.move_wheels)

        self.seq_rotate_to_angle = self.sequencer.make_complex_event(self.robot.rotate_to_angle)
        self.seq_rotate_slowly_to_angle = self.sequencer.make_complex_event(self.robot.rotate_slowly_to_angle)
        self.seq_move_to_coords = self.sequencer.make_complex_event(self.robot.move_to_coords)
        self.seq_delay_seconds = self.sequencer.make_complex_event(self.delay_manager.delay_seconds)

        self.seq_align_with_fixture = self.sequencer.make_complex_event(self.align_with_fixture)
        self.letter_to_report = None
        self.report_orientation = Angle(0)

        self.max_time_in_run = 8 * 60
        self.map_sent = False
        self.robot.set_start_time()
        self.mini_calibrate_step_counter = Stepper(20)
        self.color_filter_tuner = ColorFilterTuner(ColorFilter((0, 0, 29), (0, 0, 137)), TUNE_FILTER)

    def run(self):
        while self.robot.do_loop():
            self.robot.update()

            self.delay_manager.update(self.robot.time)
            self.stuck_detector.update(self.robot.position,
                                       self.robot.previous_position,
                                       self.robot.drive_base.get_wheel_average_angular_velocity()
                                       )

            self.color_filter_tuner.tune(self.robot.center_camera.image.image)
            self.do_mapping()

            # self.check_swamp_proximity()
            self.check_map_sending()
            self.state_machine.run()
            # self.final_matrix_creator.pixel_grid_to_final_grid(self.mapper.pixel_grid, self.mapper.start_position)

            if DO_SLOW_DOWN:
                time.sleep(SLOW_DOWN_S)

            # final_matrix = self.final_matrix_creator.pixel_grid_to_final_grid(self.mapper.pixel_grid, self.mapper.start_position)
            # print(final_matrix)
            # print("state:", self.state_machine.state)

    def do_mapping(self):
        if self.mapping_enabled:
            if not self.robot.is_shaky():
                self.mapper.update(self.robot.get_point_cloud(),
                                   self.robot.get_out_of_bounds_point_cloud(),
                                   self.robot.get_lidar_detections(),
                                   self.robot.get_camera_images(),
                                   self.robot.position,
                                   self.robot.orientation,
                                   self.robot.time)
            else:
                self.mapper.update(camera_images=self.robot.get_camera_images(),
                                   robot_position=self.robot.position,
                                   robot_orientation=self.robot.orientation,
                                   time=self.robot.time)

    def check_swamp_proximity(self):
        if self.mapper.is_close_to_swamp():
            self.robot.auto_decide_orientation_sensor = False
            self.robot.orientation_sensor = self.robot.GYROSCOPE
        else:
            self.robot.auto_decide_orientation_sensor = True

    def check_map_sending(self):
        if self.mapper.time > self.max_time_in_run - 2 and not self.map_sent:
            self.state_machine.change_state("send_map")
            self.sequencer.reset_sequence()

    def state_init(self, change_state_function):
        self.sequencer.start_sequence()
        self.seq_delay_seconds(0.5)

        self.sequencer.simple_event(self.calibrate_position_offsets)
        self.sequencer.simple_event(self.mapper.register_start, self.robot.position)
        self.seq_calibrate_robot_rotation()

        if self.sequencer.simple_event():
            self.mapping_enabled = True
            self.victim_reporting_enabled = True

        self.seq_delay_seconds(0.5)
        self.sequencer.complex_event(self.robot.rotate_to_angle, angle=Angle(90, Angle.DEGREES), direction=RotationCriteria.LEFT)
        self.sequencer.complex_event(self.robot.rotate_to_angle, angle=Angle(180, Angle.DEGREES), direction=RotationCriteria.LEFT)
        self.seq_delay_seconds(0.5)
        self.sequencer.simple_event(change_state_function, "explore")
        self.sequencer.seq_reset_sequence()

    def state_explore(self, change_state_function):
        self.sequencer.start_sequence()

        if self.sequencer.simple_event():
            self.mapping_enabled = True

        if SHOW_DEBUG and self.agent_changed():
            print("[STATE AGENT] CHANGED!")

        self.agent.update()
        self.mini_calibrate()
        self.seq_move_to_coords(self.agent.get_target_position())
        self.sequencer.seq_reset_sequence()

        if SHOW_DEBUG:
            print("[DEBUG] Orientation:", self.robot.orientation)
            print("[DEBUG] Position:", self.robot.position)

        if self.agent.do_end():
            self.state_machine.change_state("end")

        cam_images = self.robot.get_camera_images()
        if self.victim_reporting_enabled and cam_images is not None and not self.mapper.has_detected_victim_from_position():
            for cam_image in cam_images:
                self.robot.lidar.get_detections()
                fixtures = self.fixture_detector.find_fixtures(cam_image.image)
                if len(fixtures):
                    self.letter_to_report = self.fixture_detector.classify_fixture(fixtures[0])
                    self.report_orientation = cam_image.data.horizontal_orientation

                    if DO_SAVE_DETECTABLE_DEBUG:
                        cv.imwrite(
                            f"{SAVE_DETECTABLE_DEBUG_DIRECTORY}/{str(time.time()).rjust(50)}-{self.letter_to_report}-{self.robot.position}.png",
                            cam_image.image)
                    change_state_function("report_fixture")
                    self.sequencer.reset_sequence()
                    break

        """
        if self.stuck_detector.is_stuck():
            change_state_function("stuck")
        """

    def mini_calibrate(self):
        if self.mini_calibrate_step_counter.check():
            self.seq_move_wheels(1, 1)
            self.seq_delay_seconds(0.1)

        self.mini_calibrate_step_counter.increase()

    def align_with_fixture(self):
        center_image = self.robot.center_camera.image.image
        fixtures = self.fixture_detector.find_fixtures(center_image)

        if len(fixtures) == 0:
            return True

        fixture = fixtures[0]
        fixture_shape = Position2D(fixture["image"].shape)
        fixture_position = Position2D(fixture["position"])
        fixture_center = fixture_shape / 2 + fixture_position

        image_center = Position2D(center_image.shape) / 2
        diff = image_center - fixture_center

        if abs(diff.y) > 4:
            vel = diff.y * 0.1
            self.robot.move_wheels(vel, vel)
            return False

        if abs(diff.x) > 6:
            sign = np.sign(diff.x)
            vel = 0.1
            self.robot.move_wheels(vel * sign, vel * -sign)
            return False

        return True

    def state_end(self, change_state_function):
        final_matrix = self.final_matrix_creator.pixel_grid_to_final_grid(self.mapper.pixel_grid, self.mapper.start_position)
        self.robot.communicator.send_map(final_matrix)
        self.robot.communicator.send_end_of_play()

    def state_send_map(self, change_state_function):
        final_matrix = self.final_matrix_creator.pixel_grid_to_final_grid(self.mapper.pixel_grid, self.mapper.start_position)
        self.robot.communicator.send_map(final_matrix)
        self.map_sent = True
        change_state_function("explore")
        self.sequencer.seq_reset_sequence()

    def state_report_fixture(self, change_state_function):
        self.sequencer.start_sequence()
        self.seq_print("[SEQ] Entered report detectable!")
        self.seq_move_wheels(0, 0)

        if self.letter_to_report is not None:
            if self.sequencer.simple_event():
                self.mapping_enabled = False

            if self.sequencer.simple_event():
                self.report_orientation.normalize()

            self.seq_print("[REPORT] Rotating to angle:", self.report_orientation)
            self.seq_rotate_to_angle(self.report_orientation.degrees)
            self.seq_print("[REPORT] Rotated to angle")

            self.seq_align_with_fixture()
            self.seq_print("[REPORT] Aligned with detectable")
            self.seq_move_wheels(0, 0)

            if self.sequencer.simple_event():
                center_image = self.robot.center_camera.image.image
                fixtures = self.fixture_detector.find_fixtures(center_image)

                if len(fixtures) == 0:
                    change_state_function("explore")
                    self.sequencer.reset_sequence()
                    self.mapping_enabled = True
                    return

                self.letter_to_report = self.fixture_detector.classify_fixture(fixtures[0])

                if self.letter_to_report is None:
                    change_state_function("explore")
                    self.sequencer.reset_sequence()
                    self.mapping_enabled = True
                    return

                print("[REPORT] Detectable to report: ", self.letter_to_report)

            self.seq_move_wheels(0.6, 0.6)
            self.seq_delay_seconds(0.1)
            self.seq_move_wheels(0, 0)
            self.seq_delay_seconds(1.5)

            if self.sequencer.simple_event():
                print("[REPORT] Sending detectable: ", self.letter_to_report)
                self.robot.communicator.send_victim(self.robot.raw_position, self.letter_to_report)

            self.seq_delay_seconds(0.1)

            if self.sequencer.simple_event():
                self.mapper.fixture_mapper.map_detected_fixture(self.robot.position)

            self.seq_move_wheels(-0.6, -0.6)
            self.seq_delay_seconds(0.1)
            self.seq_move_wheels(0, 0)

            if self.sequencer.simple_event():
                self.letter_to_report = None

            if self.sequencer.simple_event():
                self.mapping_enabled = True

        if self.sequencer.simple_event():
            self.mapping_enabled = True

        self.sequencer.simple_event(change_state_function, "explore")
        self.sequencer.seq_reset_sequence()

    def state_stuck(self, change_state_function):
        print("[STUCK] Robot is stuck! Maneuvering out!")
        self.sequencer.start_sequence()
        self.seq_move_wheels(-0.6, -0.6)
        self.seq_delay_seconds(0.2)
        self.seq_move_wheels(0.6, -0.6)
        self.seq_delay_seconds(1)

        self.sequencer.simple_event(change_state_function, "explore")
        self.sequencer.seq_reset_sequence()

    def calibrate_position_offsets(self):
        print("[CALIBRATION] Robot position:", self.robot.position)
        self.robot.position_offsets = self.robot.position % (self.mapper.quarter_tile_size * 2)
        print("[CALIBRATION] Position offsets: ", self.robot.position_offsets)

    def seq_calibrate_robot_rotation(self):
        if self.sequencer.simple_event():
            self.robot.auto_decide_orientation_sensor = False
        self.seq_move_wheels(-1, -1)
        self.seq_delay_seconds(0.1)
        if self.sequencer.simple_event():
            self.robot.orientation_sensor = self.robot.GPS
        self.seq_move_wheels(1, 1)
        self.seq_delay_seconds(0.1)
        if self.sequencer.simple_event():
            self.robot.orientation_sensor = self.robot.GYROSCOPE
        self.seq_delay_seconds(0.1)
        self.seq_move_wheels(0, 0)
        self.seq_move_wheels(-1, -1)
        self.seq_delay_seconds(0.1)
        self.seq_move_wheels(0, 0)
        if self.sequencer.simple_event():
            self.robot.auto_decide_orientation_sensor = True

    def agent_changed(self):
        return self.current_agent != self.previous_agent
