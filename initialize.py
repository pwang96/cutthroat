import string
import utils
from collections import defaultdict


BOT_DELAY = 4  # seconds for bot delay

def initialize_tiles():
    freq = [13, 3, 3, 6, 18, 3, 4, 3, 12, 2, 2, 5, 3, 8, 11, 3, 2, 9, 6, 9, 6, 3, 3, 2, 3, 2]
    tiles = []
    for i in range(26):
        tiles += [string.ascii_lowercase[i]]*freq[i]

    return tiles


def initialize_dictionary():
    trie = utils.Trie()
    with open('dictionaries/puzzlers_org.txt') as f:
        for line in f:
            line = line.strip()
            if len(line) > 2:
                trie.add(line)

    return trie


def initialize_bot_dictionary():
    d = defaultdict(list)
    with open('dictionaries/puzzlers_org.txt') as f:
        for line in f:
            line = line.strip()
            if len(line) > 2:
                d[''.join(sorted(line))].append(line)

    return d
