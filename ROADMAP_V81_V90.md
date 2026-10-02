# v81–v90: reliability release pathway

This is one consolidated v90 release, not ten separately deployed builds.

| Version | Implemented scope | Acceptance check |
|---|---|---|
| v81 | First-catch counter initialization, configured encounter TTL, trainer-row lock | Full catch transaction persists Pokémon, consumes ball, updates dex |
| v82 | Own-bid raises account for reserved coins; missing-winner settlement guard | A 900→950 bid with 100 available leaves 50 |
| v83 | Historical market/auction relisting; active-only unique indexes | Cancel, relist, buy, reject repeat buy |
| v84 | Party-member transfer/listing rejection; validate party before clearing; reject self/invalid trades | Party-member listing rejected without locking asset |
| v85 | Bench owner propagation; replacement cannot execute fainted Pokémon's pending attack | Deterministic replacement regression |
| v86 | Reject Rare Candy at level 100 and Ether when no PP is missing | Inventory preserved on rejected item action |
| v87 | Database-side IV filtering and page-based collection search | Page 11 reaches records beyond previous 200-row cap |
| v88 | Bearer-authenticated API; debug cog isolation; 64-bit Discord IDs; container import path | Model/schema inspection, API auth regression, migration SQL generation |
| v89 | Legacy scripts collected by pytest plus real async SQLite integration tests | Single pytest invocation runs both suites |
| v90 | Release runbook, CI, versioned status, honest verification boundaries | Offline migration, command loading, archive validation |

## Deliberately deferred

Full canonical species/move data, a complete type chart, functional ability effects,
nature effects in combat, PP consumption in ranked combat, true shared wild/PvP
battle logic, comprehensive distributed locking, complete bilateral trade confirmation,
and production-scale testing remain unfinished. Earlier version labels did not establish
those capabilities. Current regional name coverage must not be presented as fully
implemented canonical Pokémon content.

SQLite integration tests exercise persistence and sequential transaction behavior.
They do not prove PostgreSQL row-lock behavior under concurrent traffic. Migration
SQL generation also does not prove the migration succeeds against your existing database.
