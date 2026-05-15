"""
Build script for English Verb System Anki package.

Produces: english_verb_system_anki.apkg

Input files (new rich-field schema):
  conjugations_recognition.txt — Recognition notes
  conjugations_contrast.txt    — Contrast notes
  conjugations_production.txt  — Production notes

Recognition fields:  Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
Contrast fields:     Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
Production fields:   Prompt | Target | Aspect | Sample | Why | Tags

Deck hierarchy:
  English Verb System
    01 - Core Tense & Aspect :: Recognition / Contrast / Production
    02 - Future Forms        :: Recognition / Contrast / Production
    03 - Conditionals        :: Recognition / Contrast / Production
    04 - Passive Voice       :: Recognition / Contrast / Production
    05 - Stative vs Dynamic  :: Recognition / Contrast / Production

Recommended Anki settings: see ANKI_SETTINGS.md
"""

import csv
import hashlib
import json
import re
import sys
import subprocess
from pathlib import Path

VERSION = '2.0.0'
CHANGELOG_URL = 'https://github.com/yanzay/english-verb-system-anki/blob/main/CHANGELOG.md'


def ensure_genanki():
    try:
        import genanki  # noqa: F401
        return
    except ImportError:
        pass
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                           '--user', '--break-system-packages', 'genanki'])


def load_tsv(path):
    """Parse Anki-format TSV. The header is taken from the `#columns:` directive
    (Anki's own metadata line); all non-comment lines are real data rows."""
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    header = None
    data_lines = []
    for line in lines:
        if line.startswith('#columns:'):
            header = line[len('#columns:'):].split('\t')
        elif line and not line.startswith('#'):
            data_lines.append(line)
    reader = csv.reader(data_lines, delimiter='\t', quotechar='"')
    rows = list(reader)
    if header is None:
        # Legacy fallback: first non-comment row is the header
        header = rows[0] if rows else []
        rows = rows[1:]
    return header, rows


MODULE_TAGS = {
    '02': {'future-going-to', 'present-continuous-future', 'present-simple-schedule',
           'future-will-vs-going-to', 'future-going-to-vs-will',
           'future-going-to-vs-present-continuous',
           'future-present-simple-schedule-vs-present-continuous',
           'future-was-going-to', 'future-about-to', 'future-due-to',
           'future-will-offer', 'future-will-promise',
           'future-was-going-to-vs-going-to', 'future-about-to-vs-going-to',
           'future-will-offer-vs-prediction', 'future-present-simple-vs-will',
           'present-continuous-trend', 'present-continuous-complaint',
           'present-continuous-complaint-vs-trend',
           'future-continuous-polite-enquiry'},
    '03': {'conditional-zero', 'conditional-first', 'conditional-second',
           'conditional-third', 'conditional-mixed',
           'conditional-zero-vs-first', 'conditional-first-vs-second',
           'conditional-second-vs-third', 'conditional-third-vs-mixed',
           'conditional-first-vs-zero',
           'wish', 'if-only', 'inverted-conditional',
           'as-long-as', 'provided-that',
           'wish-vs-conditional', 'inverted-vs-standard',
           'unless-vs-as-long-as'},
    '04': {'passive-present-simple', 'passive-past-simple', 'passive-present-perfect',
           'passive-modal', 'passive-vs-active', 'passive-agent',
           'passive-present-continuous', 'passive-past-continuous',
           'passive-past-perfect', 'passive-get', 'passive-gerund',
           'passive-infinitive', 'passive-dative',
           'passive-be-vs-get', 'passive-get-vs-be',
           'passive-dative-vs-active'},
    '05': {'stative', 'dynamic-stative', 'stative-vs-dynamic'},
    '06': {'reported-speech', 'backshift', 'reported-question', 'reported-command',
           'reported-modal', 'reported-no-backshift', 'backshift-present-to-past',
           'backshift-perfect', 'reported-production'},
    '07': {'time-clause', 'in-case', 'on-condition-that'},
    '08': {'modal', 'modal-deduction', 'modal-obligation', 'modal-permission',
           'modal-perfect', 'modal-ability', 'modal-past-habit', 'modal-production',
           'semi-modal', 'semi-modal-dare', 'semi-modal-need',
           'modal-perfect-continuous', 'shall', 'shall-suggestion',
           'be-to-infinitive', 'habitual-would', 'habitual-used-to',
           'modal-would-rather-vs-sooner'},
    '09': {'subjunctive', 'wish-present', 'wish-past', 'wish-would', 'if-only',
           'would-rather', 'its-time', 'as-if', 'mandative', 'subjunctive-production',
           'high-time', 'wish-annoyance', 'wish-polite-request',
           'as-if-counterfactual'},
    '10': {'non-finite', 'gerund', 'infinitive', 'bare-infinitive',
           'perfect-infinitive', 'perfect-gerund', 'perfect-participle',
           'infinitive-of-purpose',
           'reduced-relative', 'reduced-relative-present-participle',
           'reduced-relative-past-participle', 'raising-verb', 'control-verb'},
    '11': {'phrasal-verb', 'pv-separable', 'pv-inseparable', 'pv-transitive',
           'pv-intransitive', 'pv-three-part', 'pv-figurative', 'pv-literal'},
    '12': {'discourse', 'historical-present', 'politeness', 'hedging', 'headline',
           'recipe', 'cleft', 'emphatic', 'narrative-shift', 'performative',
           'register-formal', 'register-informal',
           'auxiliary-ellipsis', 'tag-question', 'embedded-question',
           'indirect-question', 'negative-inversion', 'comparative-correlative',
           'even-if-vs-even-though', 'narrative-layering', 'cleft-conditional',
           'light-verb', 'ame-vs-bre'},
    '13': {'l1-interference', 'l1-spanish', 'l1-french', 'l1-german',
           'l1-russian', 'l1-mandarin', 'l1-japanese',
           'l1-korean', 'l1-arabic', 'l1-portuguese'},
    '14': {'image', 'module:image', 'image-cue', 'aspect-dynamic',
           'aspect-habitual', 'aspect-perfect', 'phrasal-literal',
           'phrasal-figurative'},
}

MODULE_NAMES = {
    '01': 'English Verb System::01 - Core Tense & Aspect',
    '02': 'English Verb System::02 - Future Forms',
    '03': 'English Verb System::03 - Conditionals',
    '04': 'English Verb System::04 - Passive Voice',
    '05': 'English Verb System::05 - Stative vs Dynamic',
    '06': 'English Verb System::06 - Reported Speech',
    '07': 'English Verb System::07 - Time Clauses',
    '08': 'English Verb System::08 - Modal Verbs',
    '09': 'English Verb System::09 - Subjunctive & Wish',
    '10': 'English Verb System::10 - Non-Finite Forms',
    '11': 'English Verb System::11 - Phrasal Verbs',
    '12': 'English Verb System::12 - Discourse & Pragmatics',
    '13': 'English Verb System::13 - L1 Interference',
    '14': 'English Verb System::14 - Image Cue',
}


def row_module(tags_str):
    tags = set(tags_str.split())
    # Check newer/more-specific modules first so e.g. a phrasal-verb card
    # tagged with both 'phrasal-verb' and 'modal' routes to module 11.
    for mod in ['14', '13', '12', '11', '10', '09', '08', '07', '06', '05', '04', '03', '02']:
        if tags & MODULE_TAGS[mod]:
            return mod
    return '01'


# ── Tier-2 media plumbing ───────────────────────────────────────────────
MEDIA_AUDIO_DIR = Path('media/audio')
MEDIA_IPA_INDEX = Path('media/ipa_index.json')
MEDIA_TIMELINES_DIR = Path('media/timelines')
MEDIA_TIMELINES_INDEX = Path('media/timelines_index.json')
MEDIA_IMAGES_DIR = Path('media/images')
MEDIA_IMAGES_INDEX = Path('media/images_index.json')
IMAGE_TSV = Path('conjugations_image.txt')


def _sentence_hash(text):
    return hashlib.sha1((text or '').strip().encode('utf-8')).hexdigest()[:12]


def load_media_indices():
    """Return (ipa_index, timeline_index, media_files) for the package.
    Falls back to empty maps if media hasn't been generated yet."""
    ipa_index = {}
    timeline_index = {}
    if MEDIA_IPA_INDEX.exists():
        ipa_index = json.loads(MEDIA_IPA_INDEX.read_text(encoding='utf-8'))
    if MEDIA_TIMELINES_INDEX.exists():
        timeline_index = json.loads(MEDIA_TIMELINES_INDEX.read_text(encoding='utf-8'))

    # Collect all media files we'll bundle into the .apkg
    media_files = []
    if MEDIA_AUDIO_DIR.exists():
        media_files.extend(str(p) for p in sorted(MEDIA_AUDIO_DIR.glob('*.mp3'))
                           if p.stat().st_size > 0)
    if MEDIA_TIMELINES_DIR.exists():
        media_files.extend(str(p) for p in sorted(MEDIA_TIMELINES_DIR.glob('*.svg')))
    if MEDIA_IMAGES_DIR.exists():
        media_files.extend(str(p) for p in sorted(MEDIA_IMAGES_DIR.glob('*.jpg')))
        media_files.extend(str(p) for p in sorted(MEDIA_IMAGES_DIR.glob('*.png')))
    return ipa_index, timeline_index, media_files


def load_image_index():
    """Return {caption_hash → manifest_entry} or {} if not built yet."""
    if MEDIA_IMAGES_INDEX.exists():
        try:
            return json.loads(MEDIA_IMAGES_INDEX.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def _image_caption_hash(caption):
    return hashlib.sha1((caption or '').strip().encode('utf-8')).hexdigest()[:12]


def media_for_sentence(sentence, ipa_index, timeline_index, label=''):
    """Return (audio_field, ipa_field, timeline_field) for a sentence.
    Audio field uses Anki's [sound:filename.mp3] tag; timeline uses <img>."""
    h = _sentence_hash(sentence)
    audio_path = MEDIA_AUDIO_DIR / f'{h}.mp3'
    audio_field = f'[sound:{h}.mp3]' if audio_path.exists() and audio_path.stat().st_size > 0 else ''
    ipa_field = ipa_index.get(h, '')
    timeline_file = timeline_index.get(label, '')
    timeline_field = f'<img src="{timeline_file}">' if timeline_file else ''
    return audio_field, ipa_field, timeline_field


def embed_fsrs_preset(apkg_path):
    """Post-process the .apkg to embed a recommended FSRS deck-options preset.

    genanki 0.13 ships the package with Anki's stock SM-2 dconf and no
    FSRS / sibling-burying / sensible learning-steps. We open the embedded
    SQLite collection, replace the JSON in col.dconf with our preset, and
    re-pack the .apkg in place. On import Anki creates a deck-options preset
    named 'English Verb System' and applies it to the bundled decks.
    """
    import json as _json
    import sqlite3 as _sqlite3
    import tempfile as _tempfile
    import shutil as _shutil
    import zipfile as _zipfile
    import os as _os

    preset = {
        'id': 1700000000001,
        'mod': 0,
        'name': 'English Verb System',
        'usn': 0,
        'maxTaken': 60,
        'autoplay': True,
        'timer': 0,
        'replayq': True,
        # New cards
        'new': {
            'bury': True,                 # bury new siblings
            'delays': [1.0, 10.0],        # learning steps (minutes)
            'initialFactor': 2500,        # 250% starting ease
            'ints': [1, 4, 0],            # graduating=1d, easy=4d
            'order': 1,                   # in order added
            'perDay': 10,
            'separate': True,
        },
        # Reviews
        'rev': {
            'bury': True,                 # bury review siblings
            'ease4': 1.30,                # easy bonus 130%
            'ivlFct': 1.0,                # interval modifier 100%
            'maxIvl': 365,
            'perDay': 150,
            'hardFactor': 1.2,            # hard interval 120%
        },
        # Lapses
        'lapse': {
            'delays': [10.0],             # relearning step 10m
            'leechAction': 0,             # 0 = suspend
            'leechFails': 8,
            'minInt': 1,
            'mult': 0.0,
        },
        'dyn': False,
        # FSRS settings (Anki 23.10+ honours these)
        'fsrsParams5': [],                # use Anki defaults until user trains
        'desiredRetention': 0.90,
        'fsrsWeightSearch': '',
        # Anki 23.10+ key for enabling FSRS at the preset level
        'fsrs': True,
    }

    # Extract → patch → repack
    with _tempfile.TemporaryDirectory() as tmpdir:
        with _zipfile.ZipFile(apkg_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Anki packages may use collection.anki2 or collection.anki21
        col_path = None
        for name in ('collection.anki21', 'collection.anki2'):
            p = _os.path.join(tmpdir, name)
            if _os.path.exists(p):
                col_path = p
                break
        if not col_path:
            print('  [fsrs-preset] no collection db found; skipping')
            return

        conn = _sqlite3.connect(col_path)
        cur = conn.cursor()
        try:
            row = cur.execute('SELECT dconf FROM col').fetchone()
            if not row:
                print('  [fsrs-preset] empty col table; skipping')
                return
            dconf = _json.loads(row[0]) if row[0] else {}
            # Anki keys dconfs by string id
            dconf[str(preset['id'])] = preset
            cur.execute('UPDATE col SET dconf = ?', (_json.dumps(dconf),))

            # Point every deck at our preset so it's used out of the box
            drow = cur.execute('SELECT decks FROM col').fetchone()
            if drow and drow[0]:
                decks_blob = _json.loads(drow[0])
                for did, ddef in decks_blob.items():
                    if did == '1':
                        continue  # leave the default deck alone
                    if isinstance(ddef, dict) and ddef.get('dyn', 0) == 0:
                        ddef['conf'] = preset['id']
                cur.execute('UPDATE col SET decks = ?', (_json.dumps(decks_blob),))

            conn.commit()
        finally:
            conn.close()

        # Repack — preserve original layout (collection db + media + media map)
        tmp_apkg = apkg_path + '.tmp'
        with _zipfile.ZipFile(tmp_apkg, 'w', _zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in _os.walk(tmpdir):
                for fname in files:
                    full = _os.path.join(root, fname)
                    arc = _os.path.relpath(full, tmpdir)
                    zf.write(full, arc)
        _shutil.move(tmp_apkg, apkg_path)
        print('  [fsrs-preset] embedded preset "English Verb System" '
              '(FSRS on, retention 0.90, sibling burying)')

    # Also emit a standalone preset JSON next to the .apkg so users can
    # import it via Anki 23.10+ Deck Options → ⋮ → Import preset.
    # This works around Anki's long-standing bug where deck-options
    # embedded in an .apkg are not reliably honoured on import.
    preset_for_import = {k: v for k, v in preset.items()
                         if k not in ('id', 'mod', 'usn')}
    preset_json_path = Path('english_verb_system_preset.json')
    preset_json_path.write_text(
        _json.dumps(preset_for_import, indent=2) + '\n', encoding='utf-8')
    print(f'  [fsrs-preset] wrote standalone {preset_json_path} '
          f'for one-click Deck-Options Import')


def main():
    ensure_genanki()
    import genanki

    # ------------------------------------------------------------------
    # Shared CSS
    # ------------------------------------------------------------------
    css = '''
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-size: 19px;
  text-align: left;
  color: #1f2937;
  background: #ffffff;
  line-height: 1.5;
  max-width: 860px;
  margin: 0 auto;
  padding: 4px 0;
}

/* ── Front instruction line ── */
.instruction {
  font-size: 0.82em;
  color: #9ca3af;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-bottom: 10px;
}

/* ── Main sentence / prompt ── */
.sentence {
  font-size: 1.15em;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
  line-height: 1.4;
}

/* ── A/B options on contrast cards ── */
.options {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option {
  padding: 9px 14px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.97em;
  color: #374151;
  background: #f9fafb;
}
.option .opt-letter {
  font-weight: 700;
  color: #6b7280;
  margin-right: 6px;
}

/* ── Answer divider ── */
hr#answer {
  border: none;
  border-top: 2px solid #e5e7eb;
  margin: 20px 0 16px;
}

/* ── Primary answer block ── */
.answer-label {
  font-size: 1.35em;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}
.answer-correct {
  display: inline-block;
  background: #dcfce7;
  color: #166534;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.88em;
  font-weight: 600;
  margin-bottom: 10px;
}

/* ── Formula and main use ── */
.meta-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
  margin: 10px 0 14px;
  font-size: 0.93em;
}
.meta-key {
  color: #6b7280;
  font-weight: 600;
  white-space: nowrap;
}
.meta-val {
  color: #1f2937;
}

/* ── Secondary info box (cue + contrast) ── */
.info-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 11px 14px;
  font-size: 0.88em;
  color: #374151;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.info-row {
  display: flex;
  gap: 8px;
}
.info-key {
  color: #9ca3af;
  font-weight: 600;
  white-space: nowrap;
  min-width: 80px;
}
.info-val {
  color: #374151;
}

/* ── Why / tip block ── */
.why-block {
  margin-top: 10px;
  font-size: 0.93em;
  color: #374151;
  line-height: 1.5;
}
.why-block .why-label {
  font-weight: 700;
  color: #111827;
}
.tip-block {
  margin-top: 8px;
  font-size: 0.87em;
  color: #6b7280;
  font-style: italic;
  border-left: 3px solid #d1d5db;
  padding-left: 10px;
}

/* ── Production sample answer ── */
.sample-label {
  font-size: 0.8em;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
}
.sample-answer {
  font-size: 1.05em;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 10px;
}
.target-badge {
  display: inline-block;
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.82em;
  font-weight: 600;
  margin-top: 6px;
}

/* ── Mobile responsive: tighten paddings, scale fonts ── */
@media (max-width: 600px) {
  .card { font-size: 16px; padding: 2px 0; }
  .sentence { font-size: 1.05em; }
  .answer-label { font-size: 1.18em; }
  .option { padding: 7px 10px; font-size: 0.92em; }
}

/* ── Dark mode (Anki "night mode" toggles .nightMode on body) ── */
.nightMode .card,
.night_mode .card {
  background: #111827;
  color: #e5e7eb;
}
.nightMode .sentence, .night_mode .sentence,
.nightMode .answer-label, .night_mode .answer-label {
  color: #f9fafb;
}
.nightMode .instruction, .night_mode .instruction {
  color: #9ca3af;
}
.nightMode .option, .night_mode .option {
  background: #1f2937;
  border-color: #374151;
  color: #d1d5db;
}
.nightMode hr#answer, .night_mode hr#answer {
  border-top-color: #374151;
}
.nightMode .answer-correct, .night_mode .answer-correct {
  background: #064e3b;
  color: #d1fae5;
  border-color: #065f46;
}
.nightMode .info-box, .night_mode .info-box,
.nightMode .why-box, .night_mode .why-box,
.nightMode .tip-box, .night_mode .tip-box {
  background: #1f2937;
  border-color: #374151;
  color: #e5e7eb;
}
.nightMode .badge, .night_mode .badge {
  background: #1e3a8a;
  color: #dbeafe;
  border-color: #1e40af;
}

/* ── Tier-2 additions: audio row, IPA box, timeline image ── */
.audio-row {
  margin: 6px 0 8px;
  font-size: 0.85em;
  color: #6b7280;
}
.ipa-box {
  margin-top: 10px;
  padding: 6px 10px;
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 6px;
  font-family: "Charis SIL", "Doulos SIL", "Lucida Sans Unicode", serif;
  font-size: 0.95em;
}
.ipa-box summary {
  list-style: none;
  cursor: pointer;
  outline: none;
}
.ipa-box summary::-webkit-details-marker {
  display: none;
}
.ipa-key {
  font-weight: 700;
  color: #92400e;
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  font-size: 0.78em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-right: 6px;
}
.ipa-val {
  color: #78350f;
  display: none;
  margin-left: 4px;
}
.ipa-box[open] .ipa-val {
  display: inline;
}
.timeline-box {
  margin: 10px 0;
  text-align: center;
}
.timeline-box img {
  max-width: 100%;
  height: auto;
  display: inline-block;
}
.image-box {
  margin: 14px auto;
  text-align: center;
  max-width: 480px;
}
.image-box img {
  max-width: 100%;
  max-height: 360px;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.nightMode .image-box img, .night_mode .image-box img {
  box-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.nightMode .ipa-box, .night_mode .ipa-box {
  background: #422006;
  border-color: #78350f;
}
.nightMode .ipa-box summary, .night_mode .ipa-box summary {
  cursor: pointer;
}
.nightMode .ipa-key, .night_mode .ipa-key { color: #fde68a; }
.nightMode .ipa-val, .night_mode .ipa-val {
  color: #fef3c7;
  display: none;
}
.nightMode .ipa-box[open] .ipa-val, .night_mode .ipa-box[open] .ipa-val {
  display: inline;
}
.nightMode .audio-row, .night_mode .audio-row { color: #9ca3af; }

/* ── Tier-3 additions: WhenNotToUse callout, cloze hint row ── */
.when-not-box {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fef2f2;
  border-left: 3px solid #dc2626;
  border-radius: 4px;
  font-size: 0.92em;
  color: #7f1d1d;
}
.when-not-key {
  font-weight: 700;
  margin-right: 6px;
  color: #b91c1c;
}
.when-not-val { color: #7f1d1d; }
.hint-row {
  margin: 8px 0;
  padding: 6px 10px;
  background: #f0fdf4;
  border-left: 3px solid #16a34a;
  border-radius: 4px;
  font-size: 0.88em;
  color: #166534;
}
/* Night-mode for Tier-3 boxes */
.nightMode .when-not-box, .night_mode .when-not-box {
  background: #450a0a;
  color: #fecaca;
  border-left-color: #ef4444;
}
.nightMode .when-not-key, .night_mode .when-not-key { color: #fca5a5; }
.nightMode .when-not-val, .night_mode .when-not-val { color: #fecaca; }
.nightMode .hint-row, .night_mode .hint-row {
  background: #052e16;
  color: #bbf7d0;
  border-left-color: #22c55e;
}
/* Anki cloze blank styling */
.cloze {
  font-weight: 700;
  color: #1d4ed8;
  background: #dbeafe;
  padding: 0 4px;
  border-radius: 3px;
}
.nightMode .cloze, .night_mode .cloze {
  color: #93c5fd;
  background: #1e3a8a;
}
'''

    # ------------------------------------------------------------------
    # RECOGNITION MODEL
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
    # ------------------------------------------------------------------
    rec_model = genanki.Model(
        2056102008,  # bumped: schema changed again (added WhenNotToUse)
        'Verb System · Recognition (v3)',
        fields=[
            {'name': 'Sentence'},
            {'name': 'Label'},
            {'name': 'Aspect'},
            {'name': 'Formula'},
            {'name': 'MainUse'},
            {'name': 'QuickCue'},
            {'name': 'Contrast'},
            {'name': 'WhenNotToUse'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Recognition Card',
            'qfmt': '''
<div class="instruction">What tense or aspect is this?</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
''',
            'afmt': '''
<div class="instruction">What tense or aspect is this?</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<hr id="answer">
<div class="answer-label">{{Label}}</div>
{{#Aspect}}<span class="answer-correct">{{Aspect}}</span>{{/Aspect}}
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
<div class="meta-grid">
  <span class="meta-key">Formula</span><span class="meta-val">{{Formula}}</span>
  <span class="meta-key">Main use</span><span class="meta-val">{{MainUse}}</span>
</div>
{{#WhenNotToUse}}<div class="when-not-box"><span class="when-not-key">🚫 Don't use when</span> <span class="when-not-val">{{WhenNotToUse}}</span></div>{{/WhenNotToUse}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
{{#QuickCue}}
<div class="info-box">
  <div class="info-row"><span class="info-key">Quick cue</span><span class="info-val">{{QuickCue}}</span></div>
  {{#Contrast}}<div class="info-row"><span class="info-key">Contrast</span><span class="info-val">{{Contrast}}</span></div>{{/Contrast}}
</div>
{{/QuickCue}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # CONTRAST MODEL
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    # ------------------------------------------------------------------
    con_model = genanki.Model(
        2056102005,  # bumped
        'Verb System · Contrast (v2)',
        fields=[
            {'name': 'Sentence'},
            {'name': 'OptionA'},
            {'name': 'OptionB'},
            {'name': 'Answer'},
            {'name': 'Why'},
            {'name': 'Tip'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Contrast Card',
            'qfmt': '''
<div class="instruction">Which label fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
''',
            'afmt': '''
<div class="instruction">Which label fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
<hr id="answer">
<span class="answer-correct">✓ {{Answer}}</span>
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
<div class="why-block"><span class="why-label">Why: </span>{{Why}}</div>
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
{{#Tip}}<div class="tip-block">{{Tip}}</div>{{/Tip}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # SPOT-THE-ERROR MODEL (v1)
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    # Same schema as Contrast, but front shows strikethrough OptionA
    # ------------------------------------------------------------------
    spot_error_model = genanki.Model(
        2056102006,  # new model ID
        'Verb System · Spot-the-Error (v1)',
        fields=[
            {'name': 'Sentence'},
            {'name': 'OptionA'},
            {'name': 'OptionB'},
            {'name': 'Answer'},
            {'name': 'Why'},
            {'name': 'Tip'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Spot-the-Error Card',
            'qfmt': '''
<div class="instruction">Spot the error</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="options">
  <div class="option"><span class="opt-letter">ERROR:</span><s>{{OptionA}}</s></div>
</div>
''',
            'afmt': '''
<div class="instruction">Spot the error</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="options">
  <div class="option"><span class="opt-letter">ERROR:</span><s>{{OptionA}}</s></div>
</div>
<hr id="answer">
<span class="answer-correct">✓ {{Answer}}: {{OptionB}}</span>
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
<div class="why-block"><span class="why-label">Why: </span>{{Why}}</div>
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
{{#Tip}}<div class="tip-block">{{Tip}}</div>{{/Tip}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # PRODUCTION MODEL
    # Fields: Prompt | Target | Aspect | Sample | Why | Tags
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # CLOZE MODEL (Tier-3 — uses Anki's built-in cloze type)
    # Fields: Text | Hint | Tags | Audio | IPA | Timeline
    # ------------------------------------------------------------------
    cloze_model = genanki.Model(
        2056102007,
        'Verb System · Cloze',
        fields=[
            {'name': 'Text'},
            {'name': 'Hint'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Cloze Card',
            'qfmt': '''
<div class="instruction">Fill in the missing form</div>
<div class="sentence">{{cloze:Text}}</div>
{{#Hint}}<div class="hint-row">💡 {{Hint}}</div>{{/Hint}}
''',
            'afmt': '''
<div class="instruction">Fill in the missing form</div>
<div class="sentence">{{cloze:Text}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
{{#Hint}}<div class="hint-row">💡 {{Hint}}</div>{{/Hint}}
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
''',
        }],
        css=css,
        model_type=genanki.Model.CLOZE,
    )

    pro_model = genanki.Model(
        2056102011,  # was 2056102007 — collided with cloze_model
        'Verb System · Production (v3)',
        fields=[
            {'name': 'Prompt'},
            {'name': 'Target'},
            {'name': 'Aspect'},
            {'name': 'Sample'},
            {'name': 'Why'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Production Card',
            'qfmt': '''
<div class="instruction">Produce a sentence — type your answer below</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
{{type:Sample}}
''',
            'afmt': '''
<div class="instruction">Produce a sentence</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
<hr id="answer">
<div class="sample-label">Sample answer (compared to your input above)</div>
<div class="sample-answer">{{type:Sample}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
<div class="why-block"><span class="why-label">Why this works: </span>{{Why}}</div>
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # REVERSE PRODUCTION (AUTO) MODEL (v1)
    # Fields: Prompt | Sample | Why | Tags
    # Auto-generated from recognition rows for B2+ learners
    # ------------------------------------------------------------------
    rev_pro_model = genanki.Model(
        2056102010,  # was 2056102008 — collided with rec_model
        'Verb System · Reverse Production (Auto) (v1)',
        fields=[
            {'name': 'Prompt'},
            {'name': 'Sample'},
            {'name': 'Why'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
        ],
        templates=[{
            'name': 'Reverse Production Card',
            'qfmt': '''
<div class="instruction">Produce a sentence</div>
<div class="sentence">{{Prompt}}</div>
{{type:Sample}}
''',
            'afmt': '''
<div class="instruction">Produce a sentence</div>
<div class="sentence">{{Prompt}}</div>
<hr id="answer">
<div class="sample-label">Sample answer</div>
<div class="sample-answer">{{type:Sample}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
{{#Why}}<div class="why-block"><span class="why-label">Note: </span>{{Why}}</div>{{/Why}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # IMAGE-CUE MODEL (v1) — visual semantics for stative/dynamic, aspect, phrasals
    # Fields: ImageQuery | Caption | Form | Function | Contrast | Tags | Image | Audio | IPA | Attribution
    # Front: image only; learner formulates the caption silently.
    # Back:  caption + form/function + contrast + audio + IPA + image + CC attribution.
    # ------------------------------------------------------------------
    img_model = genanki.Model(
        2056102009,  # new model ID
        'Verb System · Image Cue (v1)',
        fields=[
            {'name': 'ImageQuery'},
            {'name': 'Caption'},
            {'name': 'Form'},
            {'name': 'Function'},
            {'name': 'Contrast'},
            {'name': 'Tags'},
            {'name': 'Image'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Attribution'},
        ],
        templates=[{
            'name': 'Image Cue Card',
            'qfmt': '''
<div class="instruction">Describe what you see in one English sentence</div>
{{#Image}}<div class="image-box">{{Image}}</div>{{/Image}}
{{^Image}}<div class="instruction">[image not available — caption: {{ImageQuery}}]</div>{{/Image}}
''',
            'afmt': '''
<div class="instruction">Describe what you see</div>
{{#Image}}<div class="image-box">{{Image}}</div>{{/Image}}
<hr id="answer">
<div class="sentence">{{Caption}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="target-badge">{{Form}}</div>
<div class="why-block"><span class="why-label">Function: </span>{{Function}}</div>
{{#Contrast}}<div class="tip-block"><span class="why-label">Contrast: </span>{{Contrast}}</div>{{/Contrast}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
{{#Attribution}}<div class="hint-row" style="font-size:0.75em;opacity:0.7">📷 {{Attribution}}</div>{{/Attribution}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # Decks
    # ------------------------------------------------------------------
    DECK_IDS = {
        ('01', 'rec'): 2056101101, ('01', 'con'): 2056101102, ('01', 'pro'): 2056101103,
        ('02', 'rec'): 2056101201, ('02', 'con'): 2056101202, ('02', 'pro'): 2056101203,
        ('03', 'rec'): 2056101301, ('03', 'con'): 2056101302, ('03', 'pro'): 2056101303,
        ('04', 'rec'): 2056101401, ('04', 'con'): 2056101402, ('04', 'pro'): 2056101403,
        ('05', 'rec'): 2056101501, ('05', 'con'): 2056101502, ('05', 'pro'): 2056101503,
        ('06', 'rec'): 2056101601, ('06', 'con'): 2056101602, ('06', 'pro'): 2056101603,
        ('07', 'rec'): 2056101701, ('07', 'con'): 2056101702, ('07', 'pro'): 2056101703,
        ('08', 'rec'): 2056101801, ('08', 'con'): 2056101802, ('08', 'pro'): 2056101803,
        ('09', 'rec'): 2056101901, ('09', 'con'): 2056101902, ('09', 'pro'): 2056101903,
        ('10', 'rec'): 2056102001, ('10', 'con'): 2056102002, ('10', 'pro'): 2056102003,
        ('11', 'rec'): 2056102101, ('11', 'con'): 2056102102, ('11', 'pro'): 2056102103,
        ('12', 'rec'): 2056102201, ('12', 'con'): 2056102202, ('12', 'pro'): 2056102203,
        ('13', 'rec'): 2056102301, ('13', 'con'): 2056102302, ('13', 'pro'): 2056102303,
        # Cloze decks (Tier 3)
        ('01', 'clz'): 2056101104, ('02', 'clz'): 2056101204, ('03', 'clz'): 2056101304,
        ('04', 'clz'): 2056101404, ('05', 'clz'): 2056101504, ('06', 'clz'): 2056101604,
        ('07', 'clz'): 2056101704, ('08', 'clz'): 2056101804, ('09', 'clz'): 2056101904,
        ('10', 'clz'): 2056102004, ('11', 'clz'): 2056102104, ('12', 'clz'): 2056102204,
        ('13', 'clz'): 2056102304,
        # Image-Cue deck (Tier 4)
        ('14', 'img'): 2056102401,
    }
    TYPE_SUFFIX = {'rec': '::1 - Recognition', 'con': '::2 - Contrast',
                   'pro': '::3 - Production', 'clz': '::4 - Cloze',
                   'img': '::1 - Image Cue'}

    deck_description = f'English Verb System v{VERSION} — Comprehensive tense, aspect, and mood study. <a href="{CHANGELOG_URL}">Changelog</a>'
    
    decks = {}
    for (mod, typ), did in DECK_IDS.items():
        name = MODULE_NAMES[mod] + TYPE_SUFFIX[typ]
        decks[(mod, typ)] = genanki.Deck(did, name, description=deck_description)

    counts = {'rec': 0, 'con': 0, 'pro': 0, 'clz': 0}
    media_counts = {'audio': 0, 'ipa': 0, 'timeline': 0}

    # Tier-2 media indices
    ipa_index, timeline_index, media_files = load_media_indices()

    # Load production samples for deduplication in reverse-production generation
    existing_samples = set()
    pro_path = Path('conjugations_production.txt')
    if pro_path.exists():
        _, pro_rows = load_tsv(str(pro_path))
        for row in pro_rows:
            if len(row) >= 4:
                existing_samples.add(row[3].strip())  # Sample is column 3

    # Recognition
    _, rec_rows = load_tsv('conjugations_recognition.txt')
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | WhenNotToUse | Tags
    for row in rec_rows:
        if len(row) < 9:
            row += [''] * (9 - len(row))
        mod = row_module(row[8])  # Tags now at index 8
        audio_f, ipa_f, tl_f = media_for_sentence(row[0], ipa_index, timeline_index, label=row[1])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        note = genanki.Note(
            model=rec_model,
            fields=row[:9] + [audio_f, ipa_f, tl_f],
            tags=row[8].split(),
        )
        decks[(mod, 'rec')].add_note(note)
        counts['rec'] += 1

    # Reverse Production (Auto) — generated from recognition rows
    rev_pro_count = 0
    standard_tenses = {
        'Present Simple', 'Past Simple', 'Present Perfect',
        'Present Perfect Continuous', 'Past Perfect', 'Past Perfect Continuous',
        'Future Perfect', 'Future Continuous', 'Future Perfect Continuous',
    }
    cefr_b2_plus = {'cefr:b2', 'cefr:c1', 'cefr:c2'}
    
    for row in rec_rows:
        if len(row) < 9:
            row += [''] * (9 - len(row))
        
        label = row[1]
        tags_str = row[8]
        tags_set = set(tags_str.split())
        
        # Check if label is in standard tense set and CEFR is B2+
        if label not in standard_tenses or not (tags_set & cefr_b2_plus):
            continue
        
        sentence = row[0]  # The Sentence field as the prompt
        formula = row[3]   # Formula for Why
        
        # Skip if sentence already exists in production samples
        if sentence in existing_samples:
            continue
        
        mod = row_module(tags_str)
        audio_f, ipa_f, tl_f = media_for_sentence(sentence, ipa_index, timeline_index, label=label)
        
        # Create reverse production note
        # Fields: Prompt | Sample | Why | Tags | Audio | IPA | Timeline
        rev_pro_note = genanki.Note(
            model=rev_pro_model,
            fields=[sentence, sentence, formula, tags_str, audio_f, ipa_f, tl_f],
            tags=tags_set.split() if isinstance(tags_set, str) else list(tags_set),
        )
        decks[(mod, 'pro')].add_note(rev_pro_note)
        rev_pro_count += 1
        existing_samples.add(sentence)

    # Contrast
    _, con_rows = load_tsv('conjugations_contrast.txt')
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    spot_error_count = 0
    for row in con_rows:
        if len(row) < 7:
            row += [''] * (7 - len(row))
        mod = row_module(row[6])
        # For contrast, the "label" we map to a timeline is the Answer (column 3)
        audio_f, ipa_f, tl_f = media_for_sentence(row[0], ipa_index, timeline_index, label=row[3])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        
        # Create regular contrast note
        note = genanki.Note(
            model=con_model,
            fields=row[:7] + [audio_f, ipa_f, tl_f],
            tags=row[6].split(),
        )
        decks[(mod, 'con')].add_note(note)
        counts['con'] += 1
        
        # Create spot-the-error note if row has error-correction, l1-interference, or spot-the-error tag
        tags_set = set(row[6].split())
        error_tags = {'error-correction', 'l1-interference', 'spot-the-error'}
        if tags_set & error_tags:
            spot_note = genanki.Note(
                model=spot_error_model,
                fields=row[:7] + [audio_f, ipa_f, tl_f],
                tags=row[6].split(),
            )
            decks[(mod, 'con')].add_note(spot_note)
            spot_error_count += 1

    # Production
    _, pro_rows = load_tsv('conjugations_production.txt')
    # Fields: Prompt | Target | Aspect | Sample | Why | Tags
    for row in pro_rows:
        if len(row) < 6:
            row += [''] * (6 - len(row))
        mod = row_module(row[5])
        # For production, audio/IPA come from the Sample (column 3); timeline from Target (column 1).
        audio_f, ipa_f, tl_f = media_for_sentence(row[3], ipa_index, timeline_index, label=row[1])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        note = genanki.Note(
            model=pro_model,
            fields=row[:6] + [audio_f, ipa_f, tl_f],
            tags=row[5].split(),
        )
        decks[(mod, 'pro')].add_note(note)
        counts['pro'] += 1

    # Cloze (Tier 3)
    counts['clz'] = 0
    cloze_path = Path('conjugations_cloze.txt')
    if cloze_path.exists():
        _, cloze_rows = load_tsv(str(cloze_path))
        for row in cloze_rows:
            if len(row) < 3:
                row += [''] * (3 - len(row))
            mod = row_module(row[2])
            # For cloze, the spoken sentence is the cloze Text with the
            # {{c1::…}} markers stripped — that's the natural English audio.
            spoken = re.sub(r'\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}', r'\1', row[0])
            audio_f, ipa_f, tl_f = media_for_sentence(spoken, ipa_index, timeline_index, label='')
            if audio_f: media_counts['audio'] += 1
            if ipa_f: media_counts['ipa'] += 1
            note = genanki.Note(
                model=cloze_model,
                fields=row[:3] + [audio_f, ipa_f, tl_f],
                tags=row[2].split(),
            )
            decks[(mod, 'clz')].add_note(note)
            counts['clz'] += 1

    # Image-Cue (Module 14)
    img_count = 0
    if IMAGE_TSV.exists():
        img_index = load_image_index()
        _, img_rows = load_tsv(str(IMAGE_TSV))
        for row in img_rows:
            if len(row) < 6:
                row += [''] * (6 - len(row))
            tags_str = row[5]
            mod = '14'
            caption = row[1].strip()
            cap_h = _image_caption_hash(caption)
            entry = img_index.get(cap_h, {})
            img_filename = entry.get('file', '')
            img_field = f'<img src="{img_filename}">' if img_filename else ''
            attrib = entry.get('attribution', '') or entry.get('license', '')
            source_url = entry.get('source', '')
            attribution_field = (
                f'{attrib} — <a href="{source_url}">source</a> ({entry.get("license", "")})'
                if entry else ''
            )
            audio_f, ipa_f, _tl = media_for_sentence(caption, ipa_index, timeline_index, label='')
            if audio_f: media_counts['audio'] += 1
            if ipa_f: media_counts['ipa'] += 1
            if img_field: media_counts.setdefault('image', 0); media_counts['image'] = media_counts.get('image', 0) + 1
            note = genanki.Note(
                model=img_model,
                fields=[row[0], caption, row[2], row[3], row[4], tags_str,
                        img_field, audio_f, ipa_f, attribution_field],
                tags=tags_str.split(),
            )
            decks[(mod, 'img')].add_note(note)
            img_count += 1

    out = 'english_verb_system_anki.apkg'
    package = genanki.Package(list(decks.values()))
    package.media_files = media_files
    package.write_to_file(out)

    # ── v2.0: repackage through the official `anki` library so the deck
    # preset auto-binds on import (genanki produces legacy v11 format
    # whose deck-options Anki silently discards on import). The repackager
    # imports the genanki output, binds every deck to our preset using
    # the proper backend API, then re-exports with `with_deck_configs=true`
    # in the modern .anki21b format. Anki Desktop 23.10+ then auto-creates
    # the preset and applies it to every imported deck — no manual step.
    try:
        from repackage_with_official_anki import repackage as _repackage
    except Exception as _e:
        print(f'  [repackage] could not import repackager: {_e}')
        print(f'  [repackage] falling back to legacy embed_fsrs_preset (preset will NOT auto-bind)')
        embed_fsrs_preset(out)
    else:
        rc = _repackage(Path(out), Path(out))
        if rc != 0:
            print(f'\n✗ Repackage failed (rc={rc}). Aborting.')
            sys.exit(rc)

    # Post-build integrity check: round-trip through SQLite to catch
    # model-id collisions, field-count mismatches, dangling references, etc.
    # Hard failure here aborts the build with non-zero exit so a broken
    # .apkg can never be shipped silently.
    try:
        import validate_apkg as _validate_apkg
    except Exception as _e:
        print(f'  [validate-apkg] could not import validator: {_e}')
    else:
        rc = _validate_apkg.validate(out)
        if rc != 0:
            print(f'\n✗ Post-build validation failed (rc={rc}). '
                  f'See errors above. .apkg left in place for inspection.')
            sys.exit(rc)

    total_cards = sum(counts.values()) + spot_error_count + rev_pro_count + img_count
    print(f'Built {out} (v{VERSION})')
    print(f'  recognition: {counts["rec"]}')
    print(f'  contrast:    {counts["con"]}')
    print(f'  spot-the-error: {spot_error_count}')
    print(f'  production:  {counts["pro"]}')
    print(f'  reverse-production (auto): {rev_pro_count}')
    print(f'  cloze:       {counts["clz"]}')
    print(f'  image-cue:   {img_count}')
    print(f'  total:       {total_cards}')
    img_n = media_counts.get('image', 0)
    print(f'Media bundled: {len(media_files)} files '
          f'(audio={media_counts["audio"]}, ipa={media_counts["ipa"]}, '
          f'timeline={media_counts["timeline"]}, image={img_n})')
    print()
    print('Decks:')
    for (mod, typ), deck in decks.items():
        n = len(deck.notes)
        if n:
            print(f'  {deck.name}: {n}')


if __name__ == '__main__':
    main()
