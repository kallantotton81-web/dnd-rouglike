from typing import TYPE_CHECKING
from dnd_rules import roll_dice

if TYPE_CHECKING:
    from entity import Entity

LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

def get_xp_for_level(level: int) -> int:
    if level <= 1: return 0
    return LEVEL_UP_BASE + (level - 2) * LEVEL_UP_FACTOR

def check_level_up(entity: 'Entity') -> bool:
    next_level_xp = get_xp_for_level(entity.fighter.level + 1)
    if entity.fighter.xp >= next_level_xp:
        from sound_manager import SoundManager
        SoundManager.play_sound("level_up")
        entity.fighter.level += 1
        
        # Rewards
        if entity.fighter.chr_class:
            num, sides = map(int, entity.fighter.chr_class.hit_dice.split('d'))
        else:
            num, sides = 1, 6  # Default hit dice for entities without a class
        hp_increase = roll_dice(1, sides) + entity.fighter.stats.con_mod
        entity.fighter.max_hp += hp_increase
        entity.fighter.hp += hp_increase
        
        return True
    return False
