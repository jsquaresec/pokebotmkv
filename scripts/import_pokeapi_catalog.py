"""Build the offline catalog from a pinned, locally cached PokeAPI CSV snapshot.

Usage: python scripts/import_pokeapi_catalog.py --cache PATH --revision SHA
The cache must contain data/v2/csv files from that revision of PokeAPI/pokeapi.
No database access or network calls are performed by this script.
"""
import argparse
import csv
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path


def normalize(name):
    name = name.casefold().replace("♀", "f").replace("♂", "m")
    return ''.join(c for c in unicodedata.normalize('NFKD', name) if c.isalnum())


def build(cache, output, revision):
    def rows(name):
        with (cache / f'{name}.csv').open(encoding='utf-8') as stream:
            return list(csv.DictReader(stream))

    def by_id(name):
        return {int(r['id']): r for r in rows(name)}

    def names(name, key):
        return {int(r[key]): r['name'] for r in rows(name) if r['local_language_id'] == '9'}

    species = by_id('pokemon_species')
    species_names = names('pokemon_species_names', 'pokemon_species_id')
    lookup = {normalize(name): sid for sid, name in species_names.items()}
    roster = list(dict.fromkeys(n for path in sorted(output.glob('pokemon_species_*.json'))
                               for n in json.loads(path.read_text(encoding='utf-8'))))
    ids = {name: lookup[normalize(name)] for name in roster}
    local_names = {sid: name for name, sid in ids.items()}
    pokemon = {int(r['species_id']): r for r in rows('pokemon') if r['is_default'] == '1'}
    stats = defaultdict(dict)
    stat_names = {i: r['identifier'].replace('-', '_') for i, r in by_id('stats').items()}
    for row in rows('pokemon_stats'):
        stats[int(row['pokemon_id'])]['base_' + stat_names[int(row['stat_id'])]] = int(row['base_stat'])
    types = {i: r['identifier'] for i, r in by_id('types').items()}
    typings = defaultdict(list)
    for row in sorted(rows('pokemon_types'), key=lambda r: int(r['slot'])):
        typings[int(row['pokemon_id'])].append(types[int(row['type_id'])])
    ability_names = names('ability_names', 'ability_id')
    abilities = defaultdict(list)
    for row in rows('pokemon_abilities'):
        abilities[int(row['pokemon_id'])].append(dict(name=ability_names[int(row['ability_id'])],
            hidden=row['is_hidden'] == '1', slot=int(row['slot'])))
    growths = {i: r['identifier'] for i, r in by_id('growth_rates').items()}
    move_names = names('move_names', 'move_id')
    meta = {int(r['move_id']): {k: int(v) if v else None for k, v in r.items() if k != 'move_id'}
            for r in rows('move_meta')}
    changes = defaultdict(list)
    for row in rows('move_meta_stat_changes'):
        changes[int(row['move_id'])].append(dict(stat=stat_names[int(row['stat_id'])], change=int(row['change'])))
    descriptions = {int(r['move_effect_id']): r['short_effect'] for r in rows('move_effect_prose') if r['local_language_id'] == '9'}
    targets = {i: r['identifier'] for i, r in by_id('move_targets').items()}
    moves = []
    # Reviewed effect IDs handled by WildTurnEngine (all others stay catalog-only).
    safe_ids = {1, 2, 3, 4, 5, 6, 7, 11, 12, 14, 17, 18, 19, 20, 21, 24, 25,
                26, 30, 32, 33, 41, 42, 44, 45, 49, 51, 52, 53, 54, 55,
                59, 60, 61, 62, 63, 67, 68, 69, 70, 71, 72, 73, 74, 78, 79,
                77, 86, 88, 89, 90, 92, 100, 104, 141, 145, 150, 154, 157, 199, 207, 357, 372, 381}
    for mid, row in by_id('moves').items():
        effect_id = int(row['effect_id'] or 0)
        moves.append(dict(id=mid, name=move_names.get(mid, row['identifier'].replace('-', ' ').title()),
            type=types[int(row['type_id'])], power=int(row['power'] or 0), pp=int(row['pp'] or 1),
            accuracy=int(row['accuracy']) if row['accuracy'] else None, priority=int(row['priority']),
            category={1:'status', 2:'physical', 3:'special'}[int(row['damage_class_id'])],
            target=targets[int(row['target_id'])], effect=None, effect_id=effect_id,
            effect_chance=int(row['effect_chance'] or 0), description=descriptions.get(effect_id, ''),
            meta=meta.get(mid, {}), stat_changes=changes[mid],
            battle_supported=effect_id in safe_ids))
    version_groups = by_id('version_groups')
    # Main-series turn-based learnsets through Scarlet/Violet DLC; prefer latest
    # available for each species, excluding Legends' different battle rules.
    allowed = set(range(1, 24)) | {25, 26, 27}
    candidates = defaultdict(lambda: defaultdict(list))
    for row in rows('pokemon_moves'):
        vg = int(row['version_group_id'])
        if row['pokemon_move_method_id'] == '1' and vg in allowed:
            candidates[int(row['pokemon_id'])][vg].append((max(1, int(row['level'])), int(row['move_id'])))
    evolutions = defaultdict(list)
    triggers = {i: r['identifier'] for i, r in by_id('evolution_triggers').items()}
    item_names = names('item_names', 'item_id')
    for row in rows('pokemon_evolution'):
        target = int(row['evolved_species_id'])
        parent = species[target]['evolves_from_species_id']
        if not parent or target not in local_names or row['is_default'] != '1':
            continue
        conditions = {k: v for k, v in row.items() if v != '' and (v != '0' or k == 'relative_physical_stats') and k not in
            ('id', 'evolved_species_id', 'evolution_trigger_id', 'version_group_id', 'is_default')}
        evolutions[int(parent)].append(dict(target=local_names[target], trigger=triggers[int(row['evolution_trigger_id'])],
            conditions=conditions, item=item_names.get(int(row['trigger_item_id'] or 0))))
    records, learnsets, legacy = [], {}, {}
    for name, sid in sorted(ids.items(), key=lambda pair: pair[1]):
        s = species[sid]; p = pokemon[sid]; pid = int(p['id'])
        versions = candidates[pid]
        if not versions:
            raise ValueError(f'No level-up learnset for {name}')
        vg = max(versions, key=lambda v: int(version_groups[v]['order']))
        earliest = {}
        for level, mid in versions[vg]:
            earliest[mid] = min(level, earliest.get(mid, 101))
        learnsets[name] = [dict(move=move_names[mid], level=level) for mid, level in sorted(earliest.items(), key=lambda pair:(pair[1],pair[0]))]
        legacy[name] = {}
        for entry in learnsets[name]:
            legacy[name].setdefault(str(entry['level']), []).append(entry['move'])
        r = dict(name=name, dex_number=sid, pokemon_id=pid, **stats[pid], types=typings[pid],
            catch_rate=int(s['capture_rate']), growth_rate=growths[int(s['growth_rate_id'])],
            gender_rate=int(s['gender_rate']), base_happiness=int(s['base_happiness']),
            abilities=abilities[pid], is_legendary=s['is_legendary']=='1', is_mythical=s['is_mythical']=='1',
            height=int(p['height']), weight=int(p['weight']), base_experience=int(p['base_experience'] or 0),
            evolves_from=local_names.get(int(s['evolves_from_species_id'] or 0)), evolutions=evolutions[sid],
            learnset_version=version_groups[vg]['identifier'])
        r['rarity'] = 'legendary' if r['is_legendary'] or r['is_mythical'] else 'rare' if r['catch_rate'] <= 45 else 'common'
        simple = [e for e in r['evolutions'] if e['trigger'] == 'level-up' and set(e['conditions']) == {'minimum_level'}]
        if len(r['evolutions']) == 1 and len(simple) == 1:
            r.update(evolves_to=simple[0]['target'], evolution_level=int(simple[0]['conditions']['minimum_level']))
        records.append(r)
    outputs = {'species.json':records, 'moves.json':moves, 'species_moves.json':learnsets, 'level_up_moves.json':legacy}
    for filename, value in outputs.items():
        (output/filename).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    manifest = dict(source='https://github.com/PokeAPI/pokeapi', revision=revision,
        species=len(records), moves=len(moves), learnset_policy='Latest available main-series level-up learnset through Scarlet/Violet DLC',
        files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in outputs})
    manifest['source_files'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(cache.glob('*.csv'))}
    (output/'catalog_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'data')
    args=parser.parse_args()
    build(args.cache,args.output,args.revision)
