import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

'''
    Global data.
'''
lock = []
port = 12000
carlotta = -1
host = 'localhost'
permanents = ['pink']
before = ['purple', 'brown']
mandatory_powers = ['red', 'blue', 'grey']
after = ['black', 'white', 'red', 'blue', 'grey']
ghosts_stats = {'pink': {'suspect': False, 'power': False},
                'blue': {'suspect': False, 'power': False},
                'purple': {'suspect': False, 'power': False},
                'grey': {'suspect': False, 'power': False},
                'white': {'suspect': False, 'power': False},
                'black': {'suspect': False, 'power': False},
                'red': {'suspect': False, 'power': False},
                'brown': {'suspect': False, 'power': False}}

pos = {0: [], 1: [], 2: [], 3: [], 4: [],
       5: [], 6: [], 7: [], 8: [], 9: []}
passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]


'''
set up inspector logging
'''
inspector_logger = logging.getLogger()
inspector_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")

os.path.exists("./logs/inspector.log") and os.remove("./logs/inspector.log")
try:
    file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
except FileNotFoundError:
    os.mkdir('logs')
    file_handler = RotatingFileHandler('./logs/inspector.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
inspector_logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
inspector_logger.addHandler(stream_handler)


class Player():
    '''
        Player class manager.
    '''
    def __init__(self):
        self.step = 0
        self.end = False
        self.shadow = 0
        self.next_rep = []
        self.nb_suspect = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def calc_isolate_suspect(self, data):
        isolate = 0
        for x in pos:
            if self.shadow == x:
                for y in pos[x]:
                    if ghosts_stats[y]["suspect"] is True:
                        isolate += 1
            else:
                if len(pos[x]) == 1 and ghosts_stats[pos[x][0]]["suspect"] is True:
                    isolate += 1
        return isolate

    def playable(self, data, color):
        i = 0
        for x in data["data"]:
            if x["color"] == color:
                return i
            i += 1
        return -1

    def find_pos(self, color):
        pos_color = -1
        for x in pos:
            for y in pos[x]:
                if y == color:
                    pos_color = x
        return pos_color


    def get_adjacent_positions(self, color, pos_color):
        if color == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        blocked = {lock[0], lock[1]}
        return [room for room in active_passages[pos_color] if set([room, pos_color]) != set(blocked)]


    def get_adjacent_positions_from_position(self, position, color):
        if color == "pink":
            active_passages = pink_passages
        else:
            active_passages = passages
        blocked = {lock[0], lock[1]}
        return [room for room in active_passages[position] if set([room, position]) != set(blocked)]

    def possible_movement(self, color, pos_color):
        # get the available rooms from a given position
        available_rooms = list()
        available_rooms.append(self.get_adjacent_positions(color, pos_color))
        for step in range(1, len(pos[pos_color])):
            # build rooms that are a distance equal to step+1
            next_rooms = list()
            for room in available_rooms[step-1]:
                next_rooms += self.get_adjacent_positions_from_position(room,
                                                                        color)
            available_rooms.append(next_rooms)

        # flatten the obtained list
        temp = list()
        for sublist in available_rooms:
            for room in sublist:
                temp.append(room)

        # filter the list in order to keep an unique occurrence of each room
        temp = set(temp)
        available_positions = list(temp)
        return available_positions

    def create_next_answer(self, color, room, power, pos_power):
        self.next_rep = [room]
        if (color in after):
            self.next_rep = [room, power, pos_power]
            if (color in mandatory_powers):
                self.next_rep = [room, pos_power]
        if (color in before):
            self.next_rep = [power, room]
            if power == 1:
                self.next_rep = [power, pos_power, room]

    def strategy_one(self, data):
        if self.playable(data, "red") >= 0:
            available_movement = self.possible_movement("red", self.find_pos("red"))
            for room in available_movement:
                if len(pos[room]) != 0:
                    for charac in pos[room]:
                        if ghosts_stats[charac]['suspect'] is True and room != self.shadow and charac != "red":
                            self.next_rep = [room]
                            return self.playable(data, "red")
                    for charac in pos[room]:
                        if charac != "red":
                            self.next_rep = [room]
                            return self.playable(data, "red")
        if self.playable(data, "black") >= 0:
            available_movement = self.possible_movement("red", self.find_pos("red"))
            tmp_nb = -1
            tmp_pos = -1
            for room in available_movement:
                if len(pos[room]) > tmp_nb:
                    tmp_pos = room
                    tmp_nb = len(pos[room])
            self.next_rep = [tmp_pos, 1]
            return self.playable(data, "black")
        if self.playable(data, "white") >= 0:
            available_movement = self.possible_movement("white", self.find_pos("white"))
            tmp_nb = -1
            tmp_pos = -1
            for room in available_movement:
                if len(pos[room]) > tmp_nb:
                    tmp_pos = room
                    tmp_nb = len(pos[room])
            self.next_rep = [tmp_pos, 0]
            return self.playable(data, "white")
        if self.playable(data, "grey") >= 0:
            available_movement = self.possible_movement("grey", self.find_pos("grey"))
            tmp_nb = -1
            tmp_pos = -1
            for room in available_movement:
                if len(pos[room]) > tmp_nb:
                    tmp_pos = room
                    tmp_nb = len(pos[room])
            tmp = -1
            for x in pos:
                if len(pos[x]) == 0:
                    tmp = x
            self.next_rep = [tmp_pos, tmp]
            return self.playable(data, "grey")
        tab = ['blue', 'brown', 'purple', 'pink']
        for charac in tab:
            if self.playable(data, charac) >= 0:
                available_movement = self.possible_movement(charac, self.find_pos(charac))
                for room in available_movement:
                    for tocheck in pos[room]:
                        if self.playable(data, tocheck) < 0:
                            self.create_next_answer(charac, room, 0, -1)
                            return self.playable(data, charac)
        for charac in tab:
            if self.playable(data, charac) >= 0:
                available_movement = self.possible_movement(charac, self.find_pos(charac))
                for room in available_movement:
                    if len(pos[room]) > 0:
                        self.create_next_answer(charac, room, 0, -1)
                        return self.playable(data, charac)
        return random.randint(0, len(data['data'])-1)

    def strategy_two(self, data):
        if self.playable(data, "red") >= 0:
            available_movement = self.possible_movement("red", self.find_pos("red"))
            for room in available_movement:
                if room == self.shadow:
                    self.next_rep = [room]
                    return self.playable(data, "red")
            for room in available_movement:
                if len(pos[room]) == 0:
                    self.next_rep = [room]
                    return self.playable(data, "red")
                if len(pos[room]) == 1 and ghosts_stats[pos[room][0]]['suspect'] is False:
                    self.next_rep = [room]
                    return self.playable(data, "red")
        if self.playable(data, "black") >= 0:
            available_movement = self.possible_movement("black", self.find_pos("black"))
            self.next_rep = [-1, 0]
            return self.playable(data, "black")
        if self.playable(data, "white") >= 0:
            available_movement = self.possible_movement("white", self.find_pos("white"))
            tmp_nb = -1
            tmp_pos = -1
            for room in available_movement:
                if len(pos[room]) > tmp_nb:
                    tmp_pos = room
                    tmp_nb = len(pos[room])
            self.next_rep = [tmp_pos, 1]
            return self.playable(data, "white")
        if self.playable(data, "grey") >= 0:
            available_movement = self.possible_movement("grey", self.find_pos("grey"))
            power_nb = -1
            power_pos = -1
            for room in pos:
                if len(pos[room]) > power_nb:
                    power_nb = len(pos[room])
                    power_pos = room
            for room in available_movement:
                if room == self.shadow:
                    self.next_rep = [room, power_pos]
                    return self.playable(data, "grey")
            move_nb = 9
            move_pos = -1
            for room in available_movement:
                if len(pos[room]) < move_nb:
                    move_nb = len(pos[room])
                    move_pos = room
            self.next_rep = [move_pos, power_pos]
            return self.playable(data, "grey")

        tab = ['blue', 'brown', 'purple', 'pink']
        for charac in tab:
            if self.playable(data, charac) >= 0:
                available_movement = self.possible_movement(charac, self.find_pos(charac))
                for room in available_movement:
                    if room == self.shadow or len(pos[room]) == 0:
                        self.create_next_answer(charac, room, 0, -1)
                        return self.playable(data, charac)
        return random.randint(0, len(data['data'])-1)

    def calc_answer(self, data):
        self.next_rep = []
        if self.nb_suspect / 2 <= self.calc_isolate_suspect(data):
            answer = self.strategy_one(data)
        else:
            answer = self.strategy_two(data)
        return answer

    def answer(self, question):
        # work
        data = question["data"]
        game_state = question["game state"]
        if self.step == 1:
            response_index = self.calc_answer(question)
        else:
            if len(self.next_rep) > 0:
                response = self.next_rep[0]
                del self.next_rep[0]
                if (response in data):
                    response_index = data.index(response)
                else:
                    response_index = random.randint(0, len(data)-1)
            else:
                response_index = random.randint(0, len(data)-1)

        # log
        inspector_logger.debug("|\n|")
        inspector_logger.debug("inspector answers")
        inspector_logger.debug(f"question type ----- {question['question type']}")
        inspector_logger.debug(f"data -------------- {data}")
        inspector_logger.debug(f"response index ---- {response_index}")
        inspector_logger.debug(f"response ---------- {data[response_index]}")
        return response_index

    def handle_json(self, data):
        global carlotta, lock
        data = json.loads(data)
        if data['question type'] == 'select character':
            self.step = 1
        else:
            self.step = self.step + 1
        carlotta = data['game state']['position_carlotta']
        lock = data['game state']['blocked']
        self.shadow = data['game state']['shadow']
        for x in pos:
            pos[x] = []
        self.nb_suspect = 0
        for ghost in data['game state']['characters']:
            ghosts_stats[ghost['color']]['power'] = ghost['power']
            ghosts_stats[ghost['color']]['suspect'] = ghost['suspect']
            if ghost['suspect'] is True:
                self.nb_suspect += 1
            pos[ghost['position']].append(ghost['color'])
        response = self.answer(data)
        bytes_data = json.dumps(response).encode("utf-8")
        protocol.send_json(self.socket, bytes_data)

    def run(self):
        self.connect()
        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print("no message, finished learning")
                self.end = True


p = Player()
p.run()
