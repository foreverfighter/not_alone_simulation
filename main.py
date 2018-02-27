#!/usr/bin/env

from classes import *

if __name__ == "main":
    no_of_players = 0
    no_of_games = 0
    while int(no_of_players) < 2 or int(no_of_players) > 7:
        no_of_players = input('How many players? (2-7): ')
    while int(no_of_games) < 1 or int(no_of_games) > 2000:
        no_of_games = input('How many games to simulate? (1-2000): ')

    for i in range(int(no_of_games)):
        game = Game(no_of_players)
        game.play(verbose=True)
