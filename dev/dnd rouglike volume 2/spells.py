from typing import List, TYPE_CHECKING
from dnd_rules import roll_dice

if TYPE_CHECKING:
    from entity import Entity
    from engine import Engine

class Spell:
    def __init__(self, name: str, damage_dice: str, range: int, area: int = 0):
        self.name = name
        self.damage_dice = damage_dice
        self.range = range
        self.area = area

    def cast(self, engine: 'Engine', caster: 'Entity', target: 'Entity') -> str:
        # Parse dice strings like "3d6" or "1d4+1"
        dice_part = self.damage_dice.split('+')[0].split('-')[0]
        bonus = 0
        if '+' in self.damage_dice:
            bonus = int(self.damage_dice.split('+')[1])
        elif '-' in self.damage_dice:
            bonus = -int(self.damage_dice.split('-')[1])
        num, sides = map(int, dice_part.split('d'))
        damage = roll_dice(num, sides) + bonus
        
        if self.area > 0:
            # Area effect
            hit_entities = []
            for entity in engine.entities[:]: # Copy list for safe removal
                if entity != caster and entity.fighter:
                    dist = abs(entity.x - target.x) + abs(entity.y - target.y)
                    if dist <= self.area:
                        entity.fighter.take_damage(damage, engine)
                        hit_entities.append(entity.name)
                        if entity.fighter.hp <= 0:
                            xp_gain = getattr(entity.fighter, 'xp_value', 50)
                            caster.fighter.xp += xp_gain
                            engine.entities.remove(entity)
            
            from leveling import check_level_up
            if check_level_up(caster):
                engine.add_message(f"You leveled up to Level {caster.fighter.level}!")
                
            return f"The {self.name} explodes! Hit: {', '.join(hit_entities)} for {damage} damage!"
        else:
            # Single target
            target.fighter.take_damage(damage, engine)
            msg = f"{caster.name} casts {self.name} on {target.name} for {damage} damage!"
            
            if target.fighter.hp <= 0:
                xp_gain = getattr(target.fighter, 'xp_value', 50)
                caster.fighter.xp += xp_gain
                msg += f" {target.name} dies! You gain {xp_gain} XP."
                engine.entities.remove(target)
                
                from leveling import check_level_up
                if check_level_up(caster):
                    engine.add_message(f"You leveled up to Level {caster.fighter.level}!")
            
            return msg

class StatusSpell(Spell):
    def __init__(self, name: str, status_name: str, duration: int, range: int):
        super().__init__(name, "0d0", range)
        self.status_name = status_name
        self.duration = duration

    def cast(self, engine: 'Engine', caster: 'Entity', target: 'Entity') -> str:
        target.fighter.status_effects[self.status_name] = self.duration
        return f"{caster.name} casts {self.name} on {target.name}! {target.name} is now {self.status_name} for {self.duration} turns."

def BlindSpell():
    return StatusSpell("Blind", "Blind", 5, 6)

def HasteSpell():
    return StatusSpell("Haste", "Haste", 3, 5) # Note: Haste logic needs to be added to turns

def SlowSpell():
    return StatusSpell("Slow", "Slow", 5, 6)

def FireballSpell():
    return Spell("Fireball", "3d6", range=5, area=2)

def MagicMissileSpell():
    return Spell("Magic Missile", "1d4+1", range=5)
