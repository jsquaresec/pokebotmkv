# PokeBot v66–v70 changelog

## v66 — Stabilization

- Added standard pytest and Ruff configuration.
- Added development requirements and repository ignore rules.
- Made Alembic migrations authoritative in production.
- Added environment gates for debug and preview extensions.
- Connected previously unloaded production cogs.
- Repaired inherited cooldown, battle-rule, and party compatibility issues.

## v67 — Persistent encounters

- Added `wild_encounters` persistence and migration.
- Added activity-triggered channel encounters.
- Added encounter inspection, weakening, ball selection, and catch commands.
- Added HP-sensitive catch probability and four ball modifiers.
- Added inventory consumption, expiry, row locking, IVs, and shiny rolls.

## v68 — Content and progression

- Added an aggregated ten-region registry containing 1,025 unique species names.
- Added typed canonical metadata with safe fallbacks for incomplete records.
- Added learnset validation and move lookup.
- Added persistent dex number, form, typing, XP, IV, and lock fields.
- Added cubic XP leveling and level-based evolution readiness.

## v69 — Unified battles

- Kept wild/PvP combat centered on shared battle state.
- Added Pokémon typing and stat-stage state.
- Added accuracy, STAB, type effectiveness, immunities, critical hits, and damage variance.
- Added paralysis turn loss and six-stage stat bounds.
- Preserved party switching, forced replacement, status damage, and replay-compatible logs.

## v70 — Transactional economy

- Added persistent global Pokémon market listings.
- Added species and maximum-price search with stable ordering.
- Added listing escrow locks, listing fees, sale fees, cancellation, and atomic purchases.
- Added recipient-only trade acceptance and atomic item, coin, or Pokémon settlement.
- Added inventory uniqueness protection and row-level concurrency controls.
- Added migration-gated Docker startup and expanded deployment documentation.
