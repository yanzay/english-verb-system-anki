"""Re-package an existing .apkg through the official `anki` library to
produce a *modern-format* .apkg whose deck-config preset auto-binds on import.

Why this exists
---------------
genanki produces legacy v11-schema .apkg files. Even when we hand-inject a
deck_config row and bind decks to it, Anki's importer (per the Rust gather.rs
logic) silently rewrites every imported deck's config_id back to 1 (Default)
unless the package was exported through the official Anki backend with
`with_deck_configs=true`.

Pipeline:
  1. Read the existing .apkg into a fresh, in-memory anki.Collection.
  2. Verify our preset is present, normalize it to FSRS + retention 0.9 + …
  3. Bind every non-Default deck to that preset using the proper backend API
     (set_config_id_for_deck_dict) so the modern Deck.Normal proto carries it.
  4. Re-export with `with_deck_configs=true` and `legacy=false` (modern format
     with `meta` + `collection.anki21b` zstd payload).

Result: a .apkg that auto-binds the preset on import in Anki 23.10+.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

PRESET_ID = 1700000000001
PRESET_NAME = 'English Verb System'
PRESET_DEF = {
    'name': PRESET_NAME,
    'fsrs': True,
    'desiredRetention': 0.9,
    'maxTaken': 60,
    'autoplay': True,
    'timer': 0,
    'replayq': True,
    'new': {
        'bury': True,
        'delays': [1.0, 10.0],
        'initialFactor': 2500,
        'ints': [1, 4, 0],
        'order': 1,
        'perDay': 10,
        'separate': True,
    },
    'rev': {
        'bury': True,
        'ease4': 1.3,
        'ivlFct': 1.0,
        'maxIvl': 365,
        'perDay': 150,
        'hardFactor': 1.2,
    },
    'lapse': {
        'delays': [10.0],
        'leechAction': 0,
        'leechFails': 8,
        'minInt': 1,
        'mult': 0.0,
    },
    'dyn': False,
    'fsrsParams5': [],
    'fsrsWeightSearch': '',
}


def repackage(in_apkg: Path, out_apkg: Path) -> int:
    """Repackage in_apkg → out_apkg with proper preset binding.

    Returns 0 on success, non-zero on failure.
    """
    from anki.collection import Collection
    from anki.import_export_pb2 import (
        ExportAnkiPackageOptions,
        ExportLimit,
        ImportAnkiPackageOptions,
        ImportAnkiPackageRequest,
    )

    in_apkg = Path(in_apkg).resolve()
    out_apkg = Path(out_apkg).resolve()
    if not in_apkg.exists():
        print(f'✗ input .apkg not found: {in_apkg}')
        return 2

    workdir = Path(tempfile.mkdtemp(prefix='rovo_repack_'))
    col_path = workdir / 'collection.anki2'
    print(f'  [repack] workdir: {workdir}')
    print(f'  [repack] reading: {in_apkg.name} ({in_apkg.stat().st_size:,} bytes)')

    col = Collection(str(col_path))
    try:
        # 1. Import the legacy .apkg into our fresh collection.
        # with_deck_configs=True so any embedded preset comes along —
        # though for genanki output we'll re-create it ourselves anyway.
        import_opts = ImportAnkiPackageOptions(
            with_scheduling=False,
            with_deck_configs=True,
        )
        col.import_anki_package(
            ImportAnkiPackageRequest(
                package_path=str(in_apkg),
                options=import_opts,
            )
        )

        all_decks = list(col.decks.all_names_and_ids())
        all_configs = list(col.decks.all_config())
        print(f'  [repack] imported: {len(all_decks)} decks, '
              f'{len(all_configs)} deck-configs')

        # 2. Ensure our canonical preset exists and is up to date.
        preset_id = _ensure_preset(col)
        print(f'  [repack] preset id: {preset_id}  name: {PRESET_NAME!r}')

        # 3. Bind every non-default deck to the preset using the proper
        #    backend API so the binding lives in Deck.Normal.config_id
        #    (the one Anki actually reads on import).
        bound = 0
        for d in all_decks:
            if d.id == 1:  # skip Default deck
                continue
            deck = col.decks.get(d.id)
            if deck is None or deck.get('dyn'):  # skip filtered decks
                continue
            col.decks.set_config_id_for_deck_dict(deck, preset_id)
            col.decks.save(deck)
            bound += 1
        print(f'  [repack] bound {bound} decks to preset {preset_id}')

        col.save()

        # 4. Export with the modern format AND with_deck_configs=true so
        #    the importing collection auto-creates the preset and binds
        #    every deck to it. legacy=false → meta + collection.anki21b.
        export_opts = ExportAnkiPackageOptions(
            with_scheduling=False,
            with_deck_configs=True,
            with_media=True,
            legacy=False,
        )
        # Whole-collection export so all decks + configs go through.
        from anki.generic_pb2 import Empty
        limit = ExportLimit(whole_collection=Empty())

        n = col.export_anki_package(
            out_path=str(out_apkg),
            options=export_opts,
            limit=limit,
        )
        print(f'  [repack] exported {n} notes → {out_apkg.name} '
              f'({out_apkg.stat().st_size:,} bytes)')
        return 0
    finally:
        col.close()


def _ensure_preset(col) -> int:
    """Make sure our canonical preset exists in the collection.

    If a preset with our name already exists (re-running, or it came across
    via the import), update its content. Otherwise create a new one.
    Returns the preset id.
    """
    # Find existing by name
    existing = next(
        (c for c in col.decks.all_config() if c.get('name') == PRESET_NAME),
        None,
    )
    if existing:
        # Update in-place with our canonical definition (preserving id).
        existing.update({k: v for k, v in PRESET_DEF.items() if k != 'name'})
        col.decks.update_config(existing)
        return int(existing['id'])

    # Create new
    new = dict(PRESET_DEF)
    new_id = col.decks.add_config_returning_id(PRESET_NAME)
    full = col.decks.get_config(new_id)
    full.update({k: v for k, v in PRESET_DEF.items() if k != 'name'})
    col.decks.update_config(full)
    return int(new_id)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    p.add_argument('input', nargs='?', default='english_verb_system_anki.apkg',
                   help='input .apkg (default: english_verb_system_anki.apkg)')
    p.add_argument('-o', '--output', default=None,
                   help='output .apkg (default: overwrite input)')
    args = p.parse_args()
    in_apkg = Path(args.input)
    out_apkg = Path(args.output) if args.output else in_apkg
    return repackage(in_apkg, out_apkg)


if __name__ == '__main__':
    sys.exit(main())
