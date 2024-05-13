"""
    SERS TEAM
    communicator.py
"""


import utils as utilities
import struct
from robot.components.sensor import Sensor
from debug.settings import SHOW_MAP_AT_END


class Communicator(Sensor):
    def __init__(self, emitter, receiver, time_step):
        self.receiver = receiver
        self.emitter = emitter
        self.receiver.enable(time_step)
        self.lack_of_progress = False
        self.do_get_world_info = True
        self.game_score = 0
        self.remaining_time = 0

    def send_victim(self, position, victim_type):
        self.do_get_world_info = False
        letter = bytes(victim_type, "utf-8")
        position = utilities.multiply_lists(position, [100, 100])
        position = [int(position[0]), int(position[1])]
        message = struct.pack("i i c", position[0], position[1], letter)
        self.emitter.send(message)
        self.do_get_world_info = False

    def send_lack_of_progress(self):
        self.do_get_world_info = False
        message = struct.pack('c', 'L'.encode())  # message = 'L' to activate lack of progress
        self.emitter.send(message)
        self.do_get_world_info = False

    def send_end_of_play(self):
        self.do_get_world_info = False
        exit_mes = struct.pack('c', b'E')
        self.emitter.send(exit_mes)
        print("[END OF PLAY] Finished!")

    def send_map(self, np_array):
        if SHOW_MAP_AT_END:
            print(np_array)
        s = np_array.shape
        s_bytes = struct.pack('2i', *s)
        flat_map = ','.join(np_array.flatten())
        sub_bytes = flat_map.encode('utf-8')
        a_bytes = s_bytes + sub_bytes

        self.emitter.send(a_bytes)
        map_evaluate_request = struct.pack('c', b'M')
        self.emitter.send(map_evaluate_request)
        self.do_get_world_info = False

    def request_game_data(self):
        if self.do_get_world_info:
            message = struct.pack('c', 'G'.encode())
            self.emitter.send(message)

    def update(self):
        if self.do_get_world_info:
            self.request_game_data()
            if self.receiver.getQueueLength() > 0:
                received_data = self.receiver.getBytes()
                if len(received_data) > 2:
                    tup = struct.unpack('c f i', received_data)
                    if tup[0].decode("utf-8") == 'G':
                        self.game_score = tup[1]
                        self.remaining_time = tup[2]
                        self.receiver.nextPacket()

            self.lack_of_progress = False
            if self.receiver.getQueueLength() > 0:
                received_data = self.receiver.getBytes()
                print(received_data)
                if len(received_data) < 2:
                    tup = struct.unpack('c', received_data)
                    if tup[0].decode("utf-8") == 'L':
                        print("[LACK OF PROGRESS] Detected!")
                        self.lack_of_progress = True
                    self.receiver.nextPacket()
        else:
            self.do_get_world_info = True
