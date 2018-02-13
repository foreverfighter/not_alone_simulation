from classes import *

no_of_players = input('How many players? (2-7) ')
no_of_games = input('How many games to simulate? (1-100) ')

for i in range(int(no_of_games)):
    game = Game(no_of_players)
    game.play(verbose=True)
