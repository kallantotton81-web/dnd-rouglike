from dnd_rules import Stats
from typing import Tuple, Optional
from monsters import MonsterType

def get_orc_king():
    return MonsterType(
        name="Orc King",
        char="K",
        color=(255, 100, 0), # Bright Orange/Red
        hp=60,
        ac=16,
        stats=Stats(18, 12, 16, 12, 12, 14),
        damage_dice="2d8",
        xp_value=500,
        ai_type="boss_expert"
    )

def get_lich():
    return MonsterType(
        name="The Lich",
        char="L",
        color=(150, 255, 200), # Eerie Cyan/White
        hp=45,
        ac=14,
        stats=Stats(10, 14, 14, 20, 16, 16),
        damage_dice="1d8",
        xp_value=1000,
        ai_type="boss_expert"
    )
