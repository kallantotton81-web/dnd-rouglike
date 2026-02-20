import pygame
import sys
from constants import *

from engine import Engine

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("D&D Roguelike")
        self.clock = pygame.time.Clock()
        self.engine = Engine(self.screen)
        self.running = True

    def run(self):
        while self.running:
            self.running = self.engine.handle_input()
            self._update()
            self.engine.render()
            self.clock.tick(30)

    def _update(self):
        if self.engine.turn == "monsters":
            self.engine.handle_monster_turns()

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
