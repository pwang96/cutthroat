class Player:

    def __init__(self, player_id, name, ws):
        """

        :param player_id: int: assigned ID
        :param name: string: friendly name
        :param ws: WebServer
        """
        self.id = player_id
        self.name = name
        self.ws = ws
        self.words = []
        self.score = 0
        self.active = False

    def __str__(self):
        return "Name={}, Score={}".format(self.name, self.score)

    def __repr__(self):
        return self.__str__()