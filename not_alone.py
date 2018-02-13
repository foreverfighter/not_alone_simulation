TARGET_CREATURES_HUNTED = {
    2: (7, 13),
    3: (8, 14),
    4: (9, 15),
    5: (10, 16),
    6: (11, 17),
    7: (12, 18)
}

ARTEMIA_SPACES = {
    'A': (-1, -2, -3, -4, -5, -6),
    'B': (-1, -3, -5, -7, -9, -11)
}


class Game:
    """A session of Not Alone."""

    def __init__(self, players, board):
        self.players = players
        self.board = board

    def play(self):
        pass


class Hunted:
    """A Hunted player."""

    def __init__(self, name):
        self.name = name
        self.will = 3
        self.shand = []
        self.phand = []
        self.discard = []
        self.played = None
        self.mind = None

    def __repr__(self):
        return '{}({})'.format(self.name, self.mind)

    def resist(self, will_lost):
        self.will -= will_lost
        for i in range(will_lost * 2):
            self.take_back(somecard)  # placeholder to be based on Hunted.mind

    def give_up(self):
        self.will = 3
        for card in self.discard:
            self.phand.append(card)
        self.discard = []

    def play(self, card, verbose=False):
        self.phand.remove(card)
        self.played.append(card)
        if verbose == True:
            print('{} played {} facedown'.format(self.name, card.name))

    def take_back(self, card, verbose=False):
        self.discard.remove(card)
        self.phand.append(card)
        if verbose == True:
            print('{} takes back {}'.format(self.name, card.name))

    def take_from_reserve(self, card, verbose=False):
        self.phand.append(card)
        if verbose == True:
            print('{} takes {} from the reserve'.format(self.name, card.name))

    def use_power(self, place, verbose=False):
        pass

    def discard(self, card):
        self.phand.remove(card)
        self.discard.append(card)


class Creature:
    """The Creature player."""

    def __init__(self, name):
        self.name = name
        self.hhand = []
        self.hdiscard = []

    def place_token(self, token, place):
        place.tokens.append(token)


class Place:
    """A Place card, either on the board or in a Hunted's phand."""

    def __init__(self, name, text, number):
        self.name = name
        self.text = text
        self.number = number


class S_card:
    """A Survival card."""

    def __init__(self, name, text, number):
        self.name = name
        self.text = text


class H_card:
    """A Hunt card."""

    def __init__(self, name, text, number):
        self.name = name
        self.text = text
