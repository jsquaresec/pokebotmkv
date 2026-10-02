# PokeBot v90 — reliability and integration release

## Discord graphical dashboard

Run `/menu` to open the Adventure Hub. Category buttons cover Trainer,
Pokémon & Party, Catching, Shop & Trading, Battles & Ranked, Daily & Seasons,
Friends & Guilds, World & Events, and Help & Status. Optional admin and preview
features appear only when loaded and are administrator-only in the dashboard.

Every player gets a **private GUI panel per channel**. Menu navigation, PC pages,
shop choices, purchases, party saves, Pokémon Center receipts, and wild battle
turns update that panel instead of posting a new message for every action.
Opening another slash command reuses the existing panel while its interaction
token is valid. Other players cannot see or operate it. Panels reported by Discord
as expired or missing are replaced privately; use `/menu` after a restart or timeout.
Only the shared spawn invitation is posted publicly. **Open private encounter**
opens that player's battle controls; the first trainer to start still reserves
the shared encounter. Public invitations never display trainer balances or party HP.
Use **Home** to return to the dashboard; an unfinished wild battle can be resumed
with `/encounter` until it expires.

Every loaded slash command opens without typed parameters. Actions needing inputs
open a button flow in both slash commands and the dashboard. Pokémon, players,
market listings, auctions, trades, friend requests, battles, guilds, and unlocked
season rewards are selected from records. Numbers and dates offer presets;
Custom opens a single text field for names, bios, or another amount/date.
Back, Cancel, Previous, and Next support navigation. A review screen shows the
choices before Run Action calls the original handler and rechecks permissions.
Existing dedicated party, catching, and shop buttons remain available.
Results appear as cards with Home
navigation, and long text results have Previous/Next pages. Menus are private
to their opener and expire after five minutes; choice menus expire after three.
Slash commands remain available and now use the same result cards.

The bot needs **Embed Links** alongside View Channel and Send Messages.
After updating, run `docker compose up -d --build bot`, then `/menu`.

### Party builder

Use `/pokemon_center` or Menu → Pokémon & Party → Pokémon Center, then click
**Heal party — 500 gold** to revive and fully restore HP and move PP for your
entire party. The price is per visit, not per Pokémon; the receipt shows your
remaining gold. Empty or fully restored parties are not charged. Healing is
unavailable during battles or while queued for ranked play.

Open `/party_set` or Menu → Pokémon & Party → Party Set. Click Pokémon to toggle
up to six teammates; selection order determines slot order. Your current party
is preselected. Previous/Next browse the collection, Clear Selection resets the
draft, Cancel leaves the saved party unchanged, and Save Party applies the whole
selection together. Locked Pokémon are excluded and availability is rechecked
when saving. Saving an empty selection clears the party.

Consolidated v81–v90 development release based on v80. See `ROADMAP_V81_V90.md`
for each milestone and `UPGRADE_V90.md` before installing over an existing database.

## Main improvements

### Complete species catalog

All 1,025 distinct species in the region lists now have explicit national Pokédex
IDs, six base stats, types, catch rates, growth-rate metadata, gender ratios,
species-specific normal/hidden abilities, evolution conditions, and level-up
learnsets. Duplicate names across regions still represent their default species
form; this update does not add separate regional or Mega forms to the spawn pool.
Art uses the default Pokémon form's correct artwork ID. Yamper is #835, Electric,
has Ball Fetch, learns Nuzzle at level 5, and can evolve into Boltund at level 25.

The catalog includes 937 move records with PP, accuracy, priority, damage category,
and effect metadata. Learnsets use the newest available main-series data through
Scarlet/Violet DLC for each species (Sword/Shield for Yamper). The complete
learnset is stored even when a move's special mechanic is not implemented.
Move buttons and move-learning menus offer reviewed, supported effects only;
unsupported stored moves are disabled in wild battles. A Pokémon with no usable
move can use Struggle. This prevents an unsupported move from silently acting
like Tackle. Generic damage, status, stat changes, recovery, recoil, drain,
multi-hit moves, and several special effects use the expanded catalog.

Ordinary, unconditional level evolutions work with `/pokemon_evolve` and update
stats, types, artwork, and ability. The info card identifies special evolution
methods that remain unavailable. Growth rates and hidden abilities are cataloged;
XP/stat scaling still uses the bot's simplified progression rules. Ability effects,
held-item effects, weather, and remaining special move/evolution mechanics are not
a full official-game simulation.

`docker compose up -d --build bot` applies the catalog revision migration. Startup
upgrades existing unlocked Pokémon once, correcting fallback stats/types/abilities
and moves while preserving their HP ratio, fainting, and spent PP. Active wild
battle parties are deferred until the battle finishes or expires. New Pokémon
receive the configured data immediately. No network requests are needed at runtime
for species or move data.

Source: [PokéAPI dataset](https://github.com/PokeAPI/pokeapi/tree/168b1e89467054cda2e7df43ccebbb69b459497a/data/v2/csv).
`data/catalog_manifest.json` records the pinned source revision and file checksums.
To reproduce the generated files, cache that revision's CSV files named in the
manifest and run `python scripts/import_pokeapi_catalog.py --cache PATH --revision SHA`.
The importer only reads that cache and writes catalog JSON; it never accesses the database.

### Earlier improvements

- Fixed first-catch persistence and bid-reserve accounting.
- Allowed historical relisting while protecting active listings.
- Prevented party Pokémon from being transferred or listed.
- Fixed replacement-turn behavior and bench ownership in battles.
- Added item-cap validation and database-side collection pagination.
- Added operator bearer authentication to the API and isolated debug commands.
- Widened Discord IDs to 64 bits and repaired container import configuration.
- Added database-backed regressions and collected legacy scripts under pytest.

## Test locally

### Wild Pokémon spawns

Use `/spawn` with Manage Server permission to spawn a catchable Pokémon immediately.
Automatic spawns also happen after 20 non-bot messages in a server channel; configure
this with `SPAWN_MESSAGE_THRESHOLD`. Only one encounter can be active per channel.
Wild levels are within **2 levels of the triggering trainer's first party Pokémon**,
bounded to levels 1–100. For example, a level-25 leader produces level-23–27 spawns.
Manual `/spawn` uses the caller's party; automatic spawns use the author of the
message that reaches the activity threshold. Party order determines the leader,
even if it has fainted. Trainers without a party use level 5 as the baseline
(level-3–7 spawns). Levels and HP are fixed when the spawn appears, so another
trainer joining or changing their party does not reroll an existing encounter.
Encounters expire after `ENCOUNTER_TTL_SECONDS` (default: 300 seconds).
The bot needs View Channel and Send Messages permissions. Restart the bot after
updating to sync the new command with Discord.

Players use `/start`, choose a starter, and set a party with `/party_set`.
Click **Open private encounter** on a spawn, then **Battle**, to send out the first healthy party Pokémon.
`/encounter`, `/wild_attack`, and `/throw` open the active encounter controls.
`/spawn_preview` is only a display preview and does not create a catchable encounter.

The first trainer to start reserves the encounter. Move buttons show learned moves,
types, and remaining PP. Both Pokémon take turns, ordered by move priority and
Speed, with accuracy, type effectiveness, STAB, critical hits, and supported status
effects. You can switch teammates, throw an inventory ball, or Run. Failed catches
and voluntary switches let the wild Pokémon attack. A fainted teammate must be
replaced; defeating the wild Pokémon awards Pokémon XP and **250 gold**, while catching awards
500 gold. Fainted wild Pokémon cannot be caught.

Party HP and PP persist, and the party is locked during the encounter. Catching,
winning, losing, running, or expiry releases it. `/encounter` restores controls
after a restart; old controls cannot spend balls on another spawn or replay a turn.
Rebuilding with Docker Compose applies the additive wild-battle database migration.

This is a game-style subset using the bot's move catalog and simplified stats,
not a complete simulation of the official games. Abilities, held-item effects,
and weather are not implemented here. Running always succeeds and status effects
are scoped to the encounter. Use `/move_learn` to change an existing moveset;
new elemental moves do not overwrite Pokémon's existing learned moves.

The catching GUI is a Discord embed with Pokémon artwork, a colored health bar,
live per-ball catch odds, expiry countdown, and reward display. Each turn updates
the card; catching replaces it with a result card. The bot needs Embed Links
permission in the channel. Artwork is hosted by https://github.com/PokeAPI/sprites;
the health, odds, and buttons work even if an image cannot load.
Encounter button actions edit that same card, including breakouts and missing-ball
errors, without posting follow-up messages. `/throw` opens the encounter GUI too.

Weakening now gives a stronger catch bonus: the HP multiplier rises linearly from
0.35 at full HP to nearly 2 at 1 HP on a high-HP Pokémon. Species catch rate,
ball strength, and status bonuses still apply. Ordinary catches are capped at
95%; Master Balls remain guaranteed.

### Button selection menus

`/shop` and `/buy` open item buttons, followed by quantity buttons showing the
total price. Clicking a quantity completes the purchase (1, 5, 10, or 25 items).
`/throw`, `/choose_starter`, `/region_pool`, and `/battle_move` open choice buttons.
`/item_use` and `/move_learn` offer Pokémon buttons, then item or move buttons;
full movesets also show buttons for the move to replace. `/trade_offer` shows
offered/requested item buttons, and `/pokemon_search` shows shiny/favorite filters.
Mission choices and the optional battle tier preview also use buttons.

Menus belong to the player who opened them. Dedicated choice menus expire after
three minutes; the general input flow expires after five. Longer lists have
Previous/Next buttons. Free text is entered through Custom, and record IDs do
not need to be typed. Rebuild and restart the
bot to register the updated command signatures:

```sh
docker compose up -d --build bot
```

### Run tests

```sh
pip install -r requirements-dev.txt
python -m pytest -q
alembic upgrade head --sql
```

Copy `.env.example` to `.env`, configure credentials and an unpredictable `API_TOKEN`,
then follow the upgrade runbook. Never commit credentials. Use a private test server first.

## Important limitations

This is not a verified production deployment or P2-equivalent release. The roster contains
1,025 names but only a small subset has detailed data. Ability/nature metadata and PP slots
are not fully integrated into combat. Wild attacks are still simplified, and multiplayer
concurrency requires PostgreSQL load testing. Existing progression/economy balancing and
several older preview systems require further work. Read the roadmap's deferred list.

The SQLite tests verify sequential database behavior, not PostgreSQL locking semantics.
Offline migration generation validates SQL construction, not execution on your live data.
No bot token was used and no external deployment was performed.
