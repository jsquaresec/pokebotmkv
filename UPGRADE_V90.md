# Upgrade and playtest v90

1. Back up PostgreSQL and verify the backup can be restored before upgrading.
2. Stop old bot/workers before migration. Do not run old and new writers together.
3. Install dependencies with `pip install -r requirements-dev.txt` for testing.
4. Run `python -m pytest -q`; review UTC deprecation warnings separately.
5. Review generated SQL: `alembic upgrade head --sql`.
6. Set a new unpredictable `API_TOKEN` in `.env`. Clients must use
   `Authorization: Bearer <token>`. With no token configured, all non-health API
   routes reject requests. The shared token is operator access, not per-user auth.
7. Run `docker compose run --rm migrator`, then start bot/API/workers.
8. In a private server, test a first catch, inventory change, party protection,
   market sale, auction outbid/refund, and reconnect/restart recovery.

## Migration considerations

The v90 migration targets PostgreSQL constraints produced by the supplied migrations.
It widens Discord IDs and replaces lifetime uniqueness of auction/market Pokémon IDs
with uniqueness for active records. Review custom schemas or prior `create_all`-created
databases separately; constraint names may differ. Automatic downgrade is intentionally
blocked because relisting history can no longer fit the old unique constraints.

The earlier v70 inventory uniqueness migration can fail if the old database contains
duplicate inventory rows. Reconcile such rows using a reviewed backup and explicit
maintenance procedure; do not blindly drop records.

## Release boundaries

No Discord login, public deployment, real PostgreSQL migration execution, or concurrent
load test was performed in this build environment. The health endpoint reports process
availability, not database/Redis health. Existing game data and balance still require
private playtesting. Traits and moveset metadata are not all applied by the battle engine.
