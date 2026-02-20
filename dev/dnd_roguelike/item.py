from constants import *

class Item:
    def __init__(self, x, y, name, char, color):
        self.x = x
        self.y = y
        self.name = name
        self.char = char
        self.color = color

class Equippable(Item):
    def __init__(self, x, y, name, char, color, slot, bonus, dex_cap=None):
        super().__init__(x, y, name, char, color)
        self.slot = slot
        self.bonus = bonus
        self.dex_cap = dex_cap

class Weapon(Equippable):
    def __init__(self, x, y, name, color, damage_dice, damage_sides, bonus=0):
        super().__init__(x, y, name, CHAR_WEAPON, color, "weapon", bonus)
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides

class Armor(Equippable):
    def __init__(self, x, y, name, char, color, bonus, dex_cap=None):
        super().__init__(x, y, name, char, color, "armor", bonus, dex_cap)

class Consumable(Item):
    def __init__(self, x, y, name, char, color):
        super().__init__(x, y, name, char, color)

class HealingPotion(Consumable):
    def __init__(self, amount):
        super().__init__(0, 0, "Healing Potion", CHAR_POTION, COLOR_GREEN)
        self.amount = amount

    def spawn(self, x, y):
        self.x = x
        self.y = y
        return self
