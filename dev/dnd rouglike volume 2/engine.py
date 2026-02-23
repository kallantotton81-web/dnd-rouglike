import pygame
import sys
import traceback

def exception_handler(extype, value, tb):
    with open("crash_log.txt", "w") as f:
        traceback.print_exception(extype, value, tb, file=f)
    sys.__excepthook__(extype, value, tb)

sys.excepthook = exception_handler

def log(msg):
    with open("debug_log.txt", "a") as f:
        f.write(f"{pygame.time.get_ticks()}: {msg}\n")
        f.flush()
    print(msg)
    sys.stdout.flush()
import random
from typing import List, Tuple, Optional
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, COLORS, GameState

from entity import Entity, Fighter
from inventory import Inventory
from dnd_rules import roll_dice
from map_tiles import GameMap
from procgen import generate_dungeon
from chr_classes import FighterClass, WizardClass, RogueClass
from save_manager import SaveManager
from ai_behaviors import HostileMelee, HostileRanged, HostileCaster
from sound_manager import SoundManager

class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("D&D Roguelike")
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen_shake = 0
        self.font = pygame.font.SysFont("Arial", 20)
        self.title_font = pygame.font.SysFont("Arial", 40)
        
        self.state = GameState.MAIN_MENU
        self.menu_index = 0
        self.available_classes = [FighterClass(), WizardClass(), RogueClass()]
        
        from input_handlers import EventHandler
        self.event_handler = EventHandler(self)
        
        log("Initializing SoundManager...")
        # Initialize Sound
        SoundManager().init_sounds()
        log("SoundManager initialized.")
        
        # Game Data (initialized on start)
        self.message_log: List[str] = []
        self.dungeon_level = 0
        self.player: Optional[Entity] = None
        self.entities: List[Entity] = []
        self.game_map: Optional[GameMap] = None
        self.vfx = [] # List of dicts: {'text': str, 'x': float, 'y': float, 'color': tuple, 'timer': int}
        self.active_shop = None # Stores Merchant component

    def add_vfx(self, text: str, x: int, y: int, color: tuple):
        """Adds a floating text effect at tile coordinates."""
        # Convert tile coords to screen pixels (center of tile)
        self.vfx.append({
            'text': text,
            'x': x * TILE_SIZE + TILE_SIZE // 2,
            'y': y * TILE_SIZE,
            'color': color,
            'timer': 40 # frames
        })

    def start_game(self, selected_class):
        log(f"Starting game with class: {selected_class.name}")
        self.state = GameState.PLAYING
        self.message_log = ["Welcome to the Dungeon!"]
        self.dungeon_level = 1
        self.player_class = selected_class
        p_stats = self.player_class.base_stats
        
        log("Calculating starting HP...")
        num, sides = map(int, self.player_class.hit_dice.split('d'))
        starting_hp = sides + p_stats.con_mod
        
        log(f"Creating player entity (HP={starting_hp})...")
        self.player = Entity(
            0, 0, "@", COLORS["gold"], "Player", 
            blocks_movement=True,
            fighter=Fighter(None, hp=starting_hp, ac=10 + p_stats.dex_mod, stats=p_stats, chr_class=self.player_class, lives=3),
            inventory=Inventory(capacity=10)
        )
        log("Calling new_floor()...")
        self.new_floor()
        log("Back from new_floor(). Loading music...")
        # Start music if available
        try:
            SoundManager.play_music("assets/sounds/ambient.mp3")
            log("Music play called.")
        except Exception as e:
            log(f"Music play FAILED: {e}")
            
        log("Saving game...")
        # Save on start
        try:
            SaveManager.save_game(self)
            log("Initial save complete.")
        except Exception as e:
            log(f"Initial save FAILED: {e}")
            
        log("Game started successfully!")

    def load_game(self):
        save_data = SaveManager.load_game()
        if save_data:
            self.player = save_data["player"]
            self.entities = save_data["entities"]
            self.game_map = save_data["game_map"]
            self.message_log = save_data["message_log"]
            self.dungeon_level = save_data["dungeon_level"]
            self.player_class = save_data["player_class"]
            self.state = GameState.PLAYING
            self.add_message("Game Loaded!")
            return True
        return False

    def new_floor(self):
        log(f"Entering new_floor() - Level {self.dungeon_level}")
        
        # Victory Condition
        if self.dungeon_level > 20:
            self.state = GameState.VICTORY
            return

        # Keep only player
        self.entities = [self.player]
        
        # Scale dungeon size and complexity
        width = min(45, 25 + (self.dungeon_level - 1) * 2)
        height = min(35, 18 + (self.dungeon_level - 1))
        rooms = min(25, 10 + (self.dungeon_level - 1))

        log(f"Generating dungeon floor (size {width}x{height}, rooms {rooms})...")
        self.game_map = generate_dungeon(
            map_width=width, 
            map_height=height, 
            max_rooms=rooms, 
            room_min_size=4, 
            room_max_size=8, 
            engine=self
        )
        log("Dungeon floor generated.")
        self.add_message("You descend deeper into the dungeon...")
        SoundManager.play_sound("stairs")
        log("Auto-saving...")
        # Auto-save on floor transition
        SaveManager.save_game(self)
        log("new_floor() complete.")

    def add_message(self, text: str):
        self.message_log.append(text)
        if len(self.message_log) > 5:
            self.message_log.pop(0)

    def handle_events(self):
        self.event_handler.handle_events()

    def player_turn(self, dx: int, dy: int):
        # Slow Logic: chance to stumble and lose action
        if "Slow" in self.player.fighter.status_effects and random.random() < 0.5:
            self.add_message("You are slowed and stumble!")
            self.player.fighter.tick_effects() # Still count down effects
            self.monster_turn()
            return

        new_x, new_y = self.player.x + dx, self.player.y + dy
        
        target = next((e for e in self.entities if e.x == new_x and e.y == new_y and e.fighter), None)
        if target:
            msg = self.player.fighter.attack(target, self)
            self.add_message(msg)
            if target.fighter.hp <= 0:
                xp_gain = getattr(target.fighter, 'xp_value', 50)
                self.player.fighter.xp += xp_gain
                
                # New: Gold Drop
                gold_gain = roll_dice(1, 10) * self.dungeon_level
                self.player.fighter.gold += gold_gain
                self.add_message(f"{target.name} dies! You gain {xp_gain} XP and {gold_gain} GP.")
                self.entities.remove(target)
                
                from leveling import check_level_up
                if check_level_up(self.player):
                    self.add_message(f"You leveled up to Level {self.player.fighter.level}!")
        else:
            # Check for interactive objects (barrels, chests)
            interact_target = next((e for e in self.entities if e.x == new_x and e.y == new_y and e.interactive and not e.interactive.is_broken), None)
            if interact_target:
                msg = interact_target.interactive.interact(self, self.player)
                self.add_message(msg)
            elif self.game_map.is_walkable(new_x, new_y):
                self.player.move(dx, dy)
                
                # Check for Traps
                hazard_target = next((e for e in self.entities if e.x == self.player.x and e.y == self.player.y and e.hazard), None)
                if hazard_target:
                    msg = hazard_target.hazard.trigger(self, self.player)
                    self.add_message(msg)
                    hazard_target.hazard.is_revealed = True
                    hazard_target.color = (255, 0, 0) # Reveal as red

                # New: Auto-collect Gold
                gold_entity = next((e for e in self.entities if e.x == self.player.x and e.y == self.player.y and hasattr(e, 'gold_value')), None)
                if gold_entity:
                    self.player.fighter.gold += gold_entity.gold_value
                    self.add_message(f"You collect {gold_entity.gold_value} gold.")
                    self.add_vfx(f"+{gold_entity.gold_value} GP", self.player.x, self.player.y, COLORS["gold"])
                    self.entities.remove(gold_entity)

        # Tick effects and cooldowns
        self.player.fighter.tick_effects()
        for ability in self.player_class.starting_abilities:
            if ability.current_cooldown > 0:
                ability.current_cooldown -= 1
        
        # Check for player death
        if self.check_player_death():
            return
        else:
            # Monsters take their turn if player is alive
            # Haste Logic: skip monster turn if player is hasted (50% chance for extra turn)
            if "Haste" in self.player.fighter.status_effects and random.random() < 0.5:
                self.add_message("Haste grants you an extra action!")
            else:
                self.monster_turn()

    def monster_turn(self):
        for entity in self.entities:
            if entity.ai and entity.fighter and entity.fighter.hp > 0:
                entity.ai.perform(self, entity)
                
                # Check if player died during monster turns
                if self.check_player_death():
                    break

    def check_player_death(self) -> bool:
        """Returns True if the player is permanently dead (GameOver)."""
        if self.player.fighter.hp <= 0:
            from sound_manager import SoundManager
            if self.player.fighter.lives > 1:
                self.player.fighter.lives -= 1
                self.player.fighter.hp = self.player.fighter.max_hp
                self.add_message(f"You have lost a life! {self.player.fighter.lives} lives remaining.")
                self.add_message("You are restored to full health.")
                SoundManager.play_sound("level_up") # Re-use level up sound for respawn
                return False
            else:
                self.add_message("You have died!")
                SoundManager.play_sound("death")
                self.state = GameState.GAME_OVER
                return True
        return False

    def update(self):
        if self.screen_shake > 0:
            self.screen_shake -= 1
            
        # Update VFX
        for effect in self.vfx[:]:
            effect['timer'] -= 1
            effect['y'] -= 1 # Float up
            if effect['timer'] <= 0:
                self.vfx.remove(effect)

    def render_bar(self, x, y, width, current, maximum, color):
        """Draws a progress bar (HP or XP)."""
        bar_height = 15
        fill_width = int((current / maximum) * width) if maximum > 0 else 0
        
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), (x, y, width, bar_height))
        # Fill
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_width, bar_height))
        # Border
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, width, bar_height), 1)

    def render(self):
        self.screen.fill(COLORS["black"])
        
        if self.state == GameState.MAIN_MENU:
            self.render_menu()
        elif self.state == GameState.CLASS_SELECT:
            self.render_class_select()
        elif self.state == GameState.PLAYING:
            self.render_game()
        elif self.state == GameState.GAME_OVER:
            self.render_game_over()
        elif self.state == GameState.VICTORY:
            self.render_victory()
        elif self.state == GameState.INVENTORY_MENU:
            self.render_game()
            self.render_inventory("INVENTORY (Use/Drop)", self.player.inventory.items)
        elif self.state == GameState.EQUIP_MENU:
            self.render_game()
            equippables = [item for item in self.player.inventory.items if getattr(item, 'owner', None) and item.owner.equippable]
            self.render_inventory("EQUIPMENT (Toggle Equip)", equippables)
        elif self.state == GameState.SHOP_MENU:
            self.render_shop()

        pygame.display.flip()

    def render_shop(self):
        self.screen.fill(COLORS["black"])
        title = self.title_font.render("--- MERCHANT'S SHOP ---", True, COLORS["gold"])
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        if not self.active_shop:
            return

        items = self.active_shop.get_stock()
        for i, (item, price) in enumerate(items):
            color = COLORS["white"] if i == self.menu_index else (150, 150, 150)
            text = f"{item.name} - {price} GP"
            item_surf = self.font.render(text, True, color)
            self.screen.blit(item_surf, (SCREEN_WIDTH // 2 - 100, 150 + i * 30))

        gold_text = self.font.render(f"Your Gold: {self.player.fighter.gold} GP", True, COLORS["white"])
        self.screen.blit(gold_text, (SCREEN_WIDTH // 2 - gold_text.get_width() // 2, SCREEN_HEIGHT - 100))
        
        help_text = self.font.render("[ENTER] Buy | [ESC] Leave", True, COLORS["gray"])
        self.screen.blit(help_text, (SCREEN_WIDTH // 2 - help_text.get_width() // 2, SCREEN_HEIGHT - 50))

    def render_inventory(self, title, items):
        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Panel
        panel_width = 400
        panel_height = 400
        pygame.draw.rect(self.screen, (50, 50, 50), (SCREEN_WIDTH // 2 - panel_width // 2, 50, panel_width, panel_height))
        pygame.draw.rect(self.screen, COLORS["white"], (SCREEN_WIDTH // 2 - panel_width // 2, 50, panel_width, panel_height), 2)

        title_surf = self.title_font.render(title, True, COLORS["gold"])
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 70))

        if not items:
            none_surf = self.font.render("No items.", True, (150, 150, 150))
            self.screen.blit(none_surf, (SCREEN_WIDTH // 2 - none_surf.get_width() // 2, 150))
        else:
            for i, item in enumerate(items):
                color = COLORS["gold"] if i == self.menu_index else COLORS["white"]
                name = item.name if item.is_identified else "Unknown item"
                
                # Show if equipped
                if self.player.fighter.weapon == item.owner or self.player.fighter.armor == item.owner:
                    name += " (E)"
                
                # Show charges
                if item.charges is not None:
                    name += f" ({item.charges} chg)"
                
                item_surf = self.font.render(f"{'> ' if i == self.menu_index else ''}{name}", True, color)
                self.screen.blit(item_surf, (SCREEN_WIDTH // 2 - panel_width // 2 + 20, 150 + (i * 25)))

        instruct_surf = self.font.render("Arrow Keys to move, ENTER to select, D to drop, ESC to close", True, (150, 150, 150))
        self.screen.blit(instruct_surf, (SCREEN_WIDTH // 2 - instruct_surf.get_width() // 2, 430))

    def render_menu(self):
        title_surf = self.title_font.render("D&D ROGUELIKE", True, COLORS["gold"])
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
        
        menu_options = ["New Game"]
        if SaveManager.save_exists():
            menu_options.append("Load Game")
        menu_options.append("Quit")

        for i, option in enumerate(menu_options):
            color = COLORS["gold"] if i == self.menu_index else COLORS["white"]
            opt_surf = self.font.render(f"{'> ' if i == self.menu_index else ''}{option}", True, color)
            self.screen.blit(opt_surf, (SCREEN_WIDTH // 2 - opt_surf.get_width() // 2, 250 + (i * 35)))

    def render_class_select(self):
        title_surf = self.title_font.render("CHOOSE YOUR CLASS", True, COLORS["gold"])
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
        
        for i, chr_class in enumerate(self.available_classes):
            color = COLORS["gold"] if i == self.menu_index else COLORS["white"]
            class_surf = self.font.render(f"{'> ' if i == self.menu_index else ''}{chr_class.name}", True, color)
            self.screen.blit(class_surf, (SCREEN_WIDTH // 2 - class_surf.get_width() // 2, 250 + (i * 35)))
            
            # Show class description or teaser
            desc = f"{chr_class.hit_dice} Hit Dice"
            desc_surf = self.font.render(desc, True, (150, 150, 150))
            self.screen.blit(desc_surf, (SCREEN_WIDTH // 2 - desc_surf.get_width() // 2, 250 + (i * 35) + 20))

        instruct_surf = self.font.render("ESC to go back", True, (100, 100, 100))
        self.screen.blit(instruct_surf, (SCREEN_WIDTH // 2 - instruct_surf.get_width() // 2, SCREEN_HEIGHT - 50))

    def render_game_over(self):
        # Still render the background game if possible
        if self.game_map:
            self.render_game()
            # Overlay dim
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

        dead_surf = self.title_font.render("YOU HAVE DIED", True, (255, 0, 0))
        self.screen.blit(dead_surf, (SCREEN_WIDTH // 2 - dead_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        restart_surf = self.font.render("Press ENTER to return to Menu", True, COLORS["white"])
        self.screen.blit(restart_surf, (SCREEN_WIDTH // 2 - restart_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def render_victory(self):
        if self.game_map:
            self.render_game()
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

        vic_surf = self.title_font.render("CONGRATULATIONS!", True, (0, 255, 0))
        self.screen.blit(vic_surf, (SCREEN_WIDTH // 2 - vic_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        
        text1 = self.font.render("You have conquered the Dungeon!", True, COLORS["white"])
        self.screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        
        text2 = self.font.render(f"Final Gold: {self.player.fighter.gold} GP", True, COLORS["gold"])
        self.screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

        restart_surf = self.font.render("Press ENTER to return to Menu", True, COLORS["white"])
        self.screen.blit(restart_surf, (SCREEN_WIDTH // 2 - restart_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

    def render_game(self):
        # Apply screen shake offset
        offset_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        offset_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        # Original render logic moved here
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                tile = self.game_map.tiles[x][y]
                pygame.draw.rect(self.screen, (20, 20, 20), 
                                (x * TILE_SIZE + offset_x, y * TILE_SIZE + offset_y, TILE_SIZE, TILE_SIZE))
                tile_surf = self.font.render(tile.char, True, tile.color)
                self.screen.blit(tile_surf, (x * TILE_SIZE + 8 + offset_x, y * TILE_SIZE + 4 + offset_y))

        for entity in self.entities:
            # Only draw hazards if revealed
            if entity.hazard and not entity.hazard.is_revealed:
                continue
            text_surface = self.font.render(entity.char, True, entity.color)
            self.screen.blit(text_surface, (entity.x * TILE_SIZE + 8 + offset_x, entity.y * TILE_SIZE + 4 + offset_y))

        # HUD - Bars
        f = self.player.fighter
        hud_y = SCREEN_HEIGHT - 60
        
        # HP Bar
        hp_color = (200, 0, 0)
        self.render_bar(10, hud_y, 200, f.hp, f.max_hp, hp_color)
        hp_text = self.font.render(f"HP: {f.hp}/{f.max_hp}", True, COLORS["white"])
        self.screen.blit(hp_text, (220, hud_y))

        # XP Bar
        from leveling import get_xp_for_level
        current_lvl_xp = get_xp_for_level(f.level)
        next_lvl_xp = get_xp_for_level(f.level + 1)
        xp_needed = next_lvl_xp - current_lvl_xp
        xp_current = f.xp - current_lvl_xp
        
        xp_color = (0, 150, 250)
        self.render_bar(10, hud_y + 25, 200, xp_current, xp_needed, xp_color)
        
        active_spell = "None"
        if f.scroll:
            if f.scroll.item.is_identified:
                active_spell = f.scroll.name
            else:
                active_spell = "Unknown Scroll"
        elif self.player_class.starting_spells:
            active_spell = self.player_class.starting_spells[0].name
            
        info_text = f"Floor {self.dungeon_level} | {self.player_class.name} Lvl {f.level} | {f.gold} GP | Lives: {f.lives}"
        active_text = f"Active Spell (C): {active_spell}"
        
        info_surf = self.font.render(info_text, True, COLORS["gold"])
        active_surf = self.font.render(active_text, True, (100, 200, 255))
        
        self.screen.blit(info_surf, (220, hud_y + 25))
        self.screen.blit(active_surf, (SCREEN_WIDTH - 250, hud_y + 25))

        # Message Log
        for i, msg in enumerate(self.message_log[-5:]): # Only show last 5 messages
            msg_surface = self.font.render(msg, True, COLORS["white"])
            self.screen.blit(msg_surface, (10, SCREEN_HEIGHT - 130 + (i * 20)))

        # Draw VFX
        for effect in self.vfx:
            vfx_surf = self.font.render(effect['text'], True, effect['color'])
            # Center horizontally over tile, vertical starts at effect['y']
            self.screen.blit(vfx_surf, (effect['x'] - vfx_surf.get_width() // 2, effect['y']))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    engine = Engine()
    engine.run()
