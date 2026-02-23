import pygame
import os
from typing import Dict, Optional

class SoundManager:
    _instance = None
    _sounds: Dict[str, pygame.mixer.Sound] = {}
    _music_volume = 0.5
    _sfx_volume = 0.7

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Failed to initialize pygame.mixer: {e}")
        return cls._instance

    @classmethod
    def load_sound(cls, name: str, filename: str):
        """Loads a sound effect if the file exists."""
        if os.path.exists(filename):
            try:
                sound = pygame.mixer.Sound(filename)
                sound.set_volume(cls._sfx_volume)
                cls._sounds[name] = sound
            except Exception as e:
                print(f"Could not load sound {filename}: {e}")

    @classmethod
    def play_sound(cls, name: str):
        """Plays a loaded sound effect."""
        if name in cls._sounds:
            cls._sounds[name].play()

    @classmethod
    def play_music(cls, filename: str, loops: int = -1):
        """Plays background music if the file exists."""
        if os.path.exists(filename):
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.set_volume(cls._music_volume)
                pygame.mixer.music.play(loops)
            except Exception as e:
                print(f"Could not play music {filename}: {e}")

    @classmethod
    def stop_music(cls):
        pygame.mixer.music.stop()

    @classmethod
    def set_sfx_volume(cls, volume: float):
        cls._sfx_volume = volume
        for sound in cls._sounds.values():
            sound.set_volume(volume)

    @classmethod
    def set_music_volume(cls, volume: float):
        cls._music_volume = volume
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(volume)

    @classmethod
    def init_sounds(cls):
        """Pre-loads default game sounds if they exist."""
        # Folder structure for sounds
        sound_dir = "assets/sounds"
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir, exist_ok=True)
            return # Exit if we just created the dir (it's empty)

        # Examples of sounds we might look for
        cls.load_sound("hit", os.path.join(sound_dir, "hit.wav"))
        cls.load_sound("miss", os.path.join(sound_dir, "miss.wav"))
        cls.load_sound("pickup", os.path.join(sound_dir, "pickup.wav"))
        cls.load_sound("level_up", os.path.join(sound_dir, "level_up.wav"))
        cls.load_sound("death", os.path.join(sound_dir, "death.wav"))
        cls.load_sound("spell", os.path.join(sound_dir, "spell.wav"))
        cls.load_sound("stairs", os.path.join(sound_dir, "stairs.wav"))
        cls.load_sound("trap", os.path.join(sound_dir, "trap.wav"))
        cls.load_sound("interact", os.path.join(sound_dir, "interact.wav"))
