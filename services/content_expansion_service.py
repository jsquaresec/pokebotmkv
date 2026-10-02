import random
POOL = ["Pidgey","Rattata","Pikachu","Bulbasaur","Charmander","Squirtle","Mew"]
class ContentExpansionService:
    def get_random(self):
        return random.choice(POOL)
