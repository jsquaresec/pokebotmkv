import random
from services.pokemon_content_registry_service import PokemonContentRegistryService

class PokemonVariationService:
    def __init__(self):
        self.registry = PokemonContentRegistryService()

    def build_display_name(
        self,
        species: str,
        form: str | None = None,
        shiny: bool = False,
        alpha: bool = False,
        shadow: bool = False,
        radiant: bool = False,
    ) -> str:
        parts = []
        if shiny:
            parts.append("Shiny")
        if radiant:
            parts.append("Radiant")
        if alpha:
            parts.append("Alpha")
        if shadow:
            parts.append("Shadow")
        parts.append(species)
        if form:
            parts.append(f"({form})")
        return " ".join(parts)

    def random_form(self, species: str) -> str | None:
        forms = self.registry.forms_for(species)
        return random.choice(forms) if forms else None
