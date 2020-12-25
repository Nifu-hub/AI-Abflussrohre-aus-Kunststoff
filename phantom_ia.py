import json
import logging
import os
import random
import socket
from logging.handlers import RotatingFileHandler

import protocol

host = "localhost"
port = 12000
# HEADERSIZE = 10

"""
    game data
"""
# determines whether the power of the character is used before
# or after moving
permanents = {"pink"}
before = {"purple", "brown"}
after = {"black", "white", "red", "blue", "grey"}

mandatory_powers = ["red", "blue", "grey"]

# Ghost info color, suspect, power
ghosts_stats =  {"pink": {"suspect": False, "power": False},
                "blue": {"suspect": False, "power": False},
                "purple": {"suspect": False, "power": False},
                "grey": {"suspect": False, "power": False},
                "white": {"suspect": False, "power": False},
                "black": {"suspect": False, "power": False},
                "red": {"suspect": False, "power": False},
                "brown": {"suspect": False, "power": False}}

# Informations per case of the map
pos = { 0: [],
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: [],
        8: [],
        9: []}

lock = []

fantom = ""

carlotta = -1

# ways between rooms
# rooms are numbered
# from right to left
# from bottom to top
# 0 ---> 9
passages = [{1, 4}, {0, 2}, {1, 3}, {2, 7}, {0, 5, 8},
            {4, 6}, {5, 7}, {3, 6, 9}, {4, 9}, {7, 8}]
# ways for the pink character
pink_passages = [{1, 4}, {0, 2, 5, 7}, {1, 3, 6}, {2, 7}, {0, 5, 8, 9},
                 {4, 6, 1, 8}, {5, 7, 2, 9}, {3, 6, 9, 1}, {4, 9, 5},
                 {7, 8, 4, 6}]


"""
set up fantom logging
"""
fantom_logger = logging.getLogger()
print(fantom_logger)
fantom_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s :: %(levelname)s :: %(message)s", "%H:%M:%S")
# file
if os.path.exists("./logs/fantom.log"):
    os.remove("./logs/fantom.log")
file_handler = RotatingFileHandler('./logs/fantom.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
fantom_logger.addHandler(file_handler)
# stream
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
fantom_logger.addHandler(stream_handler)


class Player():

    def __init__(self):

        self.end = False
        self.nb_suspect = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.step = 0
        self.next_rep = []

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
        if self.nb_suspect / 2 <= calc_isolate_suspect(data):
            answer = strategy_one(data)
        else:
            answer = strategy_two(data)
        self.next_rep = [0, 0, 0, 0]
        return answer

    def answer(self, question):
        # work
        print(question)
        data = question["data"]
        game_state = question["game state"]
        if self.step == 1:
            response_index = self.calc_answer(question)
        else:
            response_index = self.next_rep[0]
            del self.next_rep[0]
        response_index = random.randint(0, len(data)-1)
        # log
        fantom_logger.debug("|\n|")
        fantom_logger.debug("fantom answers")
        fantom_logger.debug(f"question type ----- {question['question type']}")
        fantom_logger.debug(f"data -------------- {data}")
        fantom_logger.debug(f"response index ---- {response_index}")
        fantom_logger.debug(f"response ---------- {data[response_index]}")
        print("------------------------------ REPONSE ------------------------------------")
        print(response_index)
        print("---------------------------- END REPONSE ----------------------------------")
        return response_index

    def handle_json(self, data):
        data = json.loads(data)

        print(data)
        print('step :')
        print(self.step)
        if data["question type"] == 'select character':
            self.step = 1
        else:
            self.step = self.step + 1
        #print('step 2')
        # save data
        carlotta = data["game state"]["position_carlotta"]
        lock = data["game state"]["blocked"]
        fantom = data["game state"]["fantom"]
        for x in pos:
            pos[x] = []
        self.nb_suspect = 0
        for ghost in data["game state"]["characters"]:
            ghosts_stats[ghost["color"]]["power"] = ghost["power"]
            ghosts_stats[ghost["color"]]["suspect"] = ghost["suspect"]
            if ghost["suspect"] == True:
                self.nb_suspect += 1
            pos[ghost["position"]].append(ghost["color"])
        # get the answer
        response = self.answer(data)
        # send back to server
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
