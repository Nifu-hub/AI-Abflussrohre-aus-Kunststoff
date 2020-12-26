import os
import json
import socket
import random
import logging
from logging.handlers import RotatingFileHandler

import protocol


'''
    Global data.
'''
lock = []
fantom = ''
port = 12000
carlotta = -1
host = 'localhost'
permanents = {'pink'}
before = {'purple', 'brown'}
mandatory_powers = ['red', 'blue', 'grey']
after = {'black', 'white', 'red', 'blue', 'grey'}
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
    Set up fantom logging handlers.
'''
fantom_logger = logging.getLogger()
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s :: %(levelname)s :: %(message)s', '%H:%M:%S')

os.path.exists('./logs/fantom.log') and os.remove('./logs/fantom.log')
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():
    '''
        Player class manager.
    '''
    def __init__(self):
        self.step = 0
        self.end = False
        self.next_rep = []
        self.nb_suspect = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.socket.connect((host, port))

    def reset(self):
        self.socket.close()

    def calc_isolate_suspect(self, data):
        return 2

    def strategy_one(self, data):
        return 0

    def strategy_two(self, data):
        return 0

    def calc_answer(self, data):
        if self.nb_suspect / 2 <= self.calc_isolate_suspect(data):
            answer = self.strategy_one(data)
        else:
            answer = self.strategy_two(data)
        self.next_rep = [0, 0, 0, 0]
        return answer

    def answer(self, question):
        print(question)
        data = question['data']
        game_state = question['game state']
        if self.step == 1:
            response = self.calc_answer(question)
        else:
            response = self.next_rep[0]
            del self.next_rep[0]
        response_index = data.index(response)
        # log
        fantom_logger.debug('|\n|')
        fantom_logger.debug('fantom answers')
        fantom_logger.debug(f'question type ----- {question['question type']}')
        fantom_logger.debug(f'data -------------- {data}')
        fantom_logger.debug(f'response index ---- {response_index}')
        fantom_logger.debug(f'response ---------- {data[response_index]}')
        print('----------------------- REPONSE -----------------------------')
        print(response)
        print(data)
        print(response_index)
        print('-------------------- END REPONSE ----------------------------')
        return response_index

    def handle_json(self, data):
        data = json.loads(data)
        print(data)
        print('step :')
        print(self.step)
        if data['question type'] == 'select character':
            self.step = 1
        else:
            self.step = self.step + 1
        carlotta = data['game state']['position_carlotta']
        lock = data['game state']['blocked']
        fantom = data['game state']['fantom']
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
