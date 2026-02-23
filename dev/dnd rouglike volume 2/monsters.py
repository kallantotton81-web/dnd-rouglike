from dnd_rules import Stats
from typing import Tuple, Optional

class MonsterType:
    def __init__(self, name: str, char: str, color: Tuple[int, int, int], 
                 hp: int, ac: int, stats: Stats, damage_dice: str, xp_value: int,
                 ai_type: str = "melee"):
        self.name = name
        self.char = char
        self.color = color
        self.hp = hp
        self.ac = ac
        self.stats = stats
        self.damage_dice = damage_dice
        self.xp_value = xp_value
        self.ai_type = ai_type

def get_kobold():
    return MonsterType(
        name="Kobold",
        char="k",
        color=(180, 110, 50),
        hp=5,
        ac=12,
        stats=Stats(7, 15, 9, 8, 7, 8),
        damage_dice="1d4",
        xp_value=25,
        ai_type="melee"
    )

def get_goblin():
    return MonsterType(
        name="Goblin",
        char="g",
        color=(120, 255, 0),
        hp=7,
        ac=15,
        stats=Stats(8, 14, 10, 10, 8, 8),
        damage_dice="1d6",
        xp_value=50,
        ai_type="melee"
    )

def get_skeleton():
    return MonsterType(
        name="Skeleton",
        char="s",
        color=(240, 240, 240),
        hp=13,
        ac=13,
        stats=Stats(10, 14, 15, 6, 8, 5),
        damage_dice="1d6",
        xp_value=75,
        ai_type="melee"
    )

def get_goblin_archer():
    return MonsterType(
        name="Goblin Archer",
        char="G",
        color=(50, 200, 50),
        hp=7,
        ac=13,
        stats=Stats(8, 16, 10, 10, 8, 8),
        damage_dice="1d6",
        xp_value=75,
        ai_type="ranged"
    )

def get_evil_acolyte():
    return MonsterType(
        name="Evil Acolyte",
        char="a",
        color=(180, 0, 255),
        hp=9,
        ac=10,
        stats=Stats(10, 10, 12, 14, 14, 12),
        damage_dice="1d4",
        xp_value=100,
        ai_type="caster"
    )

def get_orc():
    return MonsterType(
        name="Orc",
        char="O",
        color=(255, 50, 50),
        hp=15,
        ac=13,
        stats=Stats(16, 12, 16, 7, 11, 10),
        damage_dice="1d12",
        xp_value=100,
        ai_type="melee"
    )
