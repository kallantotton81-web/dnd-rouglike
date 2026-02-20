import pygame
import random
from constants import *
from map_gen import Map
from entity import Player, Monster
from item import Item, Armor, HealingPotion, Weapon
from fov import compute_fov

class Engine:
    def __init__(self, screen):
        self.screen = screen
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        player_x, player_y = self.map.make_map(30, 6, 10, MAP_WIDTH, MAP_HEIGHT)
        self.player = Player(player_x, player_y)
        self.entities = [self.player]
        self.items = []
        self.spawn_monsters(30)
        self.spawn_items(10, 5, 1)
        self.message_log = []
        self.add_message("Welcome to the D&D Roguelike!", COLOR_YELLOW)
        self.recompute_fov()
        self.turn = "player"

    def spawn_monsters(self, num_monsters):
        for _ in range(num_monsters):
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if not self.map.is_blocked(x, y) and not any(e.x == x and e.y == y for e in self.entities):
                choice = random.random()
                if choice < 0.7:
                    monster = Monster(x, y, "Orc", "o", COLOR_RED, hp=10, ac=12)
                elif choice < 0.9:
                    monster = Monster(x, y, "Goblin", "g", COLOR_GREEN, hp=6, ac=13)
                else:
                    monster = Monster(x, y, "Troll", "T", COLOR_BLUE, hp=20, ac=15)
                self.entities.append(monster)

    def spawn_items(self, num_armor, num_potions, num_weapons):
        for _ in range(num_armor):
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if not self.map.is_blocked(x, y) and not any(i.x == x and i.y == y for i in self.items):
                choice = random.random()
                if choice < 0.5:
                    item = Armor(x, y, "Leather Armor", CHAR_ARMOR, COLOR_GOLD, bonus=1, dex_cap=None)
                elif choice < 0.8:
                    item = Armor(x, y, "Chain Mail", CHAR_ARMOR, COLOR_GOLD, bonus=6, dex_cap=0)
                else:
                    item = Armor(x, y, "Plate Armor", CHAR_ARMOR, COLOR_GOLD, bonus=8, dex_cap=0)
                self.items.append(item)
            
        # Spawn potions
        for _ in range(num_potions):
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if not self.map.is_blocked(x, y) and not any(i.x == x and i.y == y for i in self.items):
                potion = HealingPotion(10).spawn(x, y)
                self.items.append(potion)
        
        # Spawn weapons
        for _ in range(num_weapons):
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if not self.map.is_blocked(x, y) and not any(i.x == x and i.y == y for i in self.items):
                weapon = Weapon(x, y, "Sword of Infinite Damage", COLOR_CYAN, damage_dice=100000, damage_sides=10)
                self.items.append(weapon)

    def add_message(self, text, color=COLOR_WHITE):
        self.message_log.append((text, color))
        if len(self.message_log) > 5:
            self.message_log.pop(0)

    def recompute_fov(self):
        compute_fov(self.map, self.player.x, self.player.y, FOV_RADIUS)

    def handle_input(self):
        if self.turn != "player":
            return True
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key in [pygame.K_UP, pygame.K_w]: dy = -1
                elif event.key in [pygame.K_DOWN, pygame.K_s]: dy = 1
                elif event.key in [pygame.K_LEFT, pygame.K_a]: dx = -1
                elif event.key in [pygame.K_RIGHT, pygame.K_d]: dx = 1
                elif event.key == pygame.K_g: self.pick_up_item()
                elif event.key == pygame.K_ESCAPE: return False

                if dx != 0 or dy != 0:
                    self.player_move_or_attack(dx, dy)
        return True

    def pick_up_item(self):
        item = next((i for i in self.items if i.x == self.player.x and i.y == self.player.y), None)
        if item:
            if isinstance(item, Armor):
                self.player.equipment["armor"] = item
                self.add_message(f"You pick up and equip the {item.name}!", COLOR_YELLOW)
                self.items.remove(item)
                self.turn = "monsters"
            elif isinstance(item, Weapon):
                self.player.equipment["weapon"] = item
                self.add_message(f"You pick up and equip the {item.name}!", COLOR_CYAN)
                self.items.remove(item)
                self.turn = "monsters"
            elif isinstance(item, HealingPotion):
                if self.player.hp < self.player.max_hp:
                    heal_amount = min(self.player.max_hp - self.player.hp, item.amount)
                    self.player.hp += heal_amount
                    self.add_message(f"You drink the {item.name} and heal for {heal_amount} HP!", COLOR_GREEN)
                    self.items.remove(item)
                    self.turn = "monsters"
                else:
                    self.add_message("You are already at full health.", COLOR_WHITE)
            else:
                self.add_message(f"You pick up the {item.name}.", COLOR_WHITE)
                self.items.remove(item)
                self.turn = "monsters"
        else:
            self.add_message("There is nothing here to pick up.", COLOR_GREY)

    def player_move_or_attack(self, dx, dy):
        dest_x = self.player.x + dx
        dest_y = self.player.y + dy
        
        target = next((e for e in self.entities if e.x == dest_x and e.y == dest_y and e != self.player), None)
        
        if target:
            self.attack(self.player, target)
            self.turn = "monsters"
        elif not self.map.is_blocked(dest_x, dest_y):
            self.player.move(dx, dy)
            self.recompute_fov()
            self.turn = "monsters"

    def attack(self, attacker, target):
        roll = random.randint(1, 20)
        attack_roll = roll + attacker.get_modifier(attacker.strength)
        
        if roll == 20:
            damage = 0
            weapon = attacker.equipment.get("weapon")
            if weapon:
                for _ in range(weapon.damage_dice * 2): # Critical: double dice
                    damage += random.randint(1, weapon.damage_sides)
            else:
                damage = random.randint(1, 8) + random.randint(1, 8)
            
            damage += attacker.get_modifier(attacker.strength)
            target.hp -= damage
            self.add_message(f"CRITICAL HIT! {attacker.name} deals {damage} damage to {target.name}!", COLOR_GREEN)
        elif roll == 1:
            self.add_message(f"Critical Fail! {attacker.name} misses {target.name} miserably!", COLOR_RED)
        elif attack_roll >= target.armor_class:
            damage = 0
            weapon = attacker.equipment.get("weapon")
            if weapon:
                for _ in range(weapon.damage_dice):
                    damage += random.randint(1, weapon.damage_sides)
            else:
                damage = random.randint(1, 8)
            
            damage += attacker.get_modifier(attacker.strength)
            target.hp -= damage
            self.add_message(f"{attacker.name} hits {target.name} for {damage} (Roll: {attack_roll} vs AC {target.armor_class})")
        else:
            self.add_message(f"{attacker.name} misses {target.name} (Roll: {attack_roll} vs AC {target.armor_class})", COLOR_GREY)

        if target.hp <= 0:
            self.add_message(f"{target.name} dies!", COLOR_RED)
            if target == self.player:
                self.turn = "dead"
                self.add_message("GAME OVER", COLOR_RED)
            else:
                self.entities.remove(target)

    def handle_monster_turns(self):
        for monster in self.entities[1:]: # Skip player
            dx = 0
            dy = 0
            if monster.x < self.player.x: dx = 1
            elif monster.x > self.player.x: dx = -1
            if monster.y < self.player.y: dy = 1
            elif monster.y > self.player.y: dy = -1
            
            dest_x, dest_y = monster.x + dx, monster.y + dy
            
            if dest_x == self.player.x and dest_y == self.player.y:
                self.attack(monster, self.player)
            elif not self.map.is_blocked(dest_x, dest_y) and not any(e.x == dest_x and e.y == dest_y for e in self.entities):
                monster.move(dx, dy)
        
        self.turn = "player"

    def render(self):
        self.screen.fill(COLOR_BLACK)
        font = pygame.font.SysFont("courier", TILE_SIZE)
        
        # Draw Map
        for x in range(self.map.width):
            for y in range(self.map.height):
                tile = self.map.tiles[x][y]
                rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                if tile.visible:
                    if not tile.blocked:
                        pygame.draw.rect(self.screen, (30, 30, 30), rect)
                    else:
                        pygame.draw.rect(self.screen, (60, 60, 60), rect)
                elif tile.explored:
                    if not tile.blocked:
                        pygame.draw.rect(self.screen, (10, 10, 10), rect)
                    else:
                        pygame.draw.rect(self.screen, (20, 20, 20), rect)
                # Else: draw nothing (black background)

        # Draw Entities
        for entity in self.entities:
            if self.map.tiles[entity.x][entity.y].visible:
                text_surf = font.render(entity.char, True, entity.color)
                self.screen.blit(text_surf, (entity.x * TILE_SIZE + 4, entity.y * TILE_SIZE - 2))

        # Draw Items
        for item in self.items:
            if self.map.tiles[item.x][item.y].visible:
                text_surf = font.render(item.char, True, item.color)
                self.screen.blit(text_surf, (item.x * TILE_SIZE + 4, item.y * TILE_SIZE - 2))

        # UI
        self.render_ui()
        
        pygame.display.flip()

    def render_ui(self):
        font = pygame.font.SysFont("arial", 16)
        # Message Log
        y_offset = SCREEN_HEIGHT - 100
        for msg, color in self.message_log:
            text_surf = font.render(msg, True, color)
            self.screen.blit(text_surf, (10, y_offset))
            y_offset += 20
        
        # Player Stats
        armor_name = self.player.equipment["armor"].name if self.player.equipment["armor"] else "None"
        weapon_name = self.player.equipment["weapon"].name if self.player.equipment["weapon"] else "Unarmed"
        stats_text = f"HP: {self.player.hp}/{self.player.max_hp} | AC: {self.player.armor_class} ({armor_name}) | WPN: {weapon_name}"
        stats_surf = font.render(stats_text, True, COLOR_WHITE)
        self.screen.blit(stats_surf, (10, 10))
