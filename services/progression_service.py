class ProgressionService:
    def xp_to_next_level(self, level: int) -> int:
        return max(10, level * 20)

    def apply_xp(self, pokemon, gained_xp: int) -> tuple[int, bool]:
        # lightweight placeholder progression
        threshold = self.xp_to_next_level(pokemon.level)
        leveled = False
        if gained_xp >= threshold:
            pokemon.level += 1
            pokemon.max_hp += 2
            pokemon.current_hp = min(pokemon.max_hp, pokemon.current_hp + 2)
            pokemon.attack += 1
            pokemon.defense += 1
            pokemon.speed += 1
            leveled = True
        return pokemon.level, leveled
