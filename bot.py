import utils
import initialize
import random
import threading
import time
import bisect


class Bot:
    def __init__(self, player_id):
        self.id = player_id
        self.dictionary = initialize.initialize_bot_dictionary()

    def make_move(self, game):
        """

        :param game: game: an instance of the Cutthroat game
        :return: string: the word it wants to make, empty string for no move
        """
        word_to_play = ""
        potential_points = 0

        words = [(word, player.id) for player in game.players for word in player.words]

        potential_words = self.find_words(words, game.free)
        # TODO: find how to make the bot restart after a player has gone

        if potential_words:
            potential_points, word_to_play = potential_words[0]  # TODO: Change this lol

        if word_to_play:
            t = threading.Thread(target=self.propose_word, args=(game, word_to_play))
            t.daemon = True
            t.start()

        return word_to_play

    def find_words(self, words, free):
        """

        :param words: [(string, int)]: list of tuples of (word, player_id) that are currently on the board
        :param free: [char]: list of free tiles
        :return: [(int, string)]: Sorted list of tuples of (score, word_to_play)
        """
        # TODO: Should this return a list of the best words or just the best word?
        top_words = []

        # try to augment existing words
        for (word, player_id) in words:
            for combo in list(utils.powerset(free))[1:]:
                combined = word + ''.join(combo)
                key = ''.join(sorted(combined))
                if key in self.dictionary:
                    potential_word = random.choice(self.dictionary[key])
                    points = self.calculate_points(potential_word, 0 if player_id != self.id else len(word))
                    bisect.insort(top_words, (points, potential_word))

        # check free chars
        for combo in list(utils.powerset(free))[1:]:
            combined = ''.join(combo)
            key = ''.join(sorted(combined))
            if key in self.dictionary:
                potential_word = random.choice(self.dictionary[key])
                points = self.calculate_points(potential_word, 0)
                bisect.insort(top_words, (points, potential_word))

        return top_words

    def propose_word(self, game, word):
        time.sleep(initialize.BOT_DELAY)
        print("Bot would like to play: {}".format(word))


    def calculate_points(self, word, difference):
        return len(word) - difference
