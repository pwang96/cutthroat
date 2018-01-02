import game, asyncio, json
from player import Player


class GameController:

    def __init__(self):
        self._last_game_id = 0
        self._last_player_id = 0
        self.waiting_players = {}  # Mapping of Player ID to Player object
        self.active_games = {}  # Mapping of Game ID to Game object
        self.active_players = {}  # Mapping of PlayerID to Game ID

    def new_player(self, name, ws):
        """
        Whenever a player is created, it is automatically added to the waiting area
        :param name:
        :param ws:
        :return:
        """
        self._last_player_id += 1
        p_id = self._last_player_id

        p = Player(p_id, name, ws)

        self.waiting_players[p_id] = p
        self.send_personal(ws, "handshake", name, p_id)

        self.render_active_games()
        return p

    def disconnected_player(self, player):
        game_id = self.active_players[player.id]
        self.active_games[game_id].player_disconnected(player)
        del self.active_players[player.id]

    def add_to_waiting_area(self, player):
        self.waiting_players[player.id] = player

    def add_to_existing_game(self, game_id, player):
        """
        Adds a player to the game with id = game_id
        :param game_id:
        :param player:
        :return: Game instance
        """
        self.active_games[game_id].join(player)
        del self.waiting_players[player.id]
        self.active_players[player.id] = game_id

        self.send_personal(player.ws, "joined_game")

        return self.active_games[game_id]

    def create_new_game(self):
        self._last_game_id += 1
        game_id = self._last_game_id
        new_game = game.Game(game_id)

        self.active_games[game_id] = new_game

        return new_game

    def terminate_game(self, game_id):
        """
        Happens when there are 0 players left in a game.
        :param game_id:
        :return:
        """
        del self.active_games[game_id]

    def render_active_games(self):
        games = {}
        for g_id, g in self.active_games.items():
            players = [player.name for player in g.players.values()]
            games[g_id] = players

        message = "render_active_games"
        self.send_all(message, games)

    def send_personal(self, ws, *args):
        msg = json.dumps(args)
        print("sending message: " + msg)
        asyncio.ensure_future(ws.send_str(msg))

    def send_all(self, *args):
        # TODO: make this asynchronous, await the send_str
        msg = json.dumps(args)
        print("sending message to all: {}".format(msg))
        for player in self.waiting_players.values():
            if player.ws:
                asyncio.ensure_future(player.ws.send_str(msg))