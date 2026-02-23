import random

def roll_dice(number_of_dice: int, sides: int) -> int:
    return sum(random.randint(1, sides) for _ in range(number_of_dice))

def get_modifier(stat: int) -> int:
    return (stat - 10) // 2

class Stats:
    def __init__(self, strength: int, dexterity: int, constitution: int, 
                 intelligence: int, wisdom: int, charisma: int):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma

    @property
    def str_mod(self): return get_modifier(self.strength)
    @property
    def dex_mod(self): return get_modifier(self.dexterity)
    @property
    def con_mod(self): return get_modifier(self.constitution)
    @property
    def int_mod(self): return get_modifier(self.intelligence)
    @property
    def wis_mod(self): return get_modifier(self.wisdom)
    @property
    def cha_mod(self): return get_modifier(self.charisma)
