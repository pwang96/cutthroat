from game import *
import threading
import time


class Controller:
    def __init__(self):
        num_players = get_num_players()
        self.game = Game(num_players, num_players==1)
        self.game_bot = None
        if num_players == 1:
            self.game_bot = self.game.players[-1].bot

        self.game_loop()

    def game_loop(self):
        while True:
            if self.game.state == State.DONE:
                if not self.restart_game():
                    break
            elif self.game.state == State.INIT:
                self.display_welcome()
                self.game.state = State.DRAW
            elif self.game.state == State.DRAW:
                tile = self.game.draw_tile()
                if tile:
                    self.update_display()
            elif self.game.state == State.CHANGE:
                t = threading.Thread(target=self.trigger_bot_move)
                t.start()
                self.accept_input()
                t.join()

        self.close_game()

    def update_display(self):
        free = self.game.free
        print("Free characters: {}".format(free))
        for player in self.game.players:
            if player.words:
                print("Player {} has {}".format(player.id, player.words))

    def accept_input(self):
        while True:
            user_input = input(">").strip()
            if user_input == "/next":
                # TODO: send a signal to the bot to stop
                self.game.state = State.DRAW
                break
            elif user_input == "/score":
                self.display_scores()
            elif user_input == '/quit':
                self.game.state = State.DONE
                break
            else:
                player_id = int(input("Which player are you?"))
                while player_id > len(self.game.players):
                    player_id = int(input("Your player number is between 1 and {}\n"
                                          "Which player are you?".format(len(self.game.players))))
                if self.game.propose_word(user_input, player_id):
                    print("\"{}\" is valid".format(user_input))
                    # TODO: maybe send a signal here to the bot to restart
                    self.update_display()
                else:
                    print("Sorry! \"{}\" isn't valid".format(user_input))

    def trigger_bot_move(self):
        self.game_bot.make_move(self.game)

    def display_welcome(self):
        print("Welcome to Cutthroat! Good luck :)")
        print("Player IDs: {}".format([player.id for player in self.game.players]))

    def display_scores(self):
        places = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
        for (player_id, player_score), place in zip(self.game.get_score(), places):
            print("{} Place: Player {} with {} points".format(place, player_id, player_score))

    def restart_game(self):
        print("Final Standings:\n")
        self.display_scores()
        replay = input("Do you want to play again? (y/n)")
        if replay.lower() == 'y':
            self.game.restart()
            return True

        return False

    def close_game(self):
        print("Thank you for playing!")


def get_num_players():
    players = int(input("How many people are playing?"))

    return players