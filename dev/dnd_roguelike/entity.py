import random
from constants import *

class Entity:
    def __init__(self, x, y, name, char, color):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color
        
        # D&D Stats
        self.strength = 10
        self.dexterity = 10
        self.constitution = 10
        self.intelligence = 10
        self.wisdom = 10
        self.charisma = 10
        
        self.hp = 10
        self.max_hp = 10
        self.ac = BASE_AC
        self.equipment = {"armor": None, "weapon": None}

    def get_modifier(self, stat):
        return (stat - 10) // 2

    @property
    def armor_class(self):
        dex_mod = self.get_modifier(self.dexterity)
        armor = self.equipment.get("armor")
        
        if armor:
            effective_dex_mod = dex_mod
            if armor.dex_cap is not None:
                effective_dex_mod = min(dex_mod, armor.dex_cap)
            return BASE_AC + armor.bonus + effective_dex_mod
        
        return self.ac + dex_mod

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "Zelda", "Z", COLOR_GOLD)
        self.strength = 12
        self.dexterity = 16
        self.constitution = 14
        self.intelligence = 16
        self.wisdom = 18
        self.charisma = 16
        self.max_hp = 100 + self.get_modifier(self.constitution)
        self.hp = self.max_hp

class Monster(Entity):
    def __init__(self, x, y, name, char, color, hp=5, ac=12):
        super().__init__(x, y, name, char, color)
        self.max_hp = hp
        self.hp = hp
        self.ac = ac
