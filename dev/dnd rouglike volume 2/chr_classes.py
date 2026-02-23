from dnd_rules import Stats
from spells import Spell
from abilities import RageAbility, SneakAttackAbility

class BaseClass:
    def __init__(self, name: str, hit_dice: str, damage_dice: str, 
                 base_stats: Stats, starting_spells: list = None,
                 starting_abilities: list = None):
        self.name = name
        self.hit_dice = hit_dice
        self.damage_dice = damage_dice
        self.base_stats = base_stats
        self.starting_spells = starting_spells or []
        self.starting_abilities = starting_abilities or []

class FighterClass(BaseClass):
    def __init__(self):
        super().__init__(
            name="Fighter",
            hit_dice="1d10",
            damage_dice="1d10",
            base_stats=Stats(16, 14, 16, 10, 12, 10),
            starting_abilities=[RageAbility()]
        )

class WizardClass(BaseClass):
    def __init__(self):
        super().__init__(
            name="Wizard",
            hit_dice="1d6",
            damage_dice="1d4",
            base_stats=Stats(8, 14, 12, 18, 14, 12),
            starting_spells=[
                Spell("Magic Missile", "1d4+1", range=5),
                Spell("Fireball", "3d6", range=5, area=2)
            ]
        )

class RogueClass(BaseClass):
    def __init__(self):
        super().__init__(
            name="Rogue",
            hit_dice="1d8",
            damage_dice="1d6",
            base_stats=Stats(12, 18, 14, 12, 10, 14),
            starting_abilities=[SneakAttackAbility()]
        )
