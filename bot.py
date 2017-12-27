import settings
import asyncio
from collections import defaultdict
import utils
import random


class Bot:

    def __init__(self, game, bot_id):
        self.id = bot_id
        self.name = settings.BOT_NAME
        self.words = []
        self.score = 0
        self.game = game
        self.thinking = False
        self.dictionary = None
        self.interrupted = False

        self.initialize_dictionary()

    def __str__(self):
        return "Bot: {}, ID: {}".format(self.name, self.id)

    def think(self):
        print("bot is thinking for {} sec".format(settings.BOT_DELAY))

        asyncio.ensure_future(self.play_word())

        print("bot is done thinking")

    def initialize_dictionary(self):
        self.dictionary = defaultdict(list)
        with open(settings.DICT_FILE) as f:
            for line in f:
                line = line.strip()
                if len(line) > 2:
                    self.dictionary[''.join(sorted(line))].append(line)

    async def play_word(self):
        """
        Waits the delay, finds a word and plays it.
        """
        self.thinking = True
        await asyncio.sleep(settings.BOT_DELAY)
        self.thinking = False

        words = self.game.all_words
        free = self.game.free_tiles
        top_word = ""
        max_points = 0
        pid = 0
        index = 0
        used_chars = ()

        if self.interrupted:
            self.interrupted = False
            self.thinking = False
            return

        # try to augment existing words
        for (word, player_id, i) in words:
            for combo in list(utils.powerset(free))[1:]:
                combined = word + ''.join(combo)
                key = ''.join(sorted(combined))
                if key in self.dictionary:
                    potential_word = random.choice(self.dictionary[key])
                    points = self.calculate_points(potential_word, 0 if player_id != self.id else len(word))
                    if points > max_points:
                        print(potential_word)
                        top_word, max_points = potential_word, points
                        pid, index, used_chars = player_id, i, combo

        # check free chars
        for combo in list(utils.powerset(free))[1:]:
            combined = ''.join(combo)
            key = ''.join(sorted(combined))
            if key in self.dictionary:
                potential_word = random.choice(self.dictionary[key])
                points = self.calculate_points(potential_word, 0)
                if points > max_points:
                    print(potential_word)
                    top_word, max_points = potential_word, points
                    pid, index, used_chars = 0, -1, combo

        ##########
        if not top_word:
            return

        if pid != -1:
            # delete used_chars from free
            for c in used_chars:
                self.game.free_tiles.remove(c)

            # update scores
            new_word_length = len(top_word)
            self.score += new_word_length
            if pid != 0 and pid != self.id:
                old_word_length = len(self.game.players[pid].words[index])
                self.game.players[pid].score -= old_word_length
            elif pid != 0 and pid == self.id:
                old_word_length = len(self.words[index])
                self.score -= old_word_length

            # update the player word lists
            self.words.append(top_word)
            if pid != 0:
                if pid == self.id:
                    del self.words[index]
                else:
                    del self.game.players[pid].words[index]

            self.game.update_play_field()

            self.game.send_all("valid_word", top_word, self.name)

    def calculate_points(self, word, difference):
        return len(word) - difference
