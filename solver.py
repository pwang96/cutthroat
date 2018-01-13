import utils, settings, random
from collections import defaultdict


class Solver:

    def __init__(self):
        self.words = []
        self.letters = []
        self.dictionary = None

        self.initialize_dictionary()

    def initialize_dictionary(self):
        self.dictionary = defaultdict(list)
        with open(settings.DICT_FILE) as f:
            for line in f:
                line = line.strip()
                if len(line) > 2:
                    self.dictionary[''.join(sorted(line))].append(line)

    def flip_tile(self, tile):
        self.letters.append(tile)

    def add_word(self, word):
        self.words.append(word)

    def solve(self):
        top_word = ""
        used = ()

        # try to augment existing words
        for word in self.words:
            for combo in list(utils.powerset(self.letters))[1:]:
                combined = word + ''.join(combo)
                key = ''.join(sorted(combined))
                if key in self.dictionary:
                    potential_word = random.choice(self.dictionary[key])
                    if len(potential_word) > len(top_word):
                        top_word = potential_word
                        used = combo

        # check free chars
        for combo in list(utils.powerset(self.letters))[1:]:
            combined = ''.join(combo)
            key = ''.join(sorted(combined))
            if key in self.dictionary:
                potential_word = random.choice(self.dictionary[key])
                if len(potential_word) > len(top_word):
                    top_word = potential_word
                    used = combo

        for c in used:
            self.letters.remove(c)

        return top_word

if __name__ == "__main__":
    solver = Solver()
    while True:
        x = input(">")
        if len(x) < 2:
            solver.flip_tile(x)
        else:
            solver.add_word(x)

        print(solver.solve())
