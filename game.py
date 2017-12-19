import initialize
import random
from bot import Bot
import utils
from collections import Counter
from enum import Enum


class Game:
    def __init__(self, num_players, bots=False):
        # initialize players
        self.players = []
        for p in range(1, num_players+1):
            self.players.append(Player(p))
        if bots:
            self.players.append(Player(num_players+1, True))

        # initialize game variables
        self.free = []
        self.tiles = initialize.initialize_tiles()
        self.word_list = initialize.initialize_dictionary()
        self.state = State.INIT

    def draw_tile(self):
        """
        Draws a random tile and adds it to the free pile
        :return: char: tile
        """
        if not self.tiles:
            self.state = State.DONE
            return None

        tile = random.choice(self.tiles)
        self.free.append(tile)
        self.tiles.remove(tile)

        self.state = State.CHANGE

        return tile

    def is_valid(self, proposed_word):
        """
        Checks if the word is valid or not. Checks if it is in the dictionary and if
        it can be built with the words/characters already in play.
        Returns the player ID of the word used to make the new word, or -1 is the word is not valid.
        If the word was made from the free tiles, 0 is returned. Also returns the base of the word
        :param proposed_word: string
        :return: (int, string):
        """
        if not self.word_list.has_word(proposed_word):
            return -1

        proposed_word_counter = Counter(proposed_word)

        words = [(word, player.id) for player in self.players for word in player.words]

        # check all existing words + free chars
        for (word, player_id) in words:
            if len(word) < len(proposed_word):
                for combo in list(utils.powerset(self.free))[1:]:
                    if Counter(word + ''.join(combo)) == proposed_word_counter:
                        for c in combo:
                            self.free.remove(c)
                        return player_id, word

        # check free chars
        if len(proposed_word) <= len(self.free):
            for combo in list(utils.powerset(self.free))[1:]:
                if Counter(combo) == proposed_word_counter:
                    for c in combo:
                        self.free.remove(c)
                    return 0, ""

        return -1, ""

    def propose_word(self, word, player_id):
        """

        :param word: string: proposed word
        :param player_id: int: player id
        :return: bool: if word was accepted or not
        """
        pid, base = self.is_valid(word)
        if pid != -1:
            self.players[player_id-1].words.append(word)
            self.update_player_score(player_id, pid, word)
            if pid != 0:
                self.players[pid-1].words.remove(base)
            return True

        return False

    def get_score(self):
        return sorted(((player.id, player.score) for player in self.players), key=lambda t: -t[1])

    def update_player_score(self, player_id, word_owner_id, word):
        """
        Updates the player scores
        :param player_id: int: The id of the player who made the new word
        :param word_owner_id: int: The id of the player whose word was augmented
        :param word: string: the actual word
        :return: None
        """
        if word_owner_id == 0:
            self.players[player_id-1].score += len(word)
        elif word_owner_id == player_id:
            for w in self.players[player_id-1].words:
                if utils.is_augmentation(w, word):
                    self.players[player_id-1].score += len(word) - len(w)
        else:
            for w in self.players[word_owner_id-1].words:
                if utils.is_augmentation(w, word):
                    self.players[player_id-1].score += len(word)
                    self.players[word_owner_id-1].score -= len(w)

    def restart(self):
        self.tiles = initialize.initialize_tiles()
        self.state = State.INIT
        self.free = []
        for player in self.players:
            player.restart()


class Player:
    def __init__(self, pid, is_bot=False):
        self.id = pid
        self.score = 0
        self.words = []
        self.bot = None
        if is_bot:
            self.bot = Bot(self.id)

    def restart(self):
        self.score = 0
        self.words = []


class State(Enum):
    INIT = 0
    DRAW = 1
    CHANGE = 2
    DONE = 3
