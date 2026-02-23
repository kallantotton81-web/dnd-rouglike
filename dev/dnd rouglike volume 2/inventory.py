from typing import List, TYPE_CHECKING
from items import Item

if TYPE_CHECKING:
    from entity import Entity

class Inventory:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []

    def add_item(self, item: Item) -> bool:
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True

    def remove_item(self, item: Item):
        if item in self.items:
            self.items.remove(item)

    def toggle_equip(self, item_entity: 'Entity') -> str:
        if not item_entity.equippable:
            return f"The {item_entity.name} cannot be equipped."
        
        slot = item_entity.equippable.slot
        fighter = self.owner.fighter
        
        if slot == "weapon":
            if fighter.weapon == item_entity:
                fighter.weapon = None
                return f"You unequip the {item_entity.name}."
            else:
                fighter.weapon = item_entity
                return f"You equip the {item_entity.name}."
        elif slot == "armor":
            if fighter.armor == item_entity:
                fighter.armor = None
                return f"You unequip the {item_entity.name}."
            else:
                fighter.armor = item_entity
                return f"You equip the {item_entity.name}."
        elif slot == "scroll":
            if fighter.scroll == item_entity:
                fighter.scroll = None
                return f"You unequip the {item_entity.name}."
            else:
                fighter.scroll = item_entity
                return f"You equip the {item_entity.name} as your active spell."
        
        return "Unknown equipment slot."
