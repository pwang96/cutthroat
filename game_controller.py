import game, asyncio, json, uuid
from player import Player


class GameController:

    def __init__(self, debug=False):
        self.waiting_players = {}  # Mapping of Player ID to Player object
        self.active_games = {}  # Mapping of Game ID to Game object
        self.active_players = {}  # Mapping of PlayerID to Game ID
        self.debug = debug

    def new_player(self, name, ws):
        """
        Whenever a player is created, it is automatically added to the waiting area
        :param name:
        :param ws:
        :return:
        """
        p_id = uuid.uuid4().hex

        p = Player(p_id, name, ws)

        self.waiting_players[p_id] = p
        self.send_personal(ws, "handshake", name, p_id)

        self.render_active_games()
        return p

    def player_disconnected(self, player):
        game_id = self.active_players[player.id]
        self.active_games[game_id].player_disconnected(player)
        del self.active_players[player.id]

        if self.active_games[game_id].finished:
            del self.active_games[game_id]

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

        self.render_active_games()

        return self.active_games[game_id]

    def create_new_game(self):
        game_id = uuid.uuid4().hex
        new_game = game.Game(game_id, debug=self.debug)

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
        if self.debug:
            print("(gamecontroller) sending message: " + msg)
        asyncio.ensure_future(ws.send_str(msg))

    def send_all(self, *args):
        # TODO: make this asynchronous, await the send_str
        msg = json.dumps(args)

        if self.debug:
            n = len(self.waiting_players.values())
            print("(gamecontroller) sending message to all ({} players): {}".format(n, msg))
        for player in self.waiting_players.values():
            asyncio.ensure_future(player.ws.send_str(msg))