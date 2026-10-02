from datetime import timezone
from functools import lru_cache

import discord

from services.content_registry_v70 import ContentRegistryV70
from services.encounter_v70_service import BALLS, CATCH_GOLD_REWARD, EncounterV70Service


@lru_cache(maxsize=1)
def registry():
    return ContentRegistryV70()


def artwork(embed, species, shiny=False, full_size=False):
    data = registry().species(species)
    if data:
        # Artwork hosted by https://github.com/PokeAPI/sprites.
        variant = "shiny/" if shiny else ""
        url = f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{variant}{data.get("pokemon_id", data["dex_number"])}.png'
        if full_size:
            embed.set_image(url=url)
        else:
            embed.set_thumbnail(url=url)


def encounter_card(row, expired=False):
    ratio = max(0, min(1, row.current_hp / max(1, row.max_hp)))
    filled = max(1 if ratio else 0, round(ratio * 12))
    color = 0x2ECC71 if ratio > 0.5 else 0xF1C40F if ratio > 0.2 else 0xE74C3C
    embed = discord.Embed(title=f"Wild {row.species}", color=0x747F8D if expired else color,
                          description=f'**Level {row.level}** · {getattr(row, "rarity", "common").title()}')
    artwork(embed, row.species)
    embed.add_field(name="Health", value=f'`{"█" * filled}{"░" * (12 - filled)}` **{row.current_hp}/{row.max_hp} HP**', inline=False)
    if expired:
        embed.add_field(name="Controls expired", value="Use /encounter to check for an active Pokémon.", inline=False)
    else:
        service = EncounterV70Service(None, registry=registry())
        labels = ("Poké Ball", "Great Ball", "Ultra Ball", "Master Ball")
        odds = [f'**{label}** {service.catch_probability(row, ball):.0%}' for label, ball in zip(labels, BALLS)]
        embed.add_field(name="Catch chance", value=" · ".join(odds[:2]) + "\n" + " · ".join(odds[2:]), inline=False)
        embed.add_field(name="How to catch", value="**1. Weaken** to improve the odds.\n**2. Choose a ball** below to throw one from your bag.", inline=False)
        expires = getattr(row, "expires_at", None)
        if expires:
            embed.add_field(name="Leaves", value=f'<t:{int(expires.replace(tzinfo=timezone.utc).timestamp())}:R>')
        embed.add_field(name="Catch reward", value=f"🪙 {CATCH_GOLD_REWARD} gold")
    embed.set_footer(text="Everyone can participate • Each ball click uses one ball")
    return embed


def caught_card(mon, user_id):
    embed = discord.Embed(title=f"{mon.species} caught!", color=0x2ECC71,
                          description=f"<@{user_id}> caught this Pokémon!")
    artwork(embed, mon.species)
    embed.add_field(name="Reward", value=f"🪙 +{CATCH_GOLD_REWARD} gold")
    embed.set_footer(text="Encounter complete")
    return embed
