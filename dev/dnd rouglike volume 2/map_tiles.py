import pygame
from typing import List, Tuple

class Tile:
    def __init__(self, char: str, color: tuple, walkable: bool = False, transparent: bool = False):
        self.char = char
        self.color = color
        self.walkable = walkable
        self.transparent = transparent

class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Initialize with walls
        self.tiles = [[Tile("█", (60, 60, 60), walkable=False, transparent=False) for _ in range(height)] for _ in range(width)]

    def is_walkable(self, x: int, y: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y].walkable
        return False
