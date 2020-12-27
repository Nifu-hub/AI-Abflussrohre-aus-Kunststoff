import os
import json
import socket
import random
import logging
import builtins
from logging.handlers import RotatingFileHandler

import protocol


class mylist(list):
    '''
        Change builtin list to add indexof method
    '''
    def indexof(self, char):
      try:
        return self.index(char)
      except ValueError:
        return -1
      except Exception as e:
        raise e


builtins.list = mylist


'''
    Global data.
'''
port = 12000
host = 'localhost'
permanents = ['pink']
before = ['purple', 'brown']
mandatory_powers = ['red', 'blue', 'grey']
after = ['black', 'white', 'red', 'blue', 'grey']
phantoms_stats = {'pink': {'suspect': False, 'power': False},
                'blue': {'suspect': False, 'power': False},
                'purple': {'suspect': False, 'power': False},
                'grey': {'suspect': False, 'power': False},
                'white': {'suspect': False, 'power': False},
                'black': {'suspect': False, 'power': False},
                'red': {'suspect': False, 'power': False},
                'brown': {'suspect': False, 'power': False}}

pos = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(),
       5: list(), 6: list(), 7: list(), 8: list(), 9: list()}
passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]


'''
    Set up phantom logging handlers.
'''
phantom_logger = logging.getLogger()
phantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s :: %(levelname)s :: %(message)s', '%H:%M:%S')

os.path.exists('./logs/phantom.log') and os.remove('./logs/phantom.log')
try:
    file_handler = RotatingFileHandler('./logs/phantom.log', 'a', 1000000, 1)
except FileNotFoundError:
    os.mkdir('logs')
    file_handler = RotatingFileHandler('./logs/phantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
phantom_logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
phantom_logger.addHandler(stream_handler)


class Player():
    '''
        Player class manager.
    '''
    def __init__(self):
        self.step = 0
        self.pos = pos.copy()
        self.lock = []
        self.shadow = 0
        self.end = False
        self.phantom = ''
        self.carlotta = -1
        self.nb_suspect = 0

        self.do_cdp = False
        self.next_move = -1
        self.next_answer = -1
        self.use_power = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def possible_movement(self, color, pos_color):
        available_rooms = list()
        charact = {color, pos_color, phantoms_stats[color]['suspect']}
        available_rooms.append(self.get_adjacent_positions(color, pos_color))
        for step in range(1, len(self.pos[pos_color])):
            next_rooms = list()
            for room in available_rooms[step - 1]:
                next_rooms += self.get_adjacent_positions_from_position(room,
                                                                        color)
            available_rooms.append(next_rooms)
        temp = list()
        for sublist in available_rooms:
            for room in sublist:
                temp.append(room)
        temp = set(temp)
        available_positions = list(temp)
        return available_positions

    def get_adjacent_positions(self, color, pos_color):
        if color == 'pink':
            active_passages = pink_passages
        else:
            active_passages = passages
        blocked = {self.lock[0], self.lock[1]}
        return [room for room in active_passages[pos_color]
                if set([room, pos_color]) != set(blocked)]


    def get_adjacent_positions_from_position(self, position, color):
        if color == 'pink':
            active_passages = pink_passages
        else:
            active_passages = passages
        blocked = {self.lock[0], self.lock[1]}
        return [room for room in active_passages[position]
                if set([room, position]) != set(blocked)]

    def is_sus(self, room):
        for player in room:
            if not phantoms_stats[player]["suspect"]:
                return 1
        return 0

    def do_gray_power(self, is_strat2=False):
        if is_strat2:
            max = 0
            saved_room = -1
            phantom_room = -1
            for room in self.pos:
                if self.pos[room].indexof(self.phantom) != -1:
                    phantom_room = room
                if len(self.pos[room]) > max:
                    max = len(self.pos[room])
                    saved_room = room
            if max > 2:
                return saved_room
            return phantom_room
        for room in self.pos:
            if len(self.pos[room]) == 0:
                return room
        return random.randint(0, 9)

    def step0_strat1(self, playerlist):
        playerlist = list(playerlist)
        can_go = True
        not_found = -1
        others = list()
        for player in playerlist:
            if 'color' in player and player['color'] == self.phantom:
                self.next_answer = playerlist.indexof(player)
            else:
                others.append(player['color'])
        if self.next_answer != -1:
            moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
            for room in self.pos:
                if moves.indexof(room) != -1 and len(self.pos[room]) > 0 and self.shadow != room:
                    if set(others) & set(self.pos[room]):
                        can_go = False
                    elif self.shadow != room and self.is_sus(self.pos[room]):
                        can_go = False
                        not_found = room
                    if can_go and not_found == -1:
                        self.next_move = moves.indexof(room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power()
                        return 0
            if not_found != -1:
                self.next_move = moves.indexof(not_found)
            else:
                self.next_move = random.randint(0, len(moves) - 1)
                while moves.indexof(self.next_move) == -1 and self.next_move > 0:
                    self.next_move = random.randint(0, len(moves) - 1)
            if playerlist[self.next_answer]['color'] == 'gray':
                use_power = do_gray_power()
            return 0
        else:
            return self.step1_strat1(playerlist, others)

    def step1_strat1(self, playerlist, others):
        phantom_room = -1
        for room in self.pos:
            if self.pos[room].indexof(self.phantom) != -1:
                phantom_room = room
            if len(self.pos[room]) == 1 and self.shadow != room and self.pos[room].indexof(self.phantom) != -1:
                for player in playerlist:
                    self.next_answer = playerlist.indexof(player)
                    moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                    if moves.indexof(phantom_room) != -1:
                        self.next_move = moves.indexof(phantom_room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power()
                        return 1
                return self.step1_strat2(playerlist, others)
            elif len(self.pos[room]) > 1 and self.pos[room].indexof(self.phantom) != -1 and len(self.pos[room]) > len(set(others) & set(self.pos[room])):
                return self.step2_strat1(playerlist, others)
        if self.pos[room].indexof(self.phantom) != -1:
            priority = ['gray', 'blue', 'purple', 'pink', 'red', 'brown']
            for guy in priority:
                if others.indexof(guy) == -1:
                    pass
                else:
                    self.next_answer = others.indexof(guy)
                    moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                    if moves.indexof(phantom_room) != -1:
                        self.next_move = moves.indexof(phantom_room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power()
                        return 1
        return self.step1_strat2(playerlist, others)

    def step2_strat1(self, playerlist, others):
        if others.indexof('white') != -1:
            self.next_answer = others.indexof('white')
            moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
            for room in self.pos:
                if moves.indexof(room) != -1 and len(self.pos[room]) > 0 and not set(others) & set(self.pos[room]):
                    self.next_move = moves.indexof(room)
                elif moves.indexof(room) != -1 and len(self.pos[room]) > 0:
                    self.next_move = moves.indexof(room)
                else:
                    self.next_move = 0
        else:
            return self.step3_strat1(playerlist, others)
        return 2

    def step3_strat1(self, playerlist, others):
        if others.indexof('black') != -1:
            self.next_answer = others.indexof('black')
            moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
            for room in self.pos:
                if moves.indexof(room) != -1 and len(self.pos[room]) > 0 and not set(others) & set(self.pos[room]):
                    self.next_move = moves.indexof(room)
                elif moves.indexof(room) != -1 and len(self.pos[room]) > 0:
                    self.next_move = moves.indexof(room)
                else:
                    self.next_move = 0
        else:
            return self.step4_strat1(playerlist, others)
        self.use_power = 1
        return 3

    def step4_strat1(self, playerlist, others):
        priority = ['gray', 'blue', 'purple', 'pink', 'red', 'brown']
        for guy in priority:
            if others.indexof(guy) == -1:
                pass
            else:
                self.next_answer = others.indexof(guy)
                moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                for room in self.pos:
                    if moves.indexof(room) != -1 and len(self.pos[room]) > 0 and not set(others) & set(self.pos[room]) and self.is_sus(self.pos[room]):
                        self.next_move = moves.indexof(room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power()
                        return 4
        for player in playerlist:
            moves = self.possible_movement(player['color'], player['position'])
            if moves.indexof(player['position']) != -1:
                self.next_move = moves.indexof(player['position'])
                self.do_cdp = True
                self.next_answer = playerlist.indexof(player)
                if playerlist[self.next_answer]['color'] == 'gray':
                    use_power = do_gray_power()
                return 4
        return self.step5_strat1(playerlist, others)

    def step5_strat1(self, playerlist, others):
        priority = ['gray', 'blue', 'purple', 'pink', 'red', 'brown']
        for guy in priority:
            if others.indexof(guy) == -1:
                pass
            else:
                self.next_answer = others.indexof(guy)
                moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                for room in self.pos:
                    if moves.indexof(room) != -1 and len(self.pos[room]) > 0 and not set(others) & set(self.pos[room]):
                        self.next_move = moves.indexof(room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power()
                        return 5
        for player in playerlist:
            moves = self.possible_movement(player['color'], player['position'])
            if moves.indexof(player['position']) != -1:
                self.next_move = moves.indexof(player['position'])
                self.do_cdp = True
                self.next_answer = playerlist.indexof(player)
                if playerlist[self.next_answer]['color'] == 'gray':
                    use_power = do_gray_power()
                return 5
        self.next_answer = 0
        rand = random.randint(0, len(playerlist) - 1)
        moves = self.possible_movement(playerlist[rand]['color'], playerlist[rand]['position'])
        self.next_move = moves.indexof(playerlist[rand]['position'])
        if playerlist[self.next_answer]['color'] == 'gray':
            use_power = do_gray_power()
        return 5

    def step1_strat2(self, playerlist, others):
        if others.indexof('black') != -1:
            self.next_answer = others.indexof('black')
            moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
            for room in self.pos:
                if moves.indexof(room) != -1 and len(self.pos[room]) == 0:
                    self.next_move = moves.indexof(room)
                    return 6
        return self.step2_strat2(playerlist, others)

    def step2_strat2(self, playerlist, others):
        if others.indexof('white') != -1:
            self.next_answer = others.indexof('white')
            moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
            for room in self.pos:
                if moves.indexof(room) != -1 and len(self.pos[room]) == 0:
                    self.next_move = moves.indexof(room)
                    self.use_power = 0
                    return 7
        return self.step3_strat2(playerlist, others)

    def step3_strat2(self, playerlist, others):
        priority = ['gray', 'red', 'blue', 'brown', 'purple', 'pink']
        for guy in priority:
            if others.indexof(guy) == -1:
                pass
            else:
                self.next_answer = others.indexof(guy)
                moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                for room in self.pos:
                    if (moves.indexof(room) != -1 and len(self.pos[room]) == 0) or playerlist[self.next_answer]['color'] == 'gray':
                        self.next_move = moves.indexof(room)
                        if playerlist[self.next_answer]['color'] == 'gray':
                            use_power = do_gray_power(True)
                        return 8
        return self.step4_strat2(playerlist, others)

    def step4_strat2(self, playerlist, others):
        priority = ['red', 'blue', 'brown', 'purple', 'pink']
        for guy in priority:
            if others.indexof(guy) == -1:
                pass
            else:
                self.next_answer = others.indexof(guy)
                moves = self.possible_movement(playerlist[self.next_answer]['color'], playerlist[self.next_answer]['position'])
                for room in self.pos:
                    if (moves.indexof(room) != -1 and len(self.pos[room]) == 0) or room == self.shadow:
                        self.next_move = moves.indexof(room)
                        return 9
        self.next_move = 0
        self.use_power = 0
        self.next_answer = 0
        return 9

    def answer(self, question):
        data = question['data']
        game_state = question['game state']
        response_index = 0
        phantom_logger.debug('|\n|')
        phantom_logger.debug('phantom answers')
        phantom_logger.debug(f'question type ----- {question["question type"]}')
        phantom_logger.debug(f'data -------------- {data}')
        phantom_logger.debug(f'response index ---- {response_index}')
        phantom_logger.debug(f'response ---------- {data[response_index]}')
        if question['question type'] == 'select character':
            return self.next_answer
        elif question['question type'] == 'select position':
            return self.next_move
        else:
            return self.use_power

    def handle_json(self, data):
        data = json.loads(data)
        if data['question type'] == 'select character':
            self.step = 1
            self.do_cdp = False
            self.next_move = -1
            self.next_answer = -1
            self.use_power = 0
        else:
            self.step = self.step + 1
        self.carlotta = data['game state']['position_carlotta']
        self.lock = data['game state']['blocked']
        self.phantom = data['game state']['fantom']
        self.shadow = data['game state']['shadow']
        for i in self.pos:
            self.pos[i].clear()
        self.nb_suspect = 0
        for phantom in data['game state']['characters']:
            phantoms_stats[phantom['color']]['power'] = phantom['power']
            phantoms_stats[phantom['color']]['suspect'] = phantom['suspect']
            if phantom['suspect'] is True:
                self.nb_suspect += 1
            self.pos[phantom['position']].append(phantom['color'])
        response = self.answer(data)
        bytes_data = json.dumps(response).encode('utf-8')
        protocol.send_json(self.socket, bytes_data)

    def run(self):
        self.connect()
        while self.end is not True:
            received_message = protocol.receive_json(self.socket)
            if received_message:
                self.handle_json(received_message)
            else:
                print('no message, finished learning')
                self.end = True


p = Player()
p.run()
