from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from dnd_rules import Stats

if TYPE_CHECKING:
    from engine import Engine
    from ai_behaviors import BaseAI

class Component:
    def __init__(self, owner: 'Entity'):
        self.owner = owner

from dnd_rules import Stats, roll_dice
from chr_classes import BaseClass

class Fighter(Component):
    def __init__(self, owner: 'Entity', hp: int, ac: int, stats: Stats, 
                 chr_class: Optional['BaseClass'] = None, lives: int = 1):
        super().__init__(owner)
        self.max_hp = hp
        self.hp = hp
        self.base_ac = ac
        self.stats = stats
        self.chr_class = chr_class
        self.lives = lives
        self.base_damage_dice = chr_class.damage_dice if chr_class else "1d6"
        self.level = 1
        self.xp = 0
        self.gold = 0
        
        self.weapon: Optional['Entity'] = None
        self.armor: Optional['Entity'] = None
        self.scroll: Optional['Entity'] = None
        self.status_effects = {} # Name: Duration

    @property
    def ac(self) -> int:
        bonus = 0
        if self.armor and self.armor.equippable:
            bonus += self.armor.equippable.ac_bonus
        if "Rage" in self.status_effects:
            bonus -= 2
        return self.base_ac + bonus

    @property
    def damage_dice(self) -> str:
        if self.weapon and self.weapon.equippable:
            return self.weapon.equippable.damage_dice
        return self.base_damage_dice

    def tick_effects(self):
        to_remove = []
        for effect in self.status_effects:
            self.status_effects[effect] -= 1
            if self.status_effects[effect] <= 0:
                to_remove.append(effect)
        for effect in to_remove:
            del self.status_effects[effect]

    def take_damage(self, amount: int, engine: 'Engine' = None):
        self.hp -= amount
        if engine:
            # Add floating damage number
            self.owner.x, self.owner.y
            engine.add_vfx(f"{amount}", self.owner.x, self.owner.y, (255, 0, 0))
            
            # Trigger screen shake if player is damaged
            if self.owner.name == "Player":
                engine.screen_shake = 8

    def attack(self, target: 'Entity', engine: 'Engine' = None) -> str:
        from sound_manager import SoundManager
        # d20 + Str Mod vs AC
        str_bonus = 2 if "Rage" in self.status_effects else 0
        blind_penalty = -5 if "Blind" in self.status_effects else 0
        roll = roll_dice(1, 20)
        total_hit = roll + self.stats.str_mod + str_bonus + blind_penalty
        
        if roll == 20 or total_hit >= target.fighter.ac:
            # Hit!
            SoundManager.play_sound("hit")
            num, sides = map(int, self.damage_dice.split('d'))
            damage = roll_dice(num, sides) + self.stats.str_mod + str_bonus
            
            if "SneakAttack" in self.status_effects:
                damage *= 2
                del self.status_effects["SneakAttack"]
                msg_prefix = "[SNEAK ATTACK] "
            else:
                msg_prefix = ""
                
            if roll == 20: damage *= 2 # Critical hit
            
            target.fighter.take_damage(damage, engine)
            return f"{msg_prefix}{self.owner.name} hits {target.name} for {damage} damage!"
        else:
            SoundManager.play_sound("miss")
            if "SneakAttack" in self.status_effects:
                del self.status_effects["SneakAttack"]
            return f"{self.owner.name} misses {target.name}."

class Equippable(Component):
    def __init__(self, owner: 'Entity', slot: str, 
                 damage_dice: str = "1d4", ac_bonus: int = 0):
        super().__init__(owner)
        self.slot = slot # "weapon" or "armor"
        self.damage_dice = damage_dice
        self.ac_bonus = ac_bonus

class Entity:
    def __init__(self, x: int, y: int, char: str, color: tuple, name: str, 
                 blocks_movement: bool = False,
                 fighter: Optional['Fighter'] = None,
                 inventory: Optional['Inventory'] = None,
                 item: Optional['Item'] = None,
                 equippable: Optional['Equippable'] = None,
                 hazard: Optional['Hazard'] = None,
                 interactive: Optional['Interactive'] = None,
                 ai: Optional['BaseAI'] = None,
                 stairs: bool = False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.inventory = inventory
        if self.inventory:
            self.inventory.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.equippable = equippable
        if self.equippable:
            self.equippable.owner = self

        self.hazard = hazard
        if self.hazard:
            self.hazard.owner = self

        self.interactive = interactive
        if self.interactive:
            self.interactive.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.stairs = stairs

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy
