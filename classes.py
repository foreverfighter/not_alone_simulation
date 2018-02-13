# TO DO
# log game actions
# give each game a unique ID for logging checks

# add hunt card effects
# add survival card effects


# csv for writing the results
# collections for Counter to count stats
import csv
import logging
import random
import collections

# logger 1, for logging to games.log
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s:%(message)s')

file_handler = logging.FileHandler('games.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# logger 2, for logging to the console
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


class Game:
    """A session of Not Alone."""

    # how many spaces it takes the creature / hunted to win, based on how many players there are
    GOAL_CREATURE_HUNTED = {
        2: (7, 13),
        3: (8, 14),
        4: (9, 15),
        5: (10, 16),
        6: (11, 17),
        7: (12, 18)
    }

    # which spaces(relative to the creature's goal) have artemia icons on them
    ARTEMIA_SPACES = {
        'A': (1, 2, 3, 4, 5, 6),
        'B': (1, 3, 5, 7, 9, 11)
    }

    # number of copies of place cards for each number of hunted
    PLACE_CARD_COPIES = {
        1: 1,
        2: 2,
        3: 2,
        4: 3,
        5: 3,
        6: 3
    }

    def __init__(self, players, verbose=False):
        if not 2 <= int(players) <= 7:
            logger.info('Not Alone needs 2-7 players.')
            return

        # add possible player names from external file
        with open('player_names.csv', 'r', newline='') as f:
            reader = csv.reader(f)
            self.player_names = [row[0] for row in reader]

        # create a creature with a random player name
        chosen_name = random.choice(self.player_names)
        self.creature = Creature(chosen_name, self)  # to insert mind
        self.player_names.remove(chosen_name)

        # create each hunted player, to separate setup from init
        self.hunted = []
        for i in range(int(players) - 1):
            chosen_name = random.choice(self.player_names)
            self.hunted.append(Hunted(chosen_name, self))
            self.hunted[i].phand.append(place_cards['The Lair'])
            self.hunted[i].phand.append(place_cards['The Jungle'])
            self.hunted[i].phand.append(place_cards['The River'])
            self.hunted[i].phand.append(place_cards['The Beach'])
            self.hunted[i].phand.append(place_cards['The Rover'])
            self.player_names.remove(chosen_name)

        # create reserve deck of place cards based on number of hunted
        self.reserve = []
        for i in range(Game.PLACE_CARD_COPIES[len(self.hunted)]):
            self.reserve.append(place_cards['The Swamp'])
            self.reserve.append(place_cards['The Shelter'])
            self.reserve.append(place_cards['The Wreck'])
            self.reserve.append(place_cards['The Source'])
            self.reserve.append(place_cards['The Artefact'])

        # create the board
        self.board = []
        self.board.append(place_cards['The Lair'])
        self.board.append(place_cards['The Jungle'])
        self.board.append(place_cards['The River'])
        self.board.append(place_cards['The Beach'])
        self.board.append(place_cards['The Rover'])
        self.board.append(place_cards['The Swamp'])
        self.board.append(place_cards['The Shelter'])
        self.board.append(place_cards['The Wreck'])
        self.board.append(place_cards['The Source'])
        self.board.append(place_cards['The Artefact'])

        # randomize board for side A/B artemia icons
        self.artemia = random.choice(['A', 'B'])

        self.survival_deck = [survival_cards[key] for key in survival_cards]
        self.survival_discard = []
        self.hunt_deck = [hunt_cards[key] for key in hunt_cards]

        # beach and wreck variables
        self.beach_marker_on = False
        self.beach_proced_in_turn = False
        self.wreck_proced_in_turn = False

        # hunt card variables
        self.hunt_card_artemia = False
        self.hunt_card_target = False
        self.hunt_card_target2 = False
        self.hunt_card_played = []
        self.anticipation_target = None

        self.creature.draw_hunt_card(3)

        # create the tokens
        self.c_token = Token('Creature')
        self.a_token = Token('Artemia')
        self.t_token = Token('Target')
        self.t_token2 = Token('Target2')

        self.creature_spaces_to_win = Game.GOAL_CREATURE_HUNTED[int(players)][0]
        self.hunted_spaces_to_win = Game.GOAL_CREATURE_HUNTED[int(players)][1]

        # metrics for saving
        self.counter = collections.Counter()
        self.counter['turn'] = 0

    def game_over(self):
        if (not self.creature_spaces_to_win) or (not self.hunted_spaces_to_win):
            return True
        else:
            return False

    def play(self, verbose=False):
        if verbose:
            logger.info('GAME START')
            logger.info('The game is being played on Artemia Board {}'
                        .format(self.artemia))

        while self.counter['turn'] < 20:  # temporary failsafe to prevent infinite loops, an ordinary game has theoretical a maximum of 20 turns in normal cases

            # start of turn clean-up steps
            self.counter['turn'] += 1
            self.beach_proced_in_turn = False
            self.wreck_proced_in_turn = False
            self.hunt_card_artemia = False
            self.hunt_card_target = False
            self.hunt_card_target2 = False
            self.hunt_card_played = []  # need to make sure when a hunt card is played, add the name of the hunt card to this
            self.anticipation_target = None
            self.c_token.place = self.creature
            self.a_token.place = self.creature
            self.t_token.place = self.creature

            # PHASE 1
            if verbose:
                logger.info('\nTurn {}'.format(self.counter['turn']))
                logger.info('The Creature is {} space{} from winning. '
                            'The Hunted are {} space{} from winning.'
                            .format(self.creature_spaces_to_win,
                                    's' if self.creature_spaces_to_win != 1 else '',
                                    self.hunted_spaces_to_win,
                                    's' if self.hunted_spaces_to_win != 1 else ''))
                logger.info('Phase 1')

            # hunted decide if they give up, then resist, then they play a card
            for hunted in self.hunted:
                if hunted.mind.decide_if_give_up():
                    hunted.give_up(verbose=verbose)
                if hunted.mind.decide_if_resist():
                    hunted.resist(hunted.mind.decide_if_resist(), verbose=True)
                hunted.play_card(verbose=verbose)

                # hunted play an extra card if they played river or artefact in the previous turn
                if hunted.river_turn:
                    hunted.play_card(verbose=verbose)
                    if verbose:
                        logger.info('{} played two cards because of The River.'
                                    .format(hunted.name))
                if hunted.artefact_turn:
                    hunted.play_card(verbose=verbose)
                    if verbose:
                        logger.info('{} played two cards because of The Artefact.'.format(hunted.name))

            if self.game_over():
                break

            # PHASE 2
            if verbose:
                logger.info('Phase 2')

            self.creature.place_token(self.c_token, verbose=verbose)

            # Creature places the artemia token if the Hunted are a certain number of spaces from victory, or if the Creature played a Hunt card with an artemia icon
            if (self.hunted_spaces_to_win in Game.ARTEMIA_SPACES[self.artemia]) or self.hunt_card_artemia:
                self.creature.place_token(self.a_token, verbose=verbose)

            # Creature places the target token if they played a Hunt card with an target icon
            if self.hunt_card_target:
                self.creature.place_token(self.t_token, verbose=verbose)

            for hunted in self.hunted:
                if hunted.river_turn:
                    hunted.river_turn = False
                    if len(hunted.played) == 2:
                        hunted.return_card_to_hand(hunted.mind.choose_card_to_return(), verbose=verbose)
                        # TO DO: mind should return a card if it has a creature, artemia or target token on it and the other card does not

            # PHASE 3
            if verbose:
                logger.info('Phase 3')

            caught_at_least_one = False
            for hunted in self.hunted:
                for played in hunted.played:
                    if played.name == self.c_token.place.name:
                        self.counter['creature catch'] += 1
                        if played.name == 'The Lair':
                            hunted.will -= 2
                            if verbose:
                                logger.info('{} was caught by the Creature at'
                                            ' The Lair and lost 2 will'
                                            .format(hunted.name))
                        else:
                            hunted.will -= 1
                            logger.info('{} was caught by the Creature at {} '
                                        'and lost 1 will'
                                        .format(hunted.name, played.name))
                        if caught_at_least_one == False:
                            self.counter['advances from catch'] += 1
                            self.creature_spaces_to_win -= 1
                            caught_at_least_one = True
                    elif played.name == self.a_token.place.name:
                        self.counter['artemia catch'] += 1
                        if hunted.phand == []:
                            if verbose:
                                logger.info('{} visited {} but it had the '
                                            'Artemia token on it and they had no cards in hand.'
                                            .format(hunted.name, played.name))
                        else:
                            hunted.discard_pcard(hunted.mind.choose_card_to_discard())
                            if verbose:
                                logger.info('{} visited {} but it had the '
                                            'Artemia token on it, so they discarded a card'
                                            .format(hunted.name, played.name))
                    elif played.name == self.t_token.place.name:
                        pass
                    else:
                        hunted.proc(played.name, verbose=verbose)
                        # to add option of taking back one place from discard
                    if self.game_over():
                        break
                if self.game_over():
                    break
            if self.game_over():
                break

            # PHASE 4
            if verbose:
                logger.info('Phase 4')
                logger.info('The Hunted are now one step closer to escape')
            self.hunted_spaces_to_win -= 1
            if self.game_over():
                break

            # move played cards into discard pile
            for hunted in self.hunted:
                for played in hunted.played:
                    hunted.discard.append(played)
                    hunted.played.remove(played)

        logger.info('The game is over')
        if self.creature_spaces_to_win < 1:
            winner = 'Creature'
            logger.info('The Creature won')
        elif self.hunted_spaces_to_win < 1:
            winner = 'Hunted'
            logger.info('The Hunted won')
        with open('games.csv', 'a', newline='') as csvfile:
            fieldnames = ['ARTEMIA_BOARD',
                          'PLAYERS',
                          'WINNER',
                          'TURNS',
                          'HUNTED',
                          'CREATURE',
                          'LAIR',
                          'JUNGLE',
                          'RIVER',
                          'BEACH',
                          'ROVER',
                          'SWAMP',
                          'SHELTER',
                          'WRECK',
                          'SOURCE',
                          'ARTEFACT',
                          'CREATURE_CATCH',
                          'ARTEMIA_CATCH',
                          'ADVANCES_FROM_CATCH']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'ARTEMIA_BOARD': self.artemia,
                             'PLAYERS': len(self.hunted) + 1,
                             'WINNER': winner,
                             'TURNS': self.counter['turn'],
                             'HUNTED': self.hunted_spaces_to_win,
                             'CREATURE': self.creature_spaces_to_win,
                             'LAIR': self.counter['The Lair'],
                             'JUNGLE': self.counter['The Jungle'],
                             'RIVER': self.counter['The River'],
                             'BEACH': self.counter['The Beach'],
                             'ROVER': self.counter['The Rover'],
                             'SWAMP': self.counter['The Swamp'],
                             'SHELTER': self.counter['The Shelter'],
                             'WRECK': self.counter['The Wreck'],
                             'SOURCE': self.counter['The Source'],
                             'ARTEFACT': self.counter['The Artefact'],
                             'CREATURE_CATCH': self.counter['creature catch'],
                             'ARTEMIA_CATCH': self.counter['artemia catch'],
                             'ADVANCES_FROM_CATCH': self.counter['advances from catch']
                             })


class Token:
    """The creature token, artemia token or target token."""

    def __init__(self, name):
        self.name = name
        self.place = None

    def __repr__(self):
        return self.name


class Hunted:
    """A Hunted player."""

    def __init__(self, name, game):
        self.name = name
        self.will = 3
        self.shand = []
        self.phand = []
        self.discard = []
        self.played = []
        self.mind = RandomMind(self)
        self.game = game
        self.river_turn = False
        self.artefact_turn = False

    def __repr__(self):
        return '{}({})'.format(self.name, self.mind)

    def resist(self, will_lost, verbose=False):
        self.will -= will_lost
        for i in range(will_lost * 2):
            self.take_back(self.mind.card_to_take_back())  # placeholder to be based on Hunted.mind
        if verbose:
            logger.info('{} resisted, losing {} will and taking back {} cards'
                        .format(self.name, will_lost, will_lost * 2))

    def give_up(self, verbose=False):
        self.will = 3
        for card in self.discard:
            self.phand.append(card)
        self.discard = []
        self.game.creature_spaces_to_win -= 1
        if verbose:
            logger.info('{} gave up, taking back all cards and will and '
                        'pushing the Creature one step to victory'
                        .format(self.name))

    def play_card(self, verbose=False):
        if self.phand == []:
            if verbose:
                logger.info('{} tried to play a card but had no cards in hand'
                            .format(self.name))
        else:
            card = self.mind.choose_card_to_play()
            self.phand.remove(card)
            self.played.append(card)
            if verbose:
                logger.info('{} played {} facedown'.format(self.name,
                                                           card.name))

    def take_back(self, card, verbose=False):
        if card == None:
            if verbose:
                logger.info('{} had no cards to take back'.format(self.name))
                return None
        self.discard.remove(card)
        self.phand.append(card)
        if verbose:
            logger.info('{} takes back {}'.format(self.name, card.name))

    def take_from_reserve(self, card, verbose=False):
        self.phand.append(card)
        self.game.reserve.remove(card)
        if verbose:
            logger.info('{} takes {} from the reserve'.format(self.name,
                                                              card.name))

    def discard_pcard(self, card):
        self.phand.remove(card)
        self.discard.append(card)

    def draw_survival(self):
        card = random.choice(self.game.survival_deck)
        self.game.survival_deck.remove(card)
        self.shand.append(card)

    def return_card_to_hand(self, card, verbose=False):
        self.phand.append(card)
        self.played.remove(card)
        if verbose:
            logger.info('{} returned {} to their hand.'.format(self.name,
                                                               card.name))

    def reveal_pcard(self, card):
        pass  # nothing actually happens here. I can add a verbose here if i want later

    def proc(self, cardname, verbose=False):
        def lair():
            if self.mind.choose_lair_option() == 'Take Back':
                for card in self.discard:
                    self.take_back(card, verbose=verbose)
            else:
                self.proc(self.game.c_token.place.name, verbose=verbose)

        def jungle():
            for card in self.played:
                if card.name == 'The Jungle':
                    self.phand.append(card)
                    self.played.remove(card)
            self.take_back(self.mind.choose_take_back(), verbose=verbose)

        def river():
            self.river_turn = True

        def beach():
            if not self.game.beach_proced_in_turn:
                self.game.beach_proced_in_turn = True
                if not self.game.beach_marker_on:
                    self.game.beach_marker_on = True
                    if verbose:
                        logger.info('{} put the Marker counter on the Beach'
                                    .format(self.name))
                else:
                    self.game.beach_marker_on = False
                    self.game.hunted_spaces_to_win -= 1
                    if verbose:
                        logger.info('{} removed the Marker counter from the '
                                    'Beach, moving the Rescue counter forward 1 space'
                                    .format(self.name))
            if verbose:
                logger.info('{} visited the Beach but it was'
                            ' already activated this turn'.format(self.name))

        def rover():
            card = self.mind.choose_card_from_reserve()
            if not card:
                if verbose:
                    logger.info('{} tried to explore with the Rover but no '
                                'places were left to explore.'
                                .format(self.name))
            else:
                self.take_from_reserve(card, verbose=verbose)
                if verbose:
                    logger.info('{} discovered {} using The Rover.'
                                .format(self.name, card.name))

        def swamp():
            for card in self.played:
                if card.name == 'The Swamp':
                    self.phand.append(card)
                    self.played.remove(card)
            self.take_back(self.mind.choose_take_back(), verbose=verbose)
            self.take_back(self.mind.choose_take_back(), verbose=verbose)

        def shelter():
            try:
                cards = random.sample(self.game.survival_deck, 2)
                for card in cards:
                    self.game.survival_deck.remove(card)
                card_to_draw, card_to_discard = self.mind.choose_survival_card_at_shelter(cards)
                self.shand.append(card_to_draw)
                self.game.survival_discard.append(card_to_discard)
                if verbose:
                    logger.info('{} visited the Shelter, choosing {} over {}'
                                .format(self.name, card_to_draw.name,
                                        card_to_discard.name))
            except:
                pass

        def wreck():
            if not self.game.wreck_proced_in_turn:
                self.game.wreck_proced_in_turn = True
                self.game.hunted_spaces_to_win -= 1
                if verbose:
                    logger.info('{} visited the Wreck, moving the Rescue '
                                'counter forward 1 space'
                                .format(self.name))
            else:
                if verbose:
                    logger.info('{} visited the Wreck but it was already '
                                'activated this turn'.format(self.name))

        def source():
            if self.mind.source_choose_will():
                benefactor = self.mind.player_to_gain_will()
                benefactor.will += 1
                if verbose:
                    logger.info('{} visited the Source and chose {} to gain 1 will'
                                .format(self.name, benefactor.name))
            else:
                self.draw_survival()
                if verbose:
                    logger.info('{} visited the Source and chose to draw a Survival card'
                                .format(self.name))

        def artefact():
            self.artefact_turn = True

        switcher = {
            'The Lair': lair,
            'The Jungle': jungle,
            'The River': river,
            'The Beach': beach,
            'The Rover': rover,
            'The Swamp': swamp,
            'The Shelter': shelter,
            'The Wreck': wreck,
            'The Source': source,
            'The Artefact': artefact,
        }
        # Get the function from switcher dictionary
        self.game.counter[cardname] += 1
        func = switcher.get(cardname)
        func()


class Creature:
    """The Creature player."""

    def __init__(self, name, game):
        self.name = name
        self.hhand = []
        self.hdiscard = []
        self.mind = RandomMind(self)
        self.game = game
        self.tracking_turn = False

    def place_token(self, token, verbose=False):
        chosen_place_name = self.mind.choose_place_name_to_put_token()
        for place_card in self.game.board:
            if place_card.name == chosen_place_name:
                place_card.tokens.append(token)
                token.place = place_card
                if verbose:
                    logger.info('{} puts the {} token on {}'.format(self.name,
                                                                    token.name,
                                                                    place_card.name))
                break

    def draw_hunt_card(self, number_of_cards=1):
        for i in range(number_of_cards):
            card = random.choice(self.game.hunt_deck)
            self.game.hunt_deck.remove(card)
            self.hhand.append(card)

    def play_hunt_card(self, cardname, verbose=False):
        def forbidden_zone():
            for hunted in self.game.hunted:
                try:
                    hunted.discard_pcard(hunted.mind.choose_card_to_discard())
                except:
                    pass

        def phobia():
            self.game.hunt_card_artemia = True
            target = self.mind.choose_player_for_phobia()
            for i in range(len(target.phand) - 2):
                target.reveal_pcard(target.mind.choose_card_to_reveal())
                # to add a way for creature to decide to hunt this player, and exclude the revealed cards

        def ascendancy():
            target = self.mind.choose_player_for_ascendancy()
            for i in range(len(target.phand) - 2):
                target.discard_pcard(target.mind.choose_card_to_discard())

        def scream():
            self.game.hunt_card_target = True

        def force_field():
            # there is only one target token. i should create new invisible spots in between places and create a new method for targeting two adjacent places
            if verbose:
                pass

        def toxin():
            self.game.hunt_card_target = True

        def mutation():
            self.game.hunt_card_artemia = True

        def virus():
            # there is only one artemia token. i should create new invisible spots in between places and create a new method for placing on two adjacent places
            pass

        def persecution():
            pass

        def anticipation():
            self.game.anticipation_target = self.mind.choose_player_for_anticipation()

        def interference():
            pass

        def flashback():
            pass  # to code this

        def detour():
            pass  # to code this, move to adjacent place

        def stasis():
            pass

        def despair():
            self.game.hunt_card_artemia = True

        def tracking():
            self.tracking_turn = True

        def fierceness():
            pass

        def mirage():
            pass  # same as force field

        def cataclysm():
            pass

        def clone():
            self.game.hunt_card_target = True

        switcher = {
            'Forbidden Zone': forbidden_zone,
            'Phobia': phobia,
            'Ascendancy': ascendancy,
            'Scream': scream,
            'Force Field': force_field,
            'Toxin': toxin,
            'Mutation': mutation,
            'Virus': virus,
            'Persecution': persection,
            'Anticipation': anticipation,
            'Interference': interference,
            'Flashback': flashback,
            'Detour': detour,
            'Stasis': stasis,
            'Despair': despair,
            'Tracking': tracking,
            'Fierceness': fierceness,
            'Mirage': mirage,
            'Cataclysm': cataclysm,
            'Clone': clone
        }
        # Get the function from switcher dictionary
        func = switcher.get(cardname)
        func()

        self.game.hunt_card_played.append(cardname)


class PlaceCard:
    """A Place card, either on the board or in a Hunted's phand."""

    def __init__(self, name, text, number):
        self.name = name
        self.text = text
        self.number = number
        self.tokens = []

    def __repr__(self):
        return self.name


class SurvivalCard:
    """A Survival card."""

    def __init__(self, name, text, phase):
        self.name = name
        self.text = text
        self.phase = phase


class HuntCard:
    """A Hunt card."""

    def __init__(self, name, text, phase, artemia):
        self.name = name
        self.text = text
        self.phase = phase
        self.artemia = artemia


class RandomMind:
    """A decision-making process for a player"""

    def __init__(self, player):
        self.player = player

    def choose_card_to_play(self):
        return random.choice(self.player.phand)

    def choose_take_back(self):
        if not self.player.discard:
            return None
        else:
            return random.choice(self.player.discard)

    def choose_place_name_to_put_token(self):
        place_option = []
        for hunted in self.player.game.hunted:
            for card in hunted.played:
                if card.name not in place_option:
                    place_option.append(card.name)
            for card in hunted.phand:
                if card.name not in place_option:
                    place_option.append(card.name)
        return random.choice(place_option)

    def decide_if_give_up(self):
        if self.player.will == 1 and not self.player.phand:
            return True
        else:
            return False

    def decide_if_resist(self):
        if not self.player.phand:
            return 1
        else:
            return False

    def card_to_take_back(self):
        return random.choice(self.player.discard)

    def choose_lair_option(self):
        if len(self.player.discard) > 2:
            return 'Take Back'
        else:
            return 'Proc Creature Place'

    def choose_card_from_reserve(self):
        if not self.player.game.reserve:
            return None
        return random.choice(self.player.game.reserve)

    def choose_survival_card_at_shelter(self, cards):
        if random.randint(0, 1) > 0:
            return cards[0], cards[1]
        else:
            return cards[1], cards[0]

    def choose_card_to_return(self):
        return random.choice(self.player.played)

    def source_choose_will(self):
        return random.choice([True, False])

    def player_to_gain_will(self):
        return random.choice(self.player.game.hunted)

    def choose_card_to_discard(self):
        return random.choice(self.player.phand)

    def choose_card_to_reveal(self):  # for phobia
        return random.choice(self.player.phand)

    def choose_player_for_phobia(self):
        candidates = [hunted for hunted in
                      self.player.game.hunted
                      if len(hunted.phand) > 2]
        return random.choice(candidates)

    def choose_player_for_ascendancy(self):
        candidates = [hunted for hunted in
                      self.player.game.hunted
                      if len(hunted.phand) > 2]
        return random.choice(candidates)


hunt_cards = {}
survival_cards = {}
place_cards = {}
with open('cards.csv', 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['TYPE'] == 'Hunt':
            hunt_cards[row['CARDNAME']] = HuntCard(row['CARDNAME'],
                                                   row['TEXT'],
                                                   row['PHASE'],
                                                   row['ARTEMIA'])
        elif row['TYPE'] == 'Survival':
            survival_cards[row['CARDNAME']] = SurvivalCard(row['CARDNAME'],
                                                           row['TEXT'],
                                                           row['PHASE'])
        else:
            place_cards[row['CARDNAME']] = PlaceCard(row['CARDNAME'],
                                                     row['TEXT'],
                                                     row['NUMBER'])
