from enum import Enum, auto

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32

COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red":   (255, 0, 0),
    "green": (0, 200, 0),
    "gold":  (255, 215, 0),
    "gray":  (120, 120, 120),
}

class GameState(Enum):
    MAIN_MENU      = auto()
    CLASS_SELECT   = auto()
    PLAYING        = auto()
    GAME_OVER      = auto()
    INVENTORY_MENU = auto()
    EQUIP_MENU     = auto()
    SHOP_MENU      = auto()
    VICTORY        = auto()
