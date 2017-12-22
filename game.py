import settings, string, utils, random, json
from player import Player
from collections import Counter
from bot import Bot


class Game:

    def __init__(self):
        self._last_id = 1
        self._players = {}
        self._free_tiles = []
        self._bag = []
        self._word_list = None
        self.bot = None
        self.running = False
        self.finished = False

        self._initialize_dict()

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

    def new_player(self, name, ws):
        """

        :param name: string: name of the player
        :param ws: WebServer
        :return: Player
        """
        player_id = self._last_id
        self._last_id += 1

        p = Player(player_id, name, ws)
        self.send_personal(ws, "handshake", name, player_id)

        self._players[player_id] = p

        return p

    def join(self, player):
        if player.active:
            return
        if len(self._players) >= settings.MAX_PLAYERS:
            self.send_personal(player.ws, "game_full")
            self.update_play_field()
            return

        print(self._players)
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

    def create_bot(self):
        bot_id = self._last_id
        self._last_id += 1

        self.bot = Bot(self, bot_id)

        self.send_all("p_joined", 0, self.bot.name)
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
                if self.bot and pid == self.bot:
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
        print("sending message: " + msg)
        ws.send_str(msg)

    def send_all(self, *args):
        msg = json.dumps(args)
        print("sending message to all: {}".format(msg))
        for player in self._players.values():
            if player.ws:
                player.ws.send_str(msg)

    def draw_tile(self):
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
        self._last_id = 1

    @property
    def free_tiles(self):
        return self._free_tiles

    @property
    def all_words(self):
        words = [(word, player.id, i) for player in self._players.values() for (i, word) in enumerate(player.words)]

        if self.bot:
            words.extend([(word, self.bot.id, i) for (i, word) in enumerate(self.bot.words)])

        return words

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

    def update_play_field(self):
        message = "update"
        free_tiles = self.free_tiles
        player_words = {player.name:player.words for player in self._players.values()}

        if self.bot:
            player_words[self.bot.name] = self.bot.words

        self.send_all(message, free_tiles, player_words)

        self.update_score_field()

        # make the bot think every time the board changes
        if self.bot:
            if not self.bot.thinking:
                self.bot.think()

    def update_score_field(self):
        scores = [[player.name, player.score] for player in self._players.values()]

        if self.bot:
            scores.append([self.bot.name, self.bot.score])

        self.send_all("scores", sorted(scores, key=lambda x: -x[1]))
