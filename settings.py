from collections import defaultdict


MAX_PLAYERS = 3

BOT_DELAY = 4  # seconds for bot delay

TILE_FREQUENCIES = [13, 3, 3, 6, 18, 3, 4, 3, 12, 2, 2, 5, 3, 8, 11, 3, 2, 9, 6, 9, 6, 3, 3, 2, 3, 2]

DICT_FILE = 'dictionaries/puzzlers_org.txt'

GAME_SPEED = 2


def initialize_bot_dictionary():
    d = defaultdict(list)
    with open('dictionaries/puzzlers_org.txt') as f:
        for line in f:
            line = line.strip()
            if len(line) > 2:
                d[''.join(sorted(line))].append(line)

    return d
