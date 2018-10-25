import settings, string, utils, random, json
import asyncio
from collections import Counter
from bot import Bot


class Game:

    def __init__(self, game_id, debug=False):
        self.game_id = game_id
        self._last_id = 0
        self._players = {}
        self._free_tiles = []
        self._bag = []
        self._word_list = None
        self.bot = None
        self.running = False
        self.finished = False
        self.debug = debug

        self._initialize_dict()
        self._initialize_bag()

    def _initialize_bag(self):
        freq = settings.TILE_FREQUENCIES
        self._bag = []
        for i in range(26):
            self._bag += [string.ascii_lowercase[i]] * freq[i]

    def _initialize_dict(self):
        self._word_list = utils.Trie()
        with open(settings.DICT_FILE) as f:
            for line in f:
                line = line.strip()
                if len(line) > 2:
                    self._word_list.add(line)

    @property
    def free_tiles(self):
        """Returns the list of free tiles in play"""
        return self._free_tiles

    @property
    def all_words(self):
        """Returns the list of all words in play"""
        words = [(word, player.id, i) for player in self.players.values() for (i, word) in enumerate(player.words)]

        if self.bot:
            words.extend([(word, self.bot.id, i) for (i, word) in enumerate(self.bot.words)])

        return words

    @property
    def players(self):
        return self._players

    @property
    def bag(self):
        return self._bag

    def add_player(self, player):
        """

        :param player:
        :return:
        """
        self._players[player.id] = player

    def join(self, player):
        if player.id not in self._players:
            self.add_player(player)

        if player.active:
            # should never happen because the join button should be disabled
            if self.debug:
                print("ERROR: active player joining a game")
            return
        if len(self._players) >= settings.MAX_PLAYERS:
            self.send_personal(player.ws, "game_full")
            return

        if self.debug:
            print(str(self._players))
            if self.bot:
                print(self.bot)

        player.active = True
        self.send_all("p_joined", player.id, player.name)
        self.update_play_field()

    def player_disconnected(self, player):
        player.ws = None
        name = player.name
        del self._players[player.id]
        del player
        self.send_all("dc", name)

        self.update_play_field()
        if len(self._players) == 0:
            self.finished = True

    def create_bot(self):
        if self.bot:
            self.bot = None
        self._last_id += 1
        bot_id = self._last_id
        while bot_id in self._players:
            self._last_id += 1
            bot_id = self._last_id

        self.bot = Bot(self, bot_id)

        self.send_all("p_joined", 0, self.bot.name)
        self.update_play_field()

    def remove_bot(self):
        if not self.bot:
            return None
        name = self.bot.name
        self.bot = None

        self.send_all("dc", name)
        self.update_play_field()

    def play_word(self, word, player):
        """

        :param word: string: proposed word
        :param player: Player: player who proposed the word
        :return: bool: if word was accepted or not
        """
        pid, index, used_chars = self.is_valid(word)
        if pid != -1:
            # delete used_chars from free
            for c in used_chars:
                self._free_tiles.remove(c)

            # update player scores
            new_word_length = len(word)
            player.score += new_word_length
            if pid != 0:
                if self.bot and pid == self.bot.id:
                    old_word_length = len(self.bot.words[index])
                    self.bot.score -= old_word_length
                else:
                    old_word_length = len(self._players[pid].words[index])
                    self._players[pid].score -= old_word_length

            # update the player word lists
            player.words.append(word)
            if pid != 0:
                if self.bot and pid == self.bot.id:
                    del self.bot.words[index]
                else:
                    del self._players[pid].words[index]

            self.update_play_field()

            self.send_all("valid_word", word, player.name)
            return True

        self.send_personal(player.ws, "invalid_word", word)
        return False

    def send_personal(self, ws, *args):
        msg = json.dumps(args)
        if self.debug:
            print("sending message: " + msg)
        asyncio.ensure_future(ws.send_str(msg))

    def send_all(self, *args):
        # TODO: make this asynchronous, await the send_str
        msg = json.dumps(args)
        if self.debug:
            print("sending message to all: {}".format(msg))
        for player in self._players.values():
            asyncio.ensure_future(player.ws.send_str(msg))
            # if player.ws:
            #     asyncio.ensure_future(player.ws.send_str(msg))
            #     print('sent to {}'.format(player))

    def draw_tile(self, player):
        if self.debug:
            print("{} drew a tile".format(player.name))
        if len(self._bag) == 0:
            self.finished = True
            return
        tile = random.choice(self._bag)
        self._bag.remove(tile)
        self._free_tiles.append(tile)
        self.update_play_field()

    def reset(self):
        self._initialize_bag()
        self._free_tiles = []
        self._last_id = 0

    def is_valid(self, proposed_word):
        """
        Checks if the word is valid or not. Checks if it is in the dictionary and if
        it can be built with the words/characters already in play.
        Returns a tuple with the following information:
        (player_id, index, combo), where
        player_id: either the player id, 0 for free words, and -1 for invalid words
        index: index of the base word in player_id's list of words. For free words and invalid words, index = -1
        combo: tuple of the characters used from free
        :param proposed_word: string
        :return: (int, int, tuple):
        """
        if not self._word_list.has_word(proposed_word):
            return -1, -1, ()

        proposed_word_counter = Counter(proposed_word)

        words = self.all_words
        powerset = list(utils.powerset(self._free_tiles))[1:]

        # check all existing words + free chars
        for (word, player_id, index) in words:
            if len(word) < len(proposed_word):
                for combo in powerset:
                    if Counter(word + ''.join(combo)) == proposed_word_counter:
                        return player_id, index, combo

        # check free chars
        if len(proposed_word) <= len(self._free_tiles):
            for combo in powerset:
                if Counter(combo) == proposed_word_counter:
                    return 0, -1, combo

        return -1, -1, ()

    def update_current_players(self, ws):
        message = "update_names"
        names = [player.name for player in self._players.values() if player.active]

        self.send_personal(ws, message, names)

    def get_updated_play_field_payload(self):
        message = "update"
        num_tiles_left = len(self._bag)
        free_tiles = self.free_tiles
        player_words = {player.name: player.words for player in self._players.values() if player.active}

        if self.bot:
            player_words[self.bot.name] = self.bot.words

        return message, free_tiles, num_tiles_left, player_words

    def update_play_field(self):
        message, free_tiles, num_tiles_left, player_words = self.get_updated_play_field_payload()

        self.send_all(message, free_tiles, num_tiles_left, player_words)

        self.update_score_field()

        # make the bot think every time the board changes
        if self.bot:
            if self.bot.thinking:
                self.bot.interrupted = True  # TODO: fix the bugginess of this
            else:
                self.bot.think()

    def update_score_field(self):
        scores = [[player.name, player.score] for player in self._players.values() if player.active]

        if self.bot:
            scores.append([self.bot.name, self.bot.score])

        self.send_all("scores", sorted(scores, key=lambda x: -x[1]))

    def is_ready(self):
        """The game is okay to start"""
        return not any((self._last_id, len(self._free_tiles), len(self._players)))
