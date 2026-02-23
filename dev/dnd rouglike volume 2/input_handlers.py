import pygame
from constants import GameState

class EventHandler:
    def __init__(self, engine):
        self.engine = engine

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.engine.running = False
            
            if self.engine.state == GameState.MAIN_MENU:
                self.handle_menu_events(event)
            elif self.engine.state == GameState.CLASS_SELECT:
                self.handle_class_select_events(event)
            elif self.engine.state == GameState.PLAYING:
                self.handle_playing_events(event)
            elif self.engine.state == GameState.GAME_OVER:
                self.handle_game_over_events(event)
            elif self.engine.state == GameState.INVENTORY_MENU:
                self.handle_inventory_events(event, "inventory")
            elif self.engine.state == GameState.EQUIP_MENU:
                self.handle_inventory_events(event, "equipment")
            elif self.engine.state == GameState.SHOP_MENU:
                self.handle_shop_events(event)
            elif self.engine.state == GameState.VICTORY:
                self.handle_victory_events(event)

    def handle_menu_events(self, event):
        from save_manager import SaveManager
        menu_options = ["New Game"]
        if SaveManager.save_exists():
            menu_options.append("Load Game")
        menu_options.append("Quit")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.engine.menu_index = (self.engine.menu_index - 1) % len(menu_options)
            elif event.key == pygame.K_DOWN:
                self.engine.menu_index = (self.engine.menu_index + 1) % len(menu_options)
            elif event.key == pygame.K_RETURN:
                selected = menu_options[self.engine.menu_index]
                if selected == "New Game":
                    self.engine.state = GameState.CLASS_SELECT
                    self.engine.menu_index = 0
                elif selected == "Load Game":
                    if not self.engine.load_game():
                        self.engine.add_message("Load failed!")
                elif selected == "Quit":
                    self.engine.running = False
            elif event.key == pygame.K_ESCAPE:
                self.engine.running = False

    def handle_class_select_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.engine.menu_index = (self.engine.menu_index - 1) % len(self.engine.available_classes)
            elif event.key == pygame.K_DOWN:
                self.engine.menu_index = (self.engine.menu_index + 1) % len(self.engine.available_classes)
            elif event.key == pygame.K_RETURN:
                print(f"DEBUG: Selected class index {self.engine.menu_index}")
                self.engine.start_game(self.engine.available_classes[self.engine.menu_index])
                print("DEBUG: start_game finished")
            elif event.key == pygame.K_ESCAPE:
                self.engine.state = GameState.MAIN_MENU
                self.engine.menu_index = 0

    def handle_game_over_events(self, event):
        from save_manager import SaveManager
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                SaveManager.delete_save() # Permadeath
                self.engine.state = GameState.MAIN_MENU
                self.engine.menu_index = 0

    def handle_victory_events(self, event):
        from save_manager import SaveManager
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                SaveManager.delete_save() # Run complete
                self.engine.state = GameState.MAIN_MENU
                self.engine.menu_index = 0

    def handle_inventory_events(self, event, menu_type):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or (menu_type == "inventory" and event.key == pygame.K_i) or (menu_type == "equipment" and event.key == pygame.K_e):
                self.engine.state = GameState.PLAYING
            
            items = self.engine.player.inventory.items
            if menu_type == "equipment":
                items = [item for item in items if getattr(item, 'owner', None) and item.owner.equippable]

            if event.key == pygame.K_UP:
                self.engine.menu_index = (self.engine.menu_index - 1) % len(items) if items else 0
            elif event.key == pygame.K_DOWN:
                self.engine.menu_index = (self.engine.menu_index + 1) % len(items) if items else 0
            elif event.key == pygame.K_RETURN:
                if items:
                    item = items[self.engine.menu_index]
                    if menu_type == "inventory":
                        msg = item.use(self.engine, self.engine.player)
                    else:
                        msg = self.engine.player.inventory.toggle_equip(item.owner)
                    self.engine.add_message(msg)

    def handle_shop_events(self, event):
        if event.type == pygame.KEYDOWN:
            items = self.engine.active_shop.get_stock()
            if event.key == pygame.K_ESCAPE:
                self.engine.state = GameState.PLAYING
                self.engine.active_shop = None
            elif event.key == pygame.K_UP:
                self.engine.menu_index = (self.engine.menu_index - 1) % len(items) if items else 0
            elif event.key == pygame.K_DOWN:
                self.engine.menu_index = (self.engine.menu_index + 1) % len(items) if items else 0
            elif event.key == pygame.K_RETURN:
                if items:
                    item, price = items[self.engine.menu_index]
                    if self.engine.player.fighter.gold >= price:
                        if self.engine.player.inventory.add_item(item):
                            self.engine.player.fighter.gold -= price
                            self.engine.add_message(f"You bought the {item.name}!")
                            from sound_manager import SoundManager
                            SoundManager.play_sound("pickup")
                            items.pop(self.engine.menu_index)
                            self.engine.menu_index = min(self.engine.menu_index, len(items) - 1) if items else 0
                        else:
                            self.engine.add_message("Your inventory is full!")
                    else:
                        self.engine.add_message("You don't have enough gold!")
            elif event.key == pygame.K_d:
                if items and menu_type == "inventory":
                    item = items[self.engine.menu_index]
                    if item.owner:
                        self.engine.player.inventory.remove_item(item)
                        item_entity = item.owner
                        item_entity.x, item_entity.y = self.engine.player.x, self.engine.player.y
                        self.engine.entities.append(item_entity)
                        self.engine.add_message(f"You drop the {item_entity.name}.")
                        self.engine.state = GameState.PLAYING
                    else:
                        self.engine.add_message("This item cannot be dropped.")

    def handle_playing_events(self, event):
        if event.type == pygame.KEYDOWN:
            dx, dy = 0, 0
            if event.key == pygame.K_ESCAPE:
                self.engine.state = GameState.MAIN_MENU
            elif event.key == pygame.K_UP:
                dy = -1
            elif event.key == pygame.K_DOWN:
                dy = 1
            elif event.key == pygame.K_LEFT:
                dx = -1
            elif event.key == pygame.K_RIGHT:
                dx = 1
            elif event.key == pygame.K_g:
                # Pickup item
                item_entity = next((e for e in self.engine.entities if e.x == self.engine.player.x and e.y == self.engine.player.y and e.item), None)
                if item_entity:
                    if self.engine.player.inventory.add_item(item_entity.item):
                        from sound_manager import SoundManager
                        SoundManager.play_sound("pickup")
                        self.engine.add_message(f"You pick up the {item_entity.name}.")
                        self.engine.entities.remove(item_entity)
                    else:
                        self.engine.add_message("Your inventory is full!")
                else:
                    self.engine.add_message("There is nothing here to pick up.")
            elif event.key == pygame.K_i:
                self.engine.state = GameState.INVENTORY_MENU
                self.engine.menu_index = 0
            elif event.key == pygame.K_e:
                self.engine.state = GameState.EQUIP_MENU
                self.engine.menu_index = 0
            elif event.key == pygame.K_a:
                if self.engine.player_class.starting_abilities:
                    ability = self.engine.player_class.starting_abilities[0]
                    msg = ability.activate(self.engine.player)
                    self.engine.add_message(msg)
                else:
                    self.engine.add_message("You have no special abilities.")
            elif event.key == pygame.K_s:
                self.engine.add_message("You search the area...")
                from dnd_rules import roll_dice
                for e in self.engine.entities:
                    if e.hazard and not e.hazard.is_revealed:
                        dist = abs(e.x - self.engine.player.x) + abs(e.y - self.engine.player.y)
                        if dist <= 2:
                            if roll_dice(1, 20) + self.engine.player.fighter.stats.wis_mod >= 10:
                                e.hazard.is_revealed = True
                                e.color = (255, 100, 100)
                                self.engine.add_message(f"You spotted a {e.name}!")
            elif event.key == pygame.K_c:
                # Prioritize equipped scroll as active spell
                active_scroll = self.engine.player.fighter.scroll
                if active_scroll:
                    msg = active_scroll.item.use(self.engine, self.engine.player)
                    self.engine.add_message(msg)
                elif self.engine.player_class.starting_spells:
                    spell = self.engine.player_class.starting_spells[0]
                    monsters = [e for e in self.engine.entities if e != self.engine.player and e.fighter]
                    if monsters:
                        nearest = min(monsters, key=lambda m: abs(m.x - self.engine.player.x) + abs(m.y - self.engine.player.y))
                        dist = abs(nearest.x - self.engine.player.x) + abs(nearest.y - self.engine.player.y)
                        if dist <= spell.range:
                            msg = spell.cast(self.engine, self.engine.player, nearest)
                            self.engine.add_message(msg)
                        else:
                            self.engine.add_message(f"Target is too far for {spell.name}!")
                    else:
                        self.engine.add_message("No monsters in range!")
                else:
                    self.engine.add_message("You don't have an active spell or any class spells!")
            elif event.key == pygame.K_RETURN:
                if any(e.stairs for e in self.engine.entities if e.x == self.engine.player.x and e.y == self.engine.player.y):
                    self.engine.dungeon_level += 1
                    self.engine.new_floor()
                else:
                    self.engine.add_message("There are no stairs here.")

            if dx != 0 or dy != 0:
                self.engine.player_turn(dx, dy)
