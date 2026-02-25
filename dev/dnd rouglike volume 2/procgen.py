import random
from typing import List, Tuple, TYPE_CHECKING
from map_tiles import GameMap, Tile
from entity import Entity, Fighter, Equippable
import monsters
import bosses
from dnd_rules import Stats
from ai_behaviors import HostileMelee, HostileRanged, HostileCaster, BossExpertAI
from constants import COLORS

if TYPE_CHECKING:
    from engine import Engine

class Room:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    @property
    def center(self) -> Tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersects(self, other: 'Room') -> bool:
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

def generate_dungeon(map_width: int, map_height: int, max_rooms: int, room_min_size: int, room_max_size: int, engine: 'Engine') -> GameMap:
    game_map = GameMap(map_width, map_height)
    rooms: List[Room] = []

    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(0, map_width - w - 1)
        y = random.randint(0, map_height - h - 1)

        new_room = Room(x, y, w, h)
        if any(new_room.intersects(other) for other in rooms):
            continue

        # Fill room with floor tiles
        for room_x in range(new_room.x1 + 1, new_room.x2):
            for room_y in range(new_room.y1 + 1, new_room.y2):
                game_map.tiles[room_x][room_y] = Tile(".", (50, 50, 50), walkable=True, transparent=True)

        if not rooms:
            # First room, place player
            px, py = new_room.center
            engine.player.x, engine.player.y = px, py
        else:
            # Connect to previous room
            prev_x, prev_y = rooms[-1].center
            new_x, new_y = new_room.center
            if random.random() < 0.5:
                create_v_tunnel(game_map, prev_y, new_y, new_x)
                create_h_tunnel(game_map, prev_x, new_x, prev_y)
            else:
                create_v_tunnel(game_map, prev_y, new_y, prev_x)
                create_h_tunnel(game_map, prev_x, new_x, new_y)

        # Roll for room theme
        theme = "normal"
        if len(rooms) > 0: # Don't theme the first room
            r = random.random()
            if r < 0.1: theme = "armory"
            elif r < 0.2: theme = "library"
            elif r < 0.25: theme = "vault"
            
        place_entities(new_room, engine, theme=theme)
        rooms.append(new_room)

    # Special Shops on certain floors
    if engine.dungeon_level % 3 == 0 and engine.dungeon_level % 5 != 0:
        rooms = []
        game_map = GameMap(map_width, map_height)
        # Small cozy shop room
        w, h = 8, 8
        x, y = map_width // 2 - 4, map_height // 2 - 4
        new_room = Room(x, y, w, h)
        for rx in range(new_room.x1 + 1, new_room.x2):
            for ry in range(new_room.y1 + 1, new_room.y2):
                game_map.tiles[rx][ry] = Tile(".", (80, 60, 40), walkable=True, transparent=True)
        
        # Player at door, Merchant at counter
        px, py = new_room.center
        engine.player.x, engine.player.y = px, py + 2
        place_merchant(new_room, engine)
        rooms.append(new_room)

    # Boss Floor Special: One giant room if dungeon_level % 5 == 0
    if engine.dungeon_level % 5 == 0:
        rooms = []
        game_map = GameMap(map_width, map_height) # Clear map
        # Single large room
        w, h = map_width - 4, map_height - 12
        x, y = 2, 2
        new_room = Room(x, y, w, h)
        for rx in range(new_room.x1 + 1, new_room.x2):
            for ry in range(new_room.y1 + 1, new_room.y2):
                game_map.tiles[rx][ry] = Tile(".", (50, 50, 50), walkable=True, transparent=True)
        
        # Center player and place boss
        px, py = new_room.center
        engine.player.x, engine.player.y = px, py + 5
        place_boss(new_room, engine)
        rooms.append(new_room)

    # Place stairs in last room
    sx, sy = rooms[-1].center
    from entity import Entity
    stairs = Entity(sx, sy, ">", (255, 255, 255), "Stairs", stairs=True)
    engine.entities.append(stairs)

    engine.game_map = game_map
    return game_map

def create_h_tunnel(game_map, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        game_map.tiles[x][y] = Tile(".", (100, 100, 100), walkable=True, transparent=True)

def create_v_tunnel(game_map, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        game_map.tiles[x][y] = Tile(".", (100, 100, 100), walkable=True, transparent=True)

def place_entities(room: Room, engine: 'Engine', theme: str = "normal"):
    # Label room if special
    if theme != "normal":
        tx, ty = room.x1 + 1, room.y1 + 1
        # (Optional: add a message or mark the room somehow)
        pass

    number_of_monsters = random.randint(0, 2)
    if theme == "vault": number_of_monsters += 2 # Half-guarded vault
    for _ in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(e.x == x and e.y == y for e in engine.entities):
            r = random.random()
            if engine.dungeon_level < 3:
                if r < 0.4: m_data = monsters.get_kobold()
                elif r < 0.8: m_data = monsters.get_goblin()
                else: m_data = monsters.get_orc()
            else:
                # deeper floors get variety
                if r < 0.2: m_data = monsters.get_kobold()
                elif r < 0.4: m_data = monsters.get_goblin()
                elif r < 0.6: m_data = monsters.get_skeleton()
                elif r < 0.8: m_data = monsters.get_goblin_archer()
                elif r < 0.9: m_data = monsters.get_evil_acolyte()
                else: m_data = monsters.get_orc()

            # Scaled Stats
            bonus = (engine.dungeon_level - 1) // 2
            m_stats = Stats(
                m_data.stats.strength + bonus,
                m_data.stats.dexterity + bonus,
                m_data.stats.constitution + bonus,
                m_data.stats.intelligence,
                m_data.stats.wisdom,
                m_data.stats.charisma
            )
            
            # Instantiate AI based on monster data
            if m_data.ai_type == "melee":
                ai_component = HostileMelee()
            elif m_data.ai_type == "ranged":
                ai_component = HostileRanged(range=5)
            elif m_data.ai_type == "caster":
                ai_component = HostileCaster(spell_range=6)
            else:
                ai_component = HostileMelee()

            monster_entity = Entity(
                x, y, m_data.char, m_data.color, m_data.name,
                blocks_movement=True,
                fighter=Fighter(None, hp=m_data.hp + (bonus*2), ac=m_data.ac + bonus, stats=m_stats),
                ai=ai_component
            )
            # Add custom attribute for XP value used in engine
            monster_entity.fighter.xp_value = m_data.xp_value
            engine.entities.append(monster_entity)

    # Items spawning logic
    item_chance = 0.3
    if theme in ["armory", "library", "vault"]: item_chance = 0.8
    
    number_of_items = 0
    if random.random() < item_chance:
        number_of_items = random.randint(1, 3) if theme != "normal" else 1

    # Import item-related names once at the top to avoid UnboundLocalError
    from items import Item, heal, use_scroll
    from entity import Equippable as EquippableComp
    from spells import FireballSpell, MagicMissileSpell, BlindSpell, HasteSpell, SlowSpell

    for _ in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(e.x == x and e.y == y for e in engine.entities):
            r = random.random()
            # Skew r based on theme
            if theme == "armory": r = 0.5 # Force equipment
            elif theme == "library": r = 0.85 # Force scrolls/wands
            elif theme == "vault": r = 0.99 # Force gold/traps
            
            if r < 0.4:
                item_component = Item(name="Healing Potion", char="!", color=(0, 255, 0), use_function=heal, amount=10)
                item_entity = Entity(x, y, item_component.char, item_component.color, item_component.name, item=item_component)
                engine.entities.append(item_entity)
            elif r < 0.7:
                # Spawn weapons/armor
                roll = random.random()
                if roll < 0.02:
                    # Legendary Excalibur!
                    item_component = Item(name="Excalibur", char="/", color=(255, 215, 0))
                    equippable = EquippableComp(None, slot="weapon", damage_dice="2d20")
                elif roll < 0.07:
                    # Rare God Sword!
                    item_component = Item(name="Sword of Antigravity", char="/", color=(255, 0, 255))
                    equippable = EquippableComp(None, slot="weapon", damage_dice="100d1")
                elif roll < 0.5:
                    item_component = Item(name="Longsword", char="/", color=(200, 200, 200))
                    equippable = EquippableComp(None, slot="weapon", damage_dice="1d8")
                else:
                    item_component = Item(name="Chainmail", char="[", color=(150, 150, 150))
                    equippable = EquippableComp(None, slot="armor", ac_bonus=4)
                item_entity = Entity(x, y, item_component.char, item_component.color, item_component.name, item=item_component, equippable=equippable)
                engine.entities.append(item_entity)
            elif r < 0.9:
                # Scrolls
                spell = random.choice([FireballSpell(), MagicMissileSpell(), BlindSpell(), HasteSpell(), SlowSpell()])
                item_component = Item(name=f"Scroll of {spell.name}", char="?", color=(200, 200, 0), use_function=use_scroll, is_identified=False, spell=spell)
                equippable = EquippableComp(None, slot="scroll")
                item_entity = Entity(x, y, item_component.char, item_component.color, item_component.name, item=item_component, equippable=equippable)
                engine.entities.append(item_entity)
            else:
                # Wands
                spell = MagicMissileSpell()
                charges = random.randint(3, 7)
                item_component = Item(name=f"Wand of {spell.name}", char="|", color=(200, 0, 200), use_function=use_scroll, charges=charges, is_identified=False, spell=spell)
                equippable = EquippableComp(None, slot="scroll")
                item_entity = Entity(x, y, item_component.char, item_component.color, item_component.name, item=item_component, equippable=equippable)
                engine.entities.append(item_entity)

    # Gold spawning
    if random.random() < 0.5:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(e.x == x and e.y == y for e in engine.entities):
            gold_amount = random.randint(5, 15) * engine.dungeon_level
            gold_item = Entity(x, y, "$", COLORS["gold"], f"{gold_amount} Gold Piles", blocks_movement=False)
            gold_item.gold_value = gold_amount
            engine.entities.append(gold_item)

    # Hazards (Traps, Barrels, Chests, and Vault Gold)
    trap_chance = 0.3
    if theme == "vault": trap_chance = 0.7
    
    if random.random() < trap_chance:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(e.x == x and e.y == y for e in engine.entities):
            from hazards import Hazard, spike_trap
            h = Hazard(name="Spike Trap", trigger_func=spike_trap)
            e = Entity(x, y, "^", (100, 100, 100), "Hidden Trap", hazard=h)
            engine.entities.append(e)

    # Vault special: extra gold
    if theme == "vault":
        for _ in range(3):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if not any(e.x == x and e.y == y for e in engine.entities):
                gold_amount = random.randint(20, 50) * engine.dungeon_level
                gold_item = Entity(x, y, "$", COLORS["gold"], f"{gold_amount} Gold Vault", blocks_movement=False)
                gold_item.gold_value = gold_amount
                engine.entities.append(gold_item)

    if random.random() < 0.4:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(e.x == x and e.y == y for e in engine.entities):
            from hazards import Interactive, smash_barrel
            i = Interactive(name="Barrel", interact_func=smash_barrel)
            e = Entity(x, y, "o", (139, 69, 19), "Barrel", interactive=i)
            engine.entities.append(e)

    if random.random() < 0.2:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        if not any(e.x == x and e.y == y for e in engine.entities):
            from hazards import Interactive, open_chest
            i = Interactive(name="Chest", interact_func=open_chest)
            e = Entity(x, y, "=", (255, 215, 0), "Treasure Chest", interactive=i)
            engine.entities.append(e)

def place_boss(room: Room, engine: 'Engine'):
    import bosses
    from ai_behaviors import BossExpertAI
    
    # Select boss based on level
    if engine.dungeon_level == 5:
        m_data = bosses.get_orc_king()
    elif engine.dungeon_level == 10:
        m_data = bosses.get_lich()
    else:
        # Fallback/Scale Orc King for later bosses
        m_data = bosses.get_orc_king()
        m_data.name = f"Ancient {m_data.name}"
        m_data.hp += (engine.dungeon_level // 5) * 50
        m_data.ac += (engine.dungeon_level // 5) * 2

    # Instantiate Boss AI
    ai_component = BossExpertAI(spell_range=7)
    
    bx, by = room.center
    boss_entity = Entity(
        bx, by, m_data.char, m_data.color, m_data.name,
        blocks_movement=True,
        fighter=Fighter(None, hp=m_data.hp, ac=m_data.ac, stats=m_data.stats),
        ai=ai_component
    )
    monster_entity = boss_entity # reuse variable name for convenience
    monster_entity.fighter.xp_value = m_data.xp_value
    engine.entities.append(monster_entity)
    
    # Boss Reward: Greater Chest
    from hazards import Interactive, open_chest
    i = Interactive(name="Greater Chest", interact_func=open_chest)
    # Custom chest to spawn better loot? (Simplified for now)
    e = Entity(bx + 1, by + 1, "=", (255, 100, 255), "Greater Treasure Chest", interactive=i)
    engine.entities.append(e)

def place_merchant(room: Room, engine: 'Engine'):
    from merchant import Merchant, setup_merchant_stock
    m_comp = Merchant()
    m_comp.inventory = setup_merchant_stock(engine)
    
    mx, my = room.center
    merchant_entity = Entity(
        mx, my, "M", (255, 255, 255), "Merchant",
        blocks_movement=True,
        interactive=m_comp
    )
    engine.entities.append(merchant_entity)
    
    # Add some decorative "shelves" or tables
    from map_tiles import Tile
    for dx in [-1, 1]:
        engine.game_map.tiles[mx + dx][my] = Tile("T", (139, 69, 19), walkable=False, transparent=True)
