from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Entity

class Ability:
    def __init__(self, name: str, description: str, cooldown: int = 0):
        self.name = name
        self.description = description
        self.cooldown = cooldown
        self.current_cooldown = 0

    def activate(self, entity: 'Entity') -> str:
        if self.current_cooldown > 0:
            return f"{self.name} is on cooldown ({self.current_cooldown} turns left)."
        
        msg = self.apply_effect(entity)
        if "Success" in msg or "active" in msg.lower() or "Rage" in msg:
            self.current_cooldown = self.cooldown
        return msg

    def apply_effect(self, entity: 'Entity') -> str:
        raise NotImplementedError()

class RageAbility(Ability):
    def __init__(self):
        super().__init__("Rage", "Gain +4 Str, but -2 AC for 10 turns.", cooldown=20)

    def apply_effect(self, entity: 'Entity') -> str:
        entity.fighter.status_effects["Rage"] = 10
        return "You enter a bloodthirsty Rage!"

class SneakAttackAbility(Ability):
    def __init__(self):
        super().__init__("Sneak Attack", "Deal double damage on your next hit.", cooldown=5)

    def apply_effect(self, entity: 'Entity') -> str:
        entity.fighter.status_effects["SneakAttack"] = 1
        return "You prepare a deadly Sneak Attack!"
