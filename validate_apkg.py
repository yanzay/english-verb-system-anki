#!/usr/bin/env python3
"""Post-build validator for english_verb_system_anki.apkg.

Round-trips the built .apkg through its embedded SQLite collection and asserts
package-integrity invariants that would otherwise only surface as cryptic
"500: note has N fields, expected M" errors during Anki import.

Checks (all hard failures, exit code 1):

  M1. Every model id is unique. (collisions cause notes to be validated
      against the WRONG model's field count.)
  M2. Every note's flds count == its model's declared field count.
  M3. Every note's model id (mid) refers to an existing model.
  M4. Every card's deck id (did) refers to an existing deck.
  M5. Every card's note id (nid) refers to an existing note.
  M6. No two models share a name (warning only — Anki dedupes on import,
      but it's almost always a bug).

Soft checks (warnings, exit code 0):

  S1. FSRS preset 'English Verb System' is present in col.dconf.
  S2. Every non-default deck has its `conf` pointing at the FSRS preset.
  S3. media_files referenced from notes (sound:..., img src=...) all
      resolve to a file in the .apkg's media map.

Usage:
    python3 validate_apkg.py [path/to/file.apkg]

Exit codes:
    0  all hard checks passed (warnings allowed)
    1  one or more hard checks failed
    2  could not read the .apkg (corrupt zip / no collection.anki2)
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

DEFAULT_APKG = "english_verb_system_anki.apkg"
ANKI_FIELD_SEP = "\x1f"


def _open_collection(apkg_path: str):
    """Yield (sqlite_conn, media_map, tmpdir_path). media_map: {basename → arc-name}."""
    tmpdir = tempfile.mkdtemp(prefix="apkg-validate-")
    with zipfile.ZipFile(apkg_path, "r") as zf:
        zf.extractall(tmpdir)
    db_path = None
    # Modern .apkg (Anki 23.10+) ships collection.anki21b (zstd-compressed)
    # alongside a legacy collection.anki2 stub. We must use the modern db.
    anki21b_path = Path(tmpdir) / 'collection.anki21b'
    if anki21b_path.exists():
        try:
            import zstandard as zstd  # type: ignore
            decompressed = Path(tmpdir) / 'collection.anki21'
            with anki21b_path.open('rb') as src, decompressed.open('wb') as dst:
                zstd.ZstdDecompressor().copy_stream(src, dst)
        except Exception as _e:
            print(f"  warn: could not decompress collection.anki21b: {_e}")
    for name in ("collection.anki21", "collection.anki2"):
        p = os.path.join(tmpdir, name)
        if os.path.exists(p):
            db_path = p
            break
    if db_path is None:
        print(f"  ERROR: no collection.anki21 or collection.anki2 in {apkg_path}",
              file=sys.stderr)
        sys.exit(2)
    media_index_path = os.path.join(tmpdir, "media")
    media_map: dict[str, str] = {}
    if os.path.exists(media_index_path):
        # Legacy: JSON {arc-number → original-filename}
        try:
            media_map = json.load(open(media_index_path, encoding="utf-8"))
        except Exception:
            # Modern (Anki 23.10+): zstd-compressed protobuf MediaEntries.
            try:
                import zstandard as zstd  # type: ignore
                from anki.import_export_pb2 import MediaEntries  # type: ignore
                import io as _io
                raw = anki21b_path.parent.joinpath('media').read_bytes()
                buf = _io.BytesIO()
                zstd.ZstdDecompressor().copy_stream(_io.BytesIO(raw), buf)
                entries = MediaEntries.FromString(buf.getvalue())
                # Map: arc-name (numeric str of index) → original filename
                for i, e in enumerate(entries.entries):
                    media_map[str(i)] = e.name
            except Exception:
                pass
    conn = sqlite3.connect(db_path)
    return conn, media_map, tmpdir


def validate(apkg_path: str = DEFAULT_APKG) -> int:
    if not os.path.exists(apkg_path):
        print(f"  ERROR: {apkg_path} does not exist", file=sys.stderr)
        return 2

    print(f"Validating {apkg_path} …")
    conn, media_map, tmpdir = _open_collection(apkg_path)
    cur = conn.cursor()

    # ── Load models & decks (schema-aware: modern v18+ uses dedicated tables;
    #    legacy v11 stores everything as JSON in `col`) ───────────────────
    tables = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    models: dict[str, dict] = {}
    decks: dict[str, dict] = {}
    dconf: dict[str, dict] = {}
    if 'notetypes' in tables and 'fields' in tables:
        # Modern schema (Anki 23.10+)
        for mid, name in cur.execute("SELECT id, name FROM notetypes"):
            models[str(mid)] = {'name': name, 'flds': []}
        for ntid, ord_, name in cur.execute(
            "SELECT ntid, ord, name FROM fields ORDER BY ntid, ord"
        ):
            ntid_str = str(ntid)
            if ntid_str in models:
                models[ntid_str]['flds'].append({'name': name, 'ord': ord_})
        # Modern decks store the kind (Normal/Filtered + config_id) as a
        # protobuf BLOB. We decode the inner Normal.config_id (field 1)
        # manually to avoid pulling in the full anki proto.
        def _decode_config_id(blob: bytes) -> int | None:
            """Outer Deck.kind: field 1 (Normal) length-delimited.
            Inside Normal: field 1 (config_id) varint."""
            if not blob or blob[0] != 0x0a:  # field 1, wire type 2 (length-delimited)
                return None
            # length varint
            i = 1
            length = 0
            shift = 0
            while i < len(blob):
                b = blob[i]; i += 1
                length |= (b & 0x7f) << shift
                if not (b & 0x80): break
                shift += 7
            normal = blob[i:i+length]
            if not normal or normal[0] != 0x08:  # field 1, varint
                return None
            j = 1; cid = 0; shift = 0
            while j < len(normal):
                b = normal[j]; j += 1
                cid |= (b & 0x7f) << shift
                if not (b & 0x80): break
                shift += 7
            return cid

        for did, name, kind in cur.execute("SELECT id, name, kind FROM decks"):
            cid = _decode_config_id(kind) if kind else None
            decks[str(did)] = {'name': name, 'dyn': 0, 'conf': cid}
        if 'deck_config' in tables:
            for dcid, name in cur.execute("SELECT id, name FROM deck_config"):
                dconf[str(dcid)] = {'name': name}
    else:
        # Legacy schema
        raw_models = cur.execute("SELECT models FROM col").fetchone()[0]
        raw_decks = cur.execute("SELECT decks FROM col").fetchone()[0]
        raw_dconf = cur.execute("SELECT dconf FROM col").fetchone()[0]
        models = json.loads(raw_models) if raw_models else {}
        decks = json.loads(raw_decks) if raw_decks else {}
        dconf = json.loads(raw_dconf) if raw_dconf else {}

    errors: list[str] = []
    warnings: list[str] = []

    # ── M1: model id uniqueness ─────────────────────────────────────────
    # Models dict is keyed by id-string already, but Anki internally also
    # keys notes by `mid`. The SQLite key is the source of truth; if any
    # int collision sneaks in via genanki, we catch it here.
    mid_to_name: dict[int, list[str]] = defaultdict(list)
    for mid_str, mdef in models.items():
        try:
            mid = int(mid_str)
        except ValueError:
            errors.append(f"M1: non-integer model id {mid_str!r}")
            continue
        mid_to_name[mid].append(mdef.get("name", "<no-name>"))
    for mid, names in mid_to_name.items():
        if len(names) > 1:
            errors.append(f"M1: model id {mid} used by {len(names)} models: {names}")

    # ── M6: model name uniqueness (warning) ──────────────────────────────
    name_to_mids: dict[str, list[int]] = defaultdict(list)
    for mid_str, mdef in models.items():
        name_to_mids[mdef.get("name", "")].append(int(mid_str))
    for name, mids in name_to_mids.items():
        if len(mids) > 1:
            warnings.append(f"M6: model name {name!r} used by ids {mids}")

    # ── M2 + M3: per-note field-count + model existence ─────────────────
    note_count = 0
    notes_by_model: dict[int, int] = defaultdict(int)
    field_mismatches: list[tuple[int, int, int, int]] = []  # (nid, mid, got, expected)
    bad_mids: dict[int, int] = defaultdict(int)             # mid → notes referencing it
    note_ids: set[int] = set()
    for nid, mid, fldstr in cur.execute("SELECT id, mid, flds FROM notes"):
        note_count += 1
        note_ids.add(nid)
        notes_by_model[mid] += 1
        m_str = str(mid)
        if m_str not in models:
            bad_mids[mid] += 1
            continue
        expected = len(models[m_str].get("flds", []))
        got = fldstr.count(ANKI_FIELD_SEP) + 1 if fldstr is not None else 0
        if got != expected:
            field_mismatches.append((nid, mid, got, expected))
    if bad_mids:
        for mid, n in bad_mids.items():
            errors.append(f"M3: {n} note(s) reference non-existent model id {mid}")
    if field_mismatches:
        # Bucket by (mid, got, expected) so the report stays short.
        bucket: dict[tuple, int] = defaultdict(int)
        for _nid, mid, got, expected in field_mismatches:
            bucket[(mid, got, expected)] += 1
        for (mid, got, expected), n in sorted(bucket.items(), key=lambda x: -x[1]):
            mname = models.get(str(mid), {}).get("name", "?")
            errors.append(
                f"M2: {n} note(s) on model {mid} ('{mname}') have {got} fields, "
                f"expected {expected}"
            )

    # ── M4 + M5: card → note + card → deck integrity ────────────────────
    deck_ids = {int(did) for did in decks.keys()}
    bad_card_nids = 0
    bad_card_dids = 0
    card_count = 0
    for nid, did in cur.execute("SELECT nid, did FROM cards"):
        card_count += 1
        if nid not in note_ids:
            bad_card_nids += 1
        if did not in deck_ids:
            bad_card_dids += 1
    if bad_card_nids:
        errors.append(f"M5: {bad_card_nids} card(s) reference a non-existent note id")
    if bad_card_dids:
        errors.append(f"M4: {bad_card_dids} card(s) reference a non-existent deck id")

    # ── S1 + S2: FSRS preset ────────────────────────────────────────────
    fsrs_preset_id = None
    for did_str, ddef in dconf.items():
        if ddef.get("name") == "English Verb System":
            fsrs_preset_id = int(did_str)
            break
    if fsrs_preset_id is None:
        warnings.append(
            "S1: FSRS preset 'English Verb System' not found in col.dconf"
        )
    else:
        unbound = 0
        for did_str, ddef in decks.items():
            if did_str == "1":  # default deck
                continue
            if isinstance(ddef, dict) and ddef.get("dyn", 0) == 0:
                if ddef.get("conf") != fsrs_preset_id:
                    unbound += 1
        if unbound:
            warnings.append(
                f"S2: {unbound} deck(s) not bound to FSRS preset id {fsrs_preset_id}"
            )

    # ── S3: referenced media files exist in package ────────────────────
    referenced: set[str] = set()
    sound_re = re.compile(r"\[sound:([^\]]+)\]")
    img_re = re.compile(r'<img\s+[^>]*src="([^"]+)"')
    for (fldstr,) in cur.execute("SELECT flds FROM notes"):
        if not fldstr:
            continue
        referenced.update(sound_re.findall(fldstr))
        referenced.update(img_re.findall(fldstr))
    # Modern media: media_map values are the original filenames; the
    # archive entries are numeric (0, 1, 2…). Check that the original
    # filename was placed in the archive (i.e. it appears in media_map values).
    available = set(media_map.values())
    missing = sorted(referenced - available)
    if missing:
        warnings.append(
            f"S3: {len(missing)} referenced media file(s) not in package "
            f"(first 5: {missing[:5]})"
        )

    # ── Report ──────────────────────────────────────────────────────────
    print(f"  models: {len(models)}  decks: {len(decks)}  "
          f"notes: {note_count}  cards: {card_count}")
    print(f"  per-model note counts:")
    for mid_str, mdef in models.items():
        n = notes_by_model.get(int(mid_str), 0)
        print(f"    {mid_str}  {mdef.get('name', '?'):50s}  "
              f"fields={len(mdef.get('flds', []))}  notes={n}")

    if warnings:
        print()
        print(f"⚠ {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")

    # cleanup tmpdir best-effort
    try:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass

    if errors:
        print()
        print(f"✗ {len(errors)} hard failure(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print()
    print(f"✓ All hard checks passed.")
    return 0


if __name__ == "__main__":
    apkg_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_APKG
    sys.exit(validate(apkg_path))
