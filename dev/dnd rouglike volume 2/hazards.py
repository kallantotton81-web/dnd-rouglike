from typing import TYPE_CHECKING, Optional, Callable
if TYPE_CHECKING:
    from entity import Entity
    from engine import Engine

class Hazard:
    def __init__(self, name: str, trigger_func: Callable, **kwargs):
        self.name = name
        self.trigger_func = trigger_func
        self.function_kwargs = kwargs
        self.is_revealed = False

    def trigger(self, engine: 'Engine', entity: 'Entity') -> str:
        return self.trigger_func(engine, entity, **self.function_kwargs)

def spike_trap(engine: 'Engine', entity: 'Entity', damage: int = 5):
    from dnd_rules import roll_dice
    from sound_manager import SoundManager
    SoundManager.play_sound("trap")
    entity.fighter.take_damage(damage, engine)
    return f"{entity.name} triggers a spike trap and takes {damage} damage!"

class Interactive:
    def __init__(self, name: str, interact_func: Callable, **kwargs):
        self.name = name
        self.interact_func = interact_func
        self.function_kwargs = kwargs
        self.is_broken = False

    def interact(self, engine: 'Engine', entity: 'Entity') -> str:
        if self.is_broken:
            return f"The {self.name} is already broken/opened."
        return self.interact_func(engine, entity, self, **self.function_kwargs)

def open_chest(engine: 'Engine', entity: 'Entity', interactive: 'Interactive'):
    interactive.is_broken = True
    # Spawn a random item on top of the chest
    from procgen import place_entities
    from items import Item, heal
    from entity import Entity as EntityObj
    
    # Simple version: always a potion for now
    item_comp = Item("Healing Potion", "!", (0, 255, 0), use_function=heal, amount=10)
    potion = EntityObj(entity.x, entity.y, "!", (0, 255, 0), "Healing Potion", item=item_comp)
    engine.entities.append(potion)
    
    from sound_manager import SoundManager
    SoundManager.play_sound("interact")
    
    return f"You open the chest and find a Healing Potion!"

def smash_barrel(engine: 'Engine', entity: 'Entity', interactive: 'Interactive'):
    from sound_manager import SoundManager
    SoundManager.play_sound("interact")
    interactive.is_broken = True
    entity.char = "%" # Change to debris
    return f"You smash the barrel into pieces!"
