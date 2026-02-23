from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class Merchant:
    def __init__(self):
        self.inventory = [] # List of (Item, price) tuples
        self.is_broken = False # For compatibility with interactive check if needed

    def interact(self, engine: 'Engine', player: 'Entity') -> str:
        from constants import GameState
        engine.state = GameState.SHOP_MENU
        engine.menu_index = 0
        engine.active_shop = self
        return "I have many wares, traveler! What would you like?"

    def get_stock(self):
        return self.inventory

def setup_merchant_stock(engine: 'Engine'):
    from items import Item, heal, use_scroll
    from entity import Entity, Equippable
    import random
    stock = []
    
    # Randomly select items for stock
    # 1. Always some potions
    potion_item = Item(name="Healing Potion", char="!", color=(0, 255, 0), use_function=heal, amount=15)
    Entity(0, 0, potion_item.char, potion_item.color, potion_item.name, item=potion_item)
    stock.append((potion_item, 50))
    
    # 2. Some scrolls or wands
    from spells import FireballSpell, MagicMissileSpell, BlindSpell, HasteSpell, SlowSpell
    r = random.random()
    if r < 0.3:
        spell = FireballSpell()
        name, char, color = f"Scroll of {spell.name}", "?", (255, 100, 0)
    elif r < 0.6:
        spell = MagicMissileSpell()
        name, char, color = f"Scroll of {spell.name}", "?", (100, 100, 255)
    else:
        spell = random.choice([BlindSpell(), HasteSpell(), SlowSpell()])
        name, char, color = f"Scroll of {spell.name}", "?", (200, 150, 50)
    
    scroll_item = Item(name=name, char=char, color=color, use_function=use_scroll, spell=spell)
    scroll_equippable = Equippable(None, slot="scroll")
    Entity(0, 0, scroll_item.char, scroll_item.color, scroll_item.name, item=scroll_item, equippable=scroll_equippable)
    stock.append((scroll_item, 100 if "Fireball" in name else 75 if "Missile" in name else 60))
        
    # 3. Rare Weapons Chance (God Sword)
    if random.random() < 0.15:
        god_item = Item(name="Sword of Antigravity", char="/", color=(255, 0, 255))
        god_equippable = Equippable(None, slot="weapon", damage_dice="100d1")
        # Create dummy entity for ownership/equipping logic
        Entity(0, 0, god_item.char, god_item.color, god_item.name, item=god_item, equippable=god_equippable)
        stock.append((god_item, 500))

    return stock
