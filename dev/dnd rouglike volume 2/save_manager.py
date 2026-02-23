import pickle
import os
from typing import Optional

class SaveManager:
    SAVE_FILE = "savegame.sav"

    @classmethod
    def save_game(cls, engine) -> bool:
        """Serializes the current game state to a file."""
        try:
            save_data = {
                "player": engine.player,
                "entities": engine.entities,
                "game_map": engine.game_map,
                "message_log": engine.message_log,
                "dungeon_level": engine.dungeon_level,
                "player_class": engine.player_class
            }
            with open(cls.SAVE_FILE, "wb") as f:
                pickle.dump(save_data, f)
            return True
        except Exception as e:
            print(f"Failed to save game: {e}")
            return False

    @classmethod
    def load_game(cls) -> Optional[dict]:
        """Deserializes the game state from the save file."""
        if not os.path.exists(cls.SAVE_FILE):
            return None
        
        try:
            with open(cls.SAVE_FILE, "rb") as f:
                save_data = pickle.load(f)
            return save_data
        except Exception as e:
            print(f"Failed to load game: {e}")
            return None

    @classmethod
    def delete_save(cls):
        """Removes the save file (usually on player death)."""
        if os.path.exists(cls.SAVE_FILE):
            os.remove(cls.SAVE_FILE)

    @classmethod
    def save_exists(cls) -> bool:
        """Checks if a save file currently exists."""
        return os.path.exists(cls.SAVE_FILE)
