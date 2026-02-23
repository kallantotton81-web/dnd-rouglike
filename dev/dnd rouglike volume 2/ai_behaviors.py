from __future__ import annotations
import random
from typing import TYPE_CHECKING
from dnd_rules import roll_dice

if TYPE_CHECKING:
    from entity import Entity
    from engine import Engine

class BaseAI:
    def perform(self, engine: Engine, entity: Entity):
        raise NotImplementedError()

class HostileMelee(BaseAI):
    def perform(self, engine: Engine, entity: Entity):
        target = engine.player
        dx = target.x - entity.x
        dy = target.y - entity.y
        distance = max(abs(dx), abs(dy))

        if distance <= 1:
            # Attack!
            msg = entity.fighter.attack(target, engine)
            engine.add_message(msg)
        else:
            # Move towards player
            move_dx = (dx // abs(dx)) if dx != 0 else 0
            move_dy = (dy // abs(dy)) if dy != 0 else 0
            
            new_x, new_y = entity.x + move_dx, entity.y + move_dy
            if engine.game_map.is_walkable(new_x, new_y):
                if not any(e.blocks_movement and e.x == new_x and e.y == new_y for e in engine.entities):
                    entity.move(move_dx, move_dy)

class HostileRanged(BaseAI):
    def __init__(self, range: int = 5):
        self.range = range

    def perform(self, engine: Engine, entity: Entity):
        target = engine.player
        dx = target.x - entity.x
        dy = target.y - entity.y
        distance = max(abs(dx), abs(dy))

        if 1 < distance <= self.range:
            # Ranged attack! (Simple abstraction: damage player if in range)
            roll = roll_dice(1, 20)
            total_hit = roll + entity.fighter.stats.dex_mod
            if roll == 20 or total_hit >= target.fighter.ac:
                num, sides = map(int, entity.fighter.damage_dice.split('d'))
                damage = roll_dice(num, sides) + entity.fighter.stats.dex_mod
                if roll == 20: damage *= 2
                target.fighter.take_damage(damage, engine)
                engine.add_message(f"{entity.name} shoots you for {damage} damage!")
            else:
                engine.add_message(f"{entity.name} shoots and misses.")
        elif distance <= 1:
            # Too close! Try to back away or melee if blocked
            move_dx = -(dx // abs(dx)) if dx != 0 else 0
            move_dy = -(dy // abs(dy)) if dy != 0 else 0
            
            new_x, new_y = entity.x + move_dx, entity.y + move_dy
            if engine.game_map.is_walkable(new_x, new_y) and not any(e.blocks_movement and e.x == new_x and e.y == new_y for e in engine.entities):
                entity.move(move_dx, move_dy)
            else:
                # Forced to melee
                msg = entity.fighter.attack(target, engine)
                engine.add_message(msg)
        else:
            # Move towards player until in range
            move_dx = (dx // abs(dx)) if dx != 0 else 0
            move_dy = (dy // abs(dy)) if dy != 0 else 0
            
            new_x, new_y = entity.x + move_dx, entity.y + move_dy
            if engine.game_map.is_walkable(new_x, new_y):
                if not any(e.blocks_movement and e.x == new_x and e.y == new_y for e in engine.entities):
                    entity.move(move_dx, move_dy)

class HostileCaster(BaseAI):
    def __init__(self, spell_range: int = 6):
        self.spell_range = spell_range

    def perform(self, engine: Engine, entity: Entity):
        target = engine.player
        dx = target.x - entity.x
        dy = target.y - entity.y
        distance = max(abs(dx), abs(dy))

        if distance <= self.spell_range:
            # "Magic Missile" style caster logic
            engine.add_message(f"{entity.name} chants and a bolt of energy hits you!")
            damage = roll_dice(1, 4) + 1 # Basic magic missile
            target.fighter.take_damage(damage, engine)
            engine.add_message(f"You take {damage} force damage!")
        else:
            # Move towards player
            move_dx = (dx // abs(dx)) if dx != 0 else 0
            move_dy = (dy // abs(dy)) if dy != 0 else 0
            
            new_x, new_y = entity.x + move_dx, entity.y + move_dy
            if engine.game_map.is_walkable(new_x, new_y):
                if not any(e.blocks_movement and e.x == new_x and e.y == new_y for e in engine.entities):
                    entity.move(move_dx, move_dy)

class BossExpertAI(BaseAI):
    def __init__(self, spell_range: int = 6):
        self.spell_range = spell_range

    def perform(self, engine: Engine, entity: Entity):
        target = engine.player
        dx = target.x - entity.x
        dy = target.y - entity.y
        distance = max(abs(dx), abs(dy))

        if distance <= 1:
            # Melee attack
            msg = entity.fighter.attack(target, engine)
            engine.add_message(msg)
        elif 1 < distance <= self.spell_range:
            # Chance to cast a spell or move
            if random.random() < 0.7:
                engine.add_message(f"{entity.name} unleashes a devastating boss ability!")
                damage = roll_dice(2, 6) + 2
                target.fighter.take_damage(damage, engine)
                engine.add_message(f"You take {damage} damage from the boss's power!")
            else:
                self.move_towards(target, entity, engine)
        else:
            # Move towards player
            self.move_towards(target, entity, engine)

    def move_towards(self, target: Entity, entity: Entity, engine: Engine):
        dx = target.x - entity.x
        dy = target.y - entity.y
        
        move_dx = (dx // abs(dx)) if dx != 0 else 0
        move_dy = (dy // abs(dy)) if dy != 0 else 0
        
        new_x, new_y = entity.x + move_dx, entity.y + move_dy
        if engine.game_map.is_walkable(new_x, new_y):
            if not any(e.blocks_movement and e.x == new_x and e.y == new_y for e in engine.entities):
                entity.move(move_dx, move_dy)
