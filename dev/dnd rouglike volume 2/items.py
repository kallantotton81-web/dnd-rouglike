from typing import Tuple, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Entity
    from engine import Engine

class Item:
    def __init__(self, name: str, char: str, color: Tuple[int, int, int], 
                 use_function: Optional[Callable] = None, 
                 charges: Optional[int] = None, **kwargs):
        self.name = name
        self.char = char
        self.color = color
        self.use_function = use_function
        self.charges = charges
        self.is_identified = kwargs.pop("is_identified", True)
        self.function_kwargs = kwargs

    def use(self, engine: 'Engine', user: 'Entity'):
        if self.use_function:
            if not self.is_identified:
                self.is_identified = True
                msg_suffix = f" (Identified as {self.name})"
            else:
                msg_suffix = ""
                
            msg = self.use_function(self, engine, user, **self.function_kwargs)
            # Only remove if it's a one-time use item (not a wand with charges)
            # Check for generic 'use' or 'cast' or 'heal' in message to confirm success
            success_keywords = ["You use", "You cast", "You read", "restored", "heal"]
            if self.charges is None and any(k in msg for k in success_keywords) and "wand" not in self.name.lower():
                user.inventory.remove_item(self)
            return msg + msg_suffix
        elif self.owner and self.owner.equippable:
            # Auto-equip if no use function but is equippable
            return user.inventory.toggle_equip(self.owner)
        return f"The {self.name} cannot be used."

def cast_spell(item: 'Item', engine: 'Engine', user: 'Entity', spell_data: dict):
    from spells import Spell
    spell = Spell(spell_data["name"], spell_data["damage_dice"], 
                  range=spell_data["range"], area=spell_data.get("area", 0))
    
    # Find target (nearest monster for now, similar to Wizard casting)
    monsters = [e for e in engine.entities if e != user and e.fighter]
    if not monsters:
        return "No targets in range."
    
    nearest = min(monsters, key=lambda m: abs(m.x - user.x) + abs(m.y - user.y))
    dist = abs(nearest.x - user.x) + abs(nearest.y - user.y)
    
    if dist > spell.range:
        return f"Target is too far for {spell.name}."

    from sound_manager import SoundManager
    SoundManager.play_sound("spell")
    msg = f"You cast {spell.name} from the {item.name}. " + spell.cast(engine, user, nearest)
    
    # Handle charges for Wands
    if item.charges is not None:
        item.charges -= 1
        msg += f" ({item.charges} charges left)"
        if item.charges <= 0:
            user.inventory.remove_item(item)
            msg += f" The {item.name} crumbles to dust!"
    
    # Handle monster death (copied from engine.py logic for now)
    if nearest.fighter.hp <= 0:
        xp_gain = getattr(nearest.fighter, 'xp_value', 50)
        user.fighter.xp += xp_gain
        msg += f" {nearest.name} dies! You gain {xp_gain} XP."
        engine.entities.remove(nearest)
        
        from leveling import check_level_up
        if check_level_up(user):
            engine.add_message(f"You leveled up to Level {user.fighter.level}!")

    return msg

def heal(item: 'Item', engine: 'Engine', user: 'Entity', amount: int, **kwargs):
    if user.fighter.hp >= user.fighter.max_hp:
        return "You are already at full health."
    
    heal_amount = min(amount, user.fighter.max_hp - user.fighter.hp)
    user.fighter.hp += heal_amount
    if engine:
        engine.add_vfx(f"+{heal_amount}", user.x, user.y, (0, 255, 0))
    from sound_manager import SoundManager
    SoundManager.play_sound("pickup")
    return f"You use the potion and heal for {heal_amount} HP!"

def use_scroll(item: 'Item', engine: 'Engine', user: 'Entity', spell=None, **kwargs):
    """Generic scroll use: find nearest monster and cast stored spell."""
    if spell is None:
        return "This scroll crumbles without effect."
    
    monsters = [e for e in engine.entities if e != user and e.fighter]
    if not monsters:
        return "There are no targets in range."
    
    nearest = min(monsters, key=lambda m: abs(m.x - user.x) + abs(m.y - user.y))
    dist = abs(nearest.x - user.x) + abs(nearest.y - user.y)
    
    if dist > spell.range:
        return f"Target is too far for {spell.name}."
    
    from sound_manager import SoundManager
    SoundManager.play_sound("spell")
    msg = f"You read the {item.name}. " + spell.cast(engine, user, nearest)
    
    # Handle monster death
    if nearest.fighter.hp <= 0:
        xp_gain = getattr(nearest.fighter, 'xp_value', 50)
        user.fighter.xp += xp_gain
        msg += f" {nearest.name} dies! You gain {xp_gain} XP."
        if nearest in engine.entities:
            engine.entities.remove(nearest)
        from leveling import check_level_up
        if check_level_up(user):
            engine.add_message(f"You leveled up to Level {user.fighter.level}!")
    
    return msg
