import random


NATURES = {
    "Hardy": (None, None),
    "Lonely": ("attack", "defense"),
    "Brave": ("attack", "speed"),
    "Adamant": ("attack", "special_attack"),
    "Bold": ("defense", "attack"),
    "Timid": ("speed", "attack"),
    "Jolly": ("speed", "special_attack"),
    "Modest": ("special_attack", "attack"),
}

TYPE_ABILITIES = {
    "fire": ["Blaze", "Flash Fire"],
    "water": ["Torrent", "Water Absorb"],
    "grass": ["Overgrow", "Chlorophyll"],
    "electric": ["Static", "Lightning Rod"],
    "bug": ["Swarm", "Shield Dust"],
    "poison": ["Poison Point", "Overcoat"],
    "normal": ["Adaptability", "Run Away"],
    "flying": ["Keen Eye", "Big Pecks"],
}


class PokemonTraitsService:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()

    def roll(self, types: list[str], species_data=None):
        nature = self.rng.choice(list(NATURES))
        ability_pool = TYPE_ABILITIES.get(types[0], ["Adaptability"])
        if species_data is not None:
            ability_pool = [a['name'] for a in species_data['abilities'] if not a['hidden']]
            if not ability_pool:
                ability_pool = [a['name'] for a in species_data['abilities']]
        rate = species_data.get('gender_rate') if species_data is not None else None
        gender = ('genderless' if rate == -1 else 'male' if rate == 0 else 'female' if rate == 8
                  else ('female' if self.rng.random() < rate / 8 else 'male') if rate is not None
                  else self.rng.choice(['male', 'female']))
        return {
            "nature": nature,
            "ability": self.rng.choice(ability_pool),
            "gender": gender,
        }

    @staticmethod
    def nature_multiplier(nature: str, stat: str) -> float:
        boosted, reduced = NATURES.get(nature, (None, None))
        return 1.1 if stat == boosted else 0.9 if stat == reduced else 1.0
