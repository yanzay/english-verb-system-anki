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

VERSION = '3.1.0'
CHANGELOG_URL = 'https://github.com/yanzay/english-verb-system-anki/blob/main/CHANGELOG.md'


def ensure_genanki():
    """Verify the official `anki` package is installed (our genanki shim
    is a drop-in built on top of `anki.Collection`).
    """
    try:
        import anki  # noqa: F401
        return
    except ImportError:
        pass
    print('  [setup] official `anki` package not found; installing…')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                           '--user', '--break-system-packages', 'anki>=24.0'])


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
    # Module 14 (Image-Cue) was REMOVED in v2.7.0. Wikimedia keyword
    # search produced semantically random matches (e.g. "woman thinking
    # in profile" → Picasso sculpture in Chicago). The premise itself
    # was flawed: most verbal-aspect contrasts are abstract and cannot
    # be disambiguated by a still photograph. Better no images than
    # misleading images.
    '_REMOVED_14': {'image', 'module:image', 'image-cue', 'aspect-dynamic',
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
    # Module 13 is split per-L1 so a Russian speaker, say, only sees
    # the contrasts that actually trip Russian speakers up. The bare
    # '13' key is a catch-all for any L1 row that lacks a language tag.
    '13':    'English Verb System::13 - L1 Interference::Other',
    '13-es': 'English Verb System::13 - L1 Interference::🇪🇸 Spanish speakers',
    '13-fr': 'English Verb System::13 - L1 Interference::🇫🇷 French speakers',
    '13-de': 'English Verb System::13 - L1 Interference::🇩🇪 German speakers',
    '13-ru': 'English Verb System::13 - L1 Interference::🇷🇺 Russian speakers',
    '13-zh': 'English Verb System::13 - L1 Interference::🇨🇳 Mandarin speakers',
    '13-ja': 'English Verb System::13 - L1 Interference::🇯🇵 Japanese speakers',
    '13-ko': 'English Verb System::13 - L1 Interference::🇰🇷 Korean speakers',
    '13-ar': 'English Verb System::13 - L1 Interference::🇸🇦 Arabic speakers',
    '13-pt': 'English Verb System::13 - L1 Interference::🇵🇹 Portuguese speakers',
    '13-nl': 'English Verb System::13 - L1 Interference::🇳🇱 Dutch speakers',
    # '14' (Image Cue) intentionally absent — see MODULE_TAGS comment.
}


L1_LANG_SUFFIX = {
    'l1-spanish':    '-es', 'l1-french':     '-fr', 'l1-german':    '-de',
    'l1-russian':    '-ru', 'l1-mandarin':   '-zh', 'l1-japanese':  '-ja',
    'l1-korean':     '-ko', 'l1-arabic':     '-ar', 'l1-portuguese':'-pt',
    'l1-dutch':      '-nl',
}


def row_modules(tags_str):
    """Like row_module() but returns ALL applicable module codes when an
    L1 card pertains to multiple languages (e.g. Romance-language cluster
    tagged with l1-spanish + l1-french + l1-portuguese gets routed to all
    three per-language decks). Always returns at least one element.
    """
    tags = set(tags_str.split())
    if 'l1-interference' in tags or any(t in L1_LANG_SUFFIX for t in tags):
        mods = ['13' + L1_LANG_SUFFIX[t] for t in tags if t in L1_LANG_SUFFIX]
        return mods if mods else ['13']
    return [row_module(tags_str)]


def row_module(tags_str):
    tags = set(tags_str.split())
    # L1 interference routes per-language so each user reviews only their L1.
    # We check this BEFORE the generic module loop because an L1 card may
    # also carry tags like 'modal' (about a specific structure), and we
    # always want it in the per-language deck.
    if 'l1-interference' in tags or any(t in L1_LANG_SUFFIX for t in tags):
        for tag, suffix in L1_LANG_SUFFIX.items():
            if tag in tags:
                return '13' + suffix
        return '13'  # generic L1 card with no specific language → "Other"
    # Check newer/more-specific modules first so e.g. a phrasal-verb card
    # tagged with both 'phrasal-verb' and 'modal' routes to module 11.
    for mod in ['13', '12', '11', '10', '09', '08', '07', '06', '05', '04', '03', '02']:
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
    """DEPRECATED in v2.0: superseded by genanki-shim's official-anki path.

    The anki_packager module in this repo (see ./anki_packager.py) is a drop-in
    shim built on `anki.Collection` that creates the FSRS preset and binds
    every deck to it during the export step itself. This SQLite-hackery
    fallback is kept only as a safety net and is NOT called by main().
    """
    pass


def _embed_fsrs_preset_legacy(apkg_path):
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
    import anki_packager as ap

    # ------------------------------------------------------------------
    # Shared CSS
    # ------------------------------------------------------------------
    css = '''
/* ============================================================
   English Verb System — Design System v3.0
   ------------------------------------------------------------
   Single source of truth for colors. Everything below the token
   block uses var(--*) so light <-> dark theming is automatic and
   no class can ever fall through to invisible-on-dark text.
   ------------------------------------------------------------
   Naming convention:
     --bg-*       background colors
     --fg-*       text/foreground colors  (-strong, -muted, -faint)
     --border-*   border colors
     --accent-*   per-semantic accent (success, info, warn, danger, target, sample, ipa, hint)
     --shadow-*   box-shadows
   Each semantic accent has matching -bg / -fg / -border for its callout.
   ============================================================ */

/* Light theme tokens (default) */
.card {
  --bg-card:        #ffffff;
  --bg-surface:     #f9fafb;
  --bg-surface-2:   #f3f4f6;

  --fg-strong:      #111827;
  --fg-default:     #1f2937;
  --fg-muted:       #4b5563;
  --fg-faint:       #6b7280;
  --fg-fainter:     #9ca3af;

  --border-default: #e5e7eb;
  --border-muted:   #d1d5db;
  --border-strong:  #9ca3af;

  /* Semantic callout palette (bg / fg / border) */
  --success-bg:     #dcfce7;  --success-fg:    #166534;  --success-border: #86efac;
  --info-bg:        #eff6ff;  --info-fg:       #1d4ed8;  --info-border:    #bfdbfe;
  --warn-bg:        #fef3c7;  --warn-fg:       #92400e;  --warn-border:    #fde68a;
  --danger-bg:      #fef2f2;  --danger-fg:     #991b1b;  --danger-border:  #fecaca;
  --hint-bg:        #f0fdf4;  --hint-fg:       #166534;  --hint-border:    #86efac;
  --ipa-bg:         #fef3c7;  --ipa-fg:        #78350f;  --ipa-key-fg:     #92400e;  --ipa-border: #fde68a;
  --sample-fg:      #1e40af;
  --target-bg:      #eff6ff;  --target-fg:     #1d4ed8;  --target-border:  #bfdbfe;
  --cloze-fg:       #1d4ed8;

  --shadow-image:   0 2px 8px rgba(0,0,0,0.15);
}

/* Dark theme tokens.
   Anki applies its night-mode class in DIFFERENT ways across versions
   and clients — sometimes on <body>, sometimes directly on .card itself,
   and the class name is .nightMode (Desktop / AnkiMobile) OR .night_mode
   (AnkiDroid / Krassowski legacy add-on). We cover ALL combinations
   below + add a prefers-color-scheme fallback for any future client. */
.card.nightMode,  .card.night_mode,
.nightMode .card, .night_mode .card,
.nightMode.card, .night_mode.card,
body.nightMode .card, body.night_mode .card,
html.nightMode .card, html.night_mode .card {
  --bg-card:        #0f172a;
  --bg-surface:     #1e293b;
  --bg-surface-2:   #334155;

  --fg-strong:      #f8fafc;
  --fg-default:     #e2e8f0;
  --fg-muted:       #cbd5e1;
  --fg-faint:       #94a3b8;
  --fg-fainter:     #64748b;

  --border-default: #334155;
  --border-muted:   #475569;
  --border-strong:  #64748b;

  --success-bg:     #064e3b;  --success-fg:    #bbf7d0;  --success-border: #047857;
  --info-bg:        #1e3a8a;  --info-fg:       #dbeafe;  --info-border:    #2563eb;
  --warn-bg:        #422006;  --warn-fg:       #fef3c7;  --warn-border:    #92400e;
  --danger-bg:      #450a0a;  --danger-fg:     #fecaca;  --danger-border:  #b91c1c;
  --hint-bg:        #052e16;  --hint-fg:       #bbf7d0;  --hint-border:    #22c55e;
  --ipa-bg:         #422006;  --ipa-fg:        #fef3c7;  --ipa-key-fg:     #fde68a;  --ipa-border: #92400e;
  --sample-fg:      #93c5fd;
  --target-bg:      #1e3a8a;  --target-fg:     #dbeafe;  --target-border:  #2563eb;
  --cloze-fg:       #93c5fd;

  --shadow-image:   0 2px 8px rgba(0,0,0,0.5);
}
/* Belt-and-braces: if Anki ever forgets to add the class but the OS/app
   reports dark mode, still flip our tokens. Anki's own preferences UI
   exposes a "Match OS" toggle that goes through this path. */
@media (prefers-color-scheme: dark) {
  .card {
    --bg-card:        #0f172a;
    --bg-surface:     #1e293b;
    --bg-surface-2:   #334155;
    --fg-strong:      #f8fafc;
    --fg-default:     #e2e8f0;
    --fg-muted:       #cbd5e1;
    --fg-faint:       #94a3b8;
    --fg-fainter:     #64748b;
    --border-default: #334155;
    --border-muted:   #475569;
    --border-strong:  #64748b;
    --success-bg:     #064e3b;  --success-fg:    #bbf7d0;  --success-border: #047857;
    --info-bg:        #1e3a8a;  --info-fg:       #dbeafe;  --info-border:    #2563eb;
    --warn-bg:        #422006;  --warn-fg:       #fef3c7;  --warn-border:    #92400e;
    --danger-bg:      #450a0a;  --danger-fg:     #fecaca;  --danger-border:  #b91c1c;
    --hint-bg:        #052e16;  --hint-fg:       #bbf7d0;  --hint-border:    #22c55e;
    --ipa-bg:         #422006;  --ipa-fg:        #fef3c7;  --ipa-key-fg:     #fde68a;  --ipa-border: #92400e;
    --sample-fg:      #93c5fd;
    --target-bg:      #1e3a8a;  --target-fg:     #dbeafe;  --target-border:  #2563eb;
    --cloze-fg:       #93c5fd;
    --shadow-image:   0 2px 8px rgba(0,0,0,0.5);
  }
}

/* ============================================================
   Layout primitives
   ============================================================ */
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  font-size: 19px;
  text-align: left;
  color: var(--fg-default);
  background: var(--bg-card);
  line-height: 1.5;
  max-width: 860px;
  margin: 0 auto;
  padding: 4px 0;
}

/* Front side: centered prompt for distraction-free recall */
.front { text-align: center; }
.front .options { align-items: center; }
.front .option  { display: inline-block; text-align: left; min-width: 240px; max-width: 100%; }
.front .audio-row { display: flex; justify-content: center; }

/* ============================================================
   Typography blocks
   ============================================================ */
.instruction {
  font-size: 0.82em;
  color: var(--fg-fainter);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.sentence {
  font-size: 1.15em;
  font-weight: 600;
  color: var(--fg-strong);
  margin-bottom: 6px;
  line-height: 1.4;
}

/* ============================================================
   A/B options on contrast cards
   ============================================================ */
.options {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option {
  padding: 9px 14px;
  border: 1.5px solid var(--border-default);
  border-radius: 8px;
  font-size: 0.97em;
  color: var(--fg-default);
  background: var(--bg-surface);
}
.option .opt-letter {
  font-weight: 700;
  color: var(--fg-faint);
  margin-right: 6px;
}

/* ============================================================
   Answer divider + answer block
   ============================================================ */
hr#answer {
  border: none;
  border-top: 2px solid var(--border-default);
  margin: 20px 0 16px;
}
/* Centered answer block: the form name is THE answer; everything
   underneath (aspect chip, formula grid, callouts) is supporting
   metadata for context. Centering matches the front-echo above
   the divider so the eye lands where the answer is. */
.answer-block { text-align: center; }
.answer-label {
  font-size: 1.6em;
  font-weight: 700;
  color: var(--fg-strong);
  margin-bottom: 6px;
  line-height: 1.25;
}
/* Legacy .answer-correct kept for contrast / spot-the-error
   templates that still display it as a green confirmation pill. */
.answer-correct {
  display: inline-block;
  background: var(--success-bg);
  color: var(--success-fg);
  border: 1px solid var(--success-border);
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.88em;
  font-weight: 600;
  margin-bottom: 10px;
}

/* ============================================================
   Meta grid (Formula / Main use). Inside a centered answer block
   the grid itself stays left-aligned via inline-grid + auto margins
   so the key/value columns line up but the whole grid is centered
   horizontally on the card.
   ============================================================ */
.meta-grid {
  display: inline-grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
  margin: 10px auto 14px;
  font-size: 0.93em;
  text-align: left;
  max-width: 560px;
}
.meta-key {
  color: var(--fg-faint);
  font-weight: 600;
  white-space: nowrap;
}
.meta-val { color: var(--fg-default); }

/* ============================================================
   Info box (Quick cue / Contrast)
   ============================================================ */
.info-box {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 11px 14px;
  font-size: 0.88em;
  color: var(--fg-default);
  /* Centered as a block within .answer-block, but key/value rows
     inside stay left-aligned so the columns line up. */
  margin: 12px auto 0;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}
.info-row { display: flex; gap: 8px; }
.info-key {
  color: var(--fg-fainter);
  font-weight: 600;
  white-space: nowrap;
  min-width: 80px;
}
.info-val { color: var(--fg-default); }

/* ============================================================
   Why / tip block
   ============================================================ */
.why-block {
  margin-top: 10px;
  font-size: 0.93em;
  color: var(--fg-default);
  line-height: 1.5;
}
.why-block .why-label {
  font-weight: 700;
  color: var(--fg-strong);
}
.tip-block {
  margin-top: 8px;
  font-size: 0.87em;
  color: var(--fg-muted);
  font-style: italic;
  border-left: 3px solid var(--border-muted);
  padding-left: 10px;
}

/* ============================================================
   Production: sample answer + target badge
   ============================================================ */
.sample-label {
  font-size: 0.8em;
  color: var(--fg-fainter);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
}
.sample-answer {
  font-size: 1.05em;
  font-weight: 600;
  color: var(--sample-fg);
  margin-bottom: 10px;
}
.target-badge {
  display: inline-block;
  background: var(--target-bg);
  color: var(--target-fg);
  border: 1px solid var(--target-border);
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.82em;
  font-weight: 600;
  margin-top: 6px;
}
/* Anki's type:* rendered comparison table inherits sane colors */
input[type=text],
.typeans, .typeGood, .typeBad, .typeMissed {
  color: var(--fg-default);
  background: var(--bg-surface);
}
.typeGood { color: var(--success-fg); background: var(--success-bg); }
.typeBad,
.typeMissed { color: var(--danger-fg); background: var(--danger-bg); }

/* ============================================================
   Audio + IPA + timeline + image
   ============================================================ */
.audio-row {
  margin: 6px 0 8px;
  font-size: 0.85em;
  color: var(--fg-faint);
}
/* IPA: a learner reference, not a primary signal. Quiet styling so
   it never competes with the answer / formula / timeline. The
   <details> element ensures it's collapsed by default; opening it
   reveals the transcription in monospace-friendly serif. */
.ipa-box {
  margin: 10px auto 0;
  max-width: 560px;
  padding: 5px 10px;
  background: var(--bg-surface);
  color: var(--fg-muted);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-family: "Charis SIL", "Doulos SIL", "Lucida Sans Unicode", serif;
  font-size: 0.88em;
  text-align: left;
}
.ipa-box summary {
  list-style: none;
  cursor: pointer;
  outline: none;
}
.ipa-box summary::-webkit-details-marker { display: none; }
.ipa-key {
  font-weight: 600;
  color: var(--fg-faint);
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-right: 6px;
}
.ipa-val {
  color: var(--fg-default);
  display: none;
  margin-left: 4px;
  font-size: 1.05em;
}
.ipa-box[open] .ipa-val { display: inline; }

.timeline-box {
  margin: 10px 0;
  text-align: center;
}
.timeline-box img {
  max-width: 100%;
  max-width: min(420px, 100%);  /* cap width — these are line drawings */
  height: auto;
  display: inline-block;
}
/* The timeline SVGs ship with their own @media (prefers-color-scheme)
   block, so the strokes/labels recolor themselves correctly in dark
   mode. We deliberately do NOT apply an outer invert() filter — that
   double-flips the colors and produces washed-out artifacts. */

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
  box-shadow: var(--shadow-image);
}

/* ============================================================
   WhenNotToUse callout, cloze hint row, attribution, etc.
   ============================================================ */
/* "Don't use when" sidenote: this is supplementary clarification,
   not a danger / error — so style it like .tip-block (quiet muted
   background, italic). The previous loud red callout misleadingly
   read as 'YOU MADE AN ERROR' rather than 'usage caveat'. */
.when-not-box {
  margin: 10px auto 0;
  max-width: 560px;
  padding: 7px 12px;
  background: var(--bg-surface);
  border-left: 3px solid var(--border-muted);
  border-radius: 4px;
  font-size: 0.86em;
  color: var(--fg-muted);
  font-style: italic;
  text-align: left;
}
.when-not-key {
  font-weight: 600;
  margin-right: 6px;
  color: var(--fg-faint);
  font-style: normal;
  letter-spacing: 0.02em;
}
.when-not-val { color: var(--fg-muted); }

.hint-row {
  margin: 8px 0;
  padding: 6px 10px;
  background: var(--hint-bg);
  border-left: 3px solid var(--hint-border);
  border-radius: 4px;
  font-size: 0.88em;
  color: var(--hint-fg);
}

/* Image-cue attribution line (small caption under back image) */
.attribution {
  margin-top: 8px;
  font-size: 0.78em;
  color: var(--fg-faint);
  text-align: center;
  font-style: italic;
}
.attribution a {
  color: var(--info-fg);
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* ============================================================
   Focus highlight on Recognition cards (v3.0.0)
   The <mark class="focus"> tag wraps the span the learner is
   being asked to identify — so prompts like "It could've been
   worse." with answer "Connected Speech (Weak 'have')" become
   unambiguous: the highlighted span tells you what to analyze.
   Subtle pill-shape, theme-aware, never alarm-grade.
   ============================================================ */
mark.focus {
  background: var(--target-bg);
  color: var(--target-fg);
  border: 1px solid var(--target-border);
  border-radius: 4px;
  padding: 0 4px;
  font-weight: 600;
}

/* Anki cloze blank styling */
.cloze {
  font-weight: 700;
  color: var(--cloze-fg);
  background: var(--target-bg);
  padding: 0 4px;
  border-radius: 3px;
}

/* ============================================================
   Mobile responsive: tighten paddings, scale fonts
   ============================================================ */
@media (max-width: 600px) {
  .card { font-size: 16px; padding: 2px 0; }
  .sentence { font-size: 1.05em; }
  .answer-label { font-size: 1.18em; }
  .option { padding: 7px 10px; font-size: 0.92em; }
  .front .option { min-width: 0; width: 100%; }
  .image-box { max-width: 100%; }
  .image-box img { max-height: 280px; }
  .meta-grid { gap: 2px 8px; font-size: 0.88em; }
  .info-key { min-width: 60px; }
}

/* ============================================================
   Browser hint: which themes our card supports.
   Helps native form elements (e.g. {{type:Sample}} input) pick
   matching default colors on iOS / iPadOS WebKit.
   ============================================================ */
.card { color-scheme: light dark; }
'''

    # ------------------------------------------------------------------
    # RECOGNITION MODEL
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
    # ------------------------------------------------------------------
    rec_model = ap.Model(
        2056102015,  # bumped (was 2056102014): added Category field +
                     # unified Prompt. v3.1.0 introduces a proper
                     # grammatical taxonomy: tense-aspect (the 12-cell
                     # canonical grid) is treated as the FIRST thing
                     # learners master; periphrastic-future, modal, mood,
                     # voice, conditional, construction, phonology, etc.
                     # are LATER additions, each with its own prompt
                     # ('Identify the highlighted modal' vs '…tense+aspect'
                     # vs '…construction') so the question is never
                     # misleading.
        'Verb System · Recognition (v7)',
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
            {'name': 'FocusedSentence'},  # Sentence with the targeted
                                          # span wrapped in <mark> when
                                          # extractable, else bare
                                          # sentence.
            {'name': 'Prompt'},           # Always-honest instruction
                                          # matched to the card content
                                          # AND its grammatical category.
            {'name': 'Category'},         # Grammatical category (one of
                                          # 12) for filtering/searching:
                                          # tense-aspect, modal, voice,
                                          # mood, conditional, non-finite,
                                          # periphrastic-future, periphrastic-
                                          # past-habit, construction,
                                          # phrasal-verb, reported-speech,
                                          # phonology.
        ],
        templates=[{
            'name': 'Recognition Card',
            'qfmt': '''
<div class="front">
<div class="instruction">{{Prompt}}</div>
<div class="sentence">{{FocusedSentence}}</div>
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">{{Prompt}}</div>
<div class="sentence">{{FocusedSentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
</div>
<hr id="answer">
<div class="answer-block">
  <div class="answer-label">{{Label}}</div>
  {{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
  <div class="meta-grid">
    <span class="meta-key">Formula</span><span class="meta-val">{{Formula}}</span>
    <span class="meta-key">Main use</span><span class="meta-val">{{MainUse}}</span>
  </div>
  {{#WhenNotToUse}}<div class="when-not-box"><span class="when-not-val">{{WhenNotToUse}}</span></div>{{/WhenNotToUse}}
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  {{#QuickCue}}
  <div class="info-box">
    <div class="info-row"><span class="info-key">Quick cue</span><span class="info-val">{{QuickCue}}</span></div>
    {{#Contrast}}<div class="info-row"><span class="info-key">Contrast</span><span class="info-val">{{Contrast}}</span></div>{{/Contrast}}
  </div>
  {{/QuickCue}}
</div>
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # CONTRAST MODEL
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    # ------------------------------------------------------------------
    con_model = ap.Model(
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
<div class="front">
<div class="instruction">Which form fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Which form fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
</div>
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
<hr id="answer">
<div class="answer-block">
  <span class="answer-correct">✓ {{Answer}}</span>
  {{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
  <div class="why-block"><span class="why-label">Why: </span>{{Why}}</div>
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  {{#Tip}}<div class="tip-block">{{Tip}}</div>{{/Tip}}
</div>
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # SPOT-THE-ERROR MODEL (v1)
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    # Same schema as Contrast, but front shows strikethrough OptionA
    # ------------------------------------------------------------------
    spot_error_model = ap.Model(
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
<div class="front">
<div class="instruction">Spot the error</div>
<div class="sentence">{{Sentence}}</div>
<div class="options">
  <div class="option"><span class="opt-letter">ERROR:</span><s>{{OptionA}}</s></div>
</div>
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Spot the error</div>
<div class="sentence">{{Sentence}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
<div class="options">
  <div class="option"><span class="opt-letter">ERROR:</span><s>{{OptionA}}</s></div>
</div>
</div>
<hr id="answer">
<div class="answer-block">
  <span class="answer-correct">✓ {{Answer}}: {{OptionB}}</span>
  {{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
  <div class="why-block"><span class="why-label">Why: </span>{{Why}}</div>
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  {{#Tip}}<div class="tip-block">{{Tip}}</div>{{/Tip}}
</div>
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
    cloze_model = ap.Model(
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
<div class="front">
<div class="instruction">Fill in the missing form</div>
<div class="sentence">{{cloze:Text}}</div>
{{#Hint}}<div class="hint-row">💡 {{Hint}}</div>{{/Hint}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Fill in the missing form</div>
<div class="sentence">{{cloze:Text}}</div>
{{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
{{#Hint}}<div class="hint-row">💡 {{Hint}}</div>{{/Hint}}
</div>
{{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
{{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
''',
        }],
        css=css,
        model_type=ap.Model.CLOZE,
    )

    pro_model = ap.Model(
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
<div class="front">
<div class="instruction">Write a sentence using the target form</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
{{type:Sample}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Write a sentence in English</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
</div>
<hr id="answer">
<div class="answer-block">
  <div class="sample-label">Sample answer (compared to your input above)</div>
  <div class="sample-answer">{{type:Sample}}</div>
  {{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
  {{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  <div class="why-block"><span class="why-label">Why this works: </span>{{Why}}</div>
</div>
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # REVERSE PRODUCTION (AUTO) MODEL (v1)
    # Fields: Prompt | Sample | Why | Tags
    # Auto-generated from recognition rows for B2+ learners
    # ------------------------------------------------------------------
    rev_pro_model = ap.Model(
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
<div class="front">
<div class="instruction">Write a sentence in English</div>
<div class="sentence">{{Prompt}}</div>
{{type:Sample}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Write a sentence in English</div>
<div class="sentence">{{Prompt}}</div>
</div>
<hr id="answer">
<div class="answer-block">
  <div class="sample-label">Sample answer</div>
  <div class="sample-answer">{{type:Sample}}</div>
  {{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
  {{#Timeline}}<div class="timeline-box">{{Timeline}}</div>{{/Timeline}}
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  {{#Why}}<div class="why-block"><span class="why-label">Note: </span>{{Why}}</div>{{/Why}}
</div>
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
    img_model = ap.Model(
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
<div class="front">
<div class="instruction">Describe what you see in one English sentence</div>
{{#Image}}<div class="image-box">{{Image}}</div>{{/Image}}
{{^Image}}<div class="instruction">[image not available — caption: {{ImageQuery}}]</div>{{/Image}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">Describe what you see</div>
{{#Image}}<div class="image-box">{{Image}}</div>{{/Image}}
</div>
<hr id="answer">
<div class="answer-block">
  <div class="sentence">{{Caption}}</div>
  {{#Audio}}<div class="audio-row">{{Audio}}</div>{{/Audio}}
  <div class="target-badge">{{Form}}</div>
  <div class="why-block"><span class="why-label">Function: </span>{{Function}}</div>
  {{#Contrast}}<div class="tip-block"><span class="why-label">Contrast: </span>{{Contrast}}</div>{{/Contrast}}
  {{#IPA}}<details class="ipa-box"><summary class="ipa-key">🔊 IPA — tap to show</summary><span class="ipa-val">/{{IPA}}/</span></details>{{/IPA}}
  {{#Attribution}}<div class="hint-row" style="font-size:0.75em;opacity:0.7">📷 {{Attribution}}</div>{{/Attribution}}
</div>
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
        # Module 13 — bare keys are the catch-all "Other" L1 deck. Per-
        # language IDs follow at +10/+20/+30/+40 offsets to stay readable.
        ('13', 'rec'): 2056102301, ('13', 'con'): 2056102302, ('13', 'pro'): 2056102303,
        ('13-es', 'rec'): 2056102311, ('13-es', 'con'): 2056102312, ('13-es', 'pro'): 2056102313, ('13-es', 'clz'): 2056102314,
        ('13-fr', 'rec'): 2056102321, ('13-fr', 'con'): 2056102322, ('13-fr', 'pro'): 2056102323, ('13-fr', 'clz'): 2056102324,
        ('13-de', 'rec'): 2056102331, ('13-de', 'con'): 2056102332, ('13-de', 'pro'): 2056102333, ('13-de', 'clz'): 2056102334,
        ('13-ru', 'rec'): 2056102341, ('13-ru', 'con'): 2056102342, ('13-ru', 'pro'): 2056102343, ('13-ru', 'clz'): 2056102344,
        ('13-zh', 'rec'): 2056102351, ('13-zh', 'con'): 2056102352, ('13-zh', 'pro'): 2056102353, ('13-zh', 'clz'): 2056102354,
        ('13-ja', 'rec'): 2056102361, ('13-ja', 'con'): 2056102362, ('13-ja', 'pro'): 2056102363, ('13-ja', 'clz'): 2056102364,
        ('13-ko', 'rec'): 2056102371, ('13-ko', 'con'): 2056102372, ('13-ko', 'pro'): 2056102373, ('13-ko', 'clz'): 2056102374,
        ('13-ar', 'rec'): 2056102381, ('13-ar', 'con'): 2056102382, ('13-ar', 'pro'): 2056102383, ('13-ar', 'clz'): 2056102384,
        ('13-pt', 'rec'): 2056102391, ('13-pt', 'con'): 2056102392, ('13-pt', 'pro'): 2056102393, ('13-pt', 'clz'): 2056102394,
        ('13-nl', 'rec'): 2056102501, ('13-nl', 'con'): 2056102502, ('13-nl', 'pro'): 2056102503, ('13-nl', 'clz'): 2056102504,
        # Cloze decks (Tier 3)
        ('01', 'clz'): 2056101104, ('02', 'clz'): 2056101204, ('03', 'clz'): 2056101304,
        ('04', 'clz'): 2056101404, ('05', 'clz'): 2056101504, ('06', 'clz'): 2056101604,
        ('07', 'clz'): 2056101704, ('08', 'clz'): 2056101804, ('09', 'clz'): 2056101904,
        ('10', 'clz'): 2056102004, ('11', 'clz'): 2056102104, ('12', 'clz'): 2056102204,
        ('13', 'clz'): 2056102304,
        # Image-Cue deck (Tier 4)
        # ('14', 'img') deck-id retired in v2.7.0 — see MODULE_TAGS comment.
    }
    TYPE_SUFFIX = {'rec': '::1 - Recognition', 'con': '::2 - Contrast',
                   'pro': '::3 - Production', 'clz': '::4 - Cloze'}

    deck_description = f'English Verb System v{VERSION} — Comprehensive tense, aspect, and mood study. <a href="{CHANGELOG_URL}">Changelog</a>'
    
    decks = {}
    for (mod, typ), did in DECK_IDS.items():
        name = MODULE_NAMES[mod] + TYPE_SUFFIX[typ]
        decks[(mod, typ)] = ap.Deck(did, name, description=deck_description)

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

    # Helper: suppress redundant WhenNotToUse when it duplicates Contrast
    # (same authored sentence in both fields makes the back read as if the
    # same caveat is repeated twice — sloppy). We compute a SequenceMatcher
    # ratio after light normalization (lowercase, strip trailing punct,
    # collapse whitespace) and drop WhenNotToUse if it's >=0.85 similar
    # to Contrast — empirically catches the duplicates without sacrificing
    # genuinely-different notes.
    from difflib import SequenceMatcher as _SM
    def _norm_redundancy(s: str) -> str:
        return re.sub(r'\s+', ' ', s.lower().strip().rstrip('.;,'))
    def _dedupe_when_not(contrast: str, when_not: str) -> str:
        if not (contrast and when_not):
            return when_not
        c, w = _norm_redundancy(contrast), _norm_redundancy(when_not)
        if c == w:
            return ''
        # high-similarity (one is a near-superset of the other)
        if _SM(None, c, w).ratio() >= 0.85:
            return ''
        # one starts with the other's first ~30 chars (clear prefix dupes)
        head = w[:30]
        if head and (c.startswith(head) or w.startswith(c[:30])):
            return ''
        return when_not

    # ── Focus-span extractor (v3.0.0) ─────────────────────────────────
    # The Recognition prompt was historically ambiguous: "It could've
    # easily been worse." with answer "Connected Speech (Weak 'have')"
    # is unanswerable because the sentence has multiple verbs and
    # multiple grammatical features. The fix is NOT to reword the prompt
    # — it's to TELL the learner which span of the sentence is being
    # asked about, by wrapping that span in <mark>. The extractor below
    # is a deterministic regex pipeline keyed on the Label content;
    # 80%+ hit-rate is the target — for the unmatched edge cases
    # (T-flapping, Linking R, etc.) we fall back to no highlight and
    # the learner sees the bare sentence (current behaviour).
    def _extract_focus(sentence: str, label: str) -> str:
        """Return the substring of `sentence` to wrap in <mark>, or '' to
        leave the sentence unhighlighted. Pure regex, no NLP — every
        rule is keyed on the Label string."""
        L = label.lower()
        S = sentence
        # Pronunciation / phonology
        if 'connected speech' in L and 'have' in L:
            m = re.search(r"\b(could|would|should|might|may|must|will|shall)('ve|\s+have)\b", S, re.I)
            if m: return m.group(0)
            # Relaxed: allow one adverb between modal and have
            m = re.search(r"\b(could|would|should|might|may|must|will|shall)\s+\w+\s+have\b", S, re.I)
            if m: return m.group(0)
            m = re.search(r"\b(I|you|we|they|he|she|it|[A-Z]\w+)\s+(have|has|had)\b", S)
            if m: return m.group(0)
        if 'contraction' in L:
            # Pull the cue from the parenthetical (have/is/had/would)
            cue = ''
            mp = re.search(r'\(([^)]+)\)', label)
            if mp: cue = mp.group(1).lower()
            # Find ANY apostrophe-contracted token: I'd, She'd, We've, It's, There'd, He's, You've, etc.
            m = re.search(r"\b\w+'(?:ve|d|s|re|ll|m)\b", S)
            if m: return m.group(0)
            # Or n't contractions
            m = re.search(r"\b\w+n't\b", S)
            if m: return m.group(0)
        if 'reduction' in L:
            m = re.search(r'\(([a-z]+)\)', label, re.I)
            if m:
                tok = m.group(1).lower()
                expansions = {
                    'gonna': r'gonna|going\s+to', 'gotta': r'gotta|got\s+to|have\s+got\s+to',
                    'wanna': r'wanna|want\s+to', 'hafta': r'hafta|have\s+to',
                    'shoulda': r"shoulda|should(?:'ve|\s+have)",
                    'coulda': r"coulda|could(?:'ve|\s+have)",
                    'woulda': r"woulda|would(?:'ve|\s+have)",
                    'lemme': r'lemme|let\s+me', 'gimme': r'gimme|give\s+me',
                    'dunno': r"dunno|don'?t\s+know",
                    'kinda': r'kinda|kind\s+of', 'sorta': r'sorta|sort\s+of',
                }
                pat = expansions.get(tok, re.escape(tok))
                mm = re.search(rf'\b({pat})\b', S, re.I)
                if mm: return mm.group(0)
        if 'stress contrast' in L or 'modal weak form' in L or ('weak form' in L and re.search(r'[("]', label)):
            m = re.search(r'"([^"]+)"', label) or re.search(r'\(([\w\s]+)\)', label)
            if m:
                tok = re.sub(r'^\s*weak\s+', '', m.group(1).strip(), flags=re.I)
                mm = re.search(rf'\b{re.escape(tok)}\b', S, re.I)
                if mm: return mm.group(0)
        if 'contraction' in L and 'connected' not in L:
            m = re.search(r"\b\w+(?:'(?:ve|d|s|re|ll|m)|n't)\b", S)
            if m: return m.group(0)
        # Constructions
        if 'cleft' in L and 'pseudo' not in L and 'conditional' not in L:
            m = re.search(r"\b(?:It|It's)\s+(?:was|is|were|will be|has been|had been|only)?[\w\s'-]*?\b(?:who|that|which|whom)\b", S, re.I)
            if m: return m.group(0).rstrip()
        if 'cleft conditional' in L or "if it weren't" in L.lower():
            m = re.match(r"^If\s+it\s+(?:wasn't|weren't|hadn't\s+been|isn't|hasn't\s+been)\s+for\s+[\w\s'’]+,?", S, re.I)
            if m: return m.group(0).rstrip(',')
        if 'pseudo-cleft' in L or 'what-cleft' in L:
            m = re.search(r'\b(?:What|All|The\s+(?:thing|reason|most\s+\w+\s+thing|only\s+thing))\b[\w\s\']*?\b(?:is|was|are|were)\b', S, re.I)
            if m: return m.group(0)
        if 'reverse pseudo' in L:
            m = re.search(r'\b(?:is|was|are|were)\s+(?:what|the\s+\w+)\b', S, re.I)
            if m: return m.group(0)
        if 'existential there' in L:
            m = re.search(r'\bThere\s+(?:is|are|was|were|has\s+been|have\s+been|will\s+be|seems?\s+to\s+be|appears?\s+to\s+be)\b', S, re.I)
            if m: return m.group(0)
            # Inverted existential: "A cat is in the garden." → highlight "is in the"
            m = re.search(r'\b(is|are|was|were)\s+in\s+(?:the|a|an|my|your|his|her|its|our|their)\b', S, re.I)
            if m: return m.group(0)
        if 'possession existential' in L:
            # Bare possessive: "I have a car", "My brother has two cars"
            m = re.search(r'\b(have|has|had)\s+(?:a|an|the|some|no|two|three|four|five|several|many|few)\s+\w+', S, re.I)
            if m: return m.group(0)
            # Subject + have/has + N
            m = re.search(r'\b(I|you|we|they|he|she|it|[A-Z]\w+)\s+(have|has|had)\b', S)
            if m: return m.group(0)
            # Mis-tagged "There" sentence shadowed as possessive
            m = re.search(r'\bThere\s+(?:is|are|was|were)\b', S, re.I)
            if m: return m.group(0)
        if 'causative' in L:
            m = re.search(r'\b(had|have|has|got|get|gets|made|make|let|help|helped)\b\s+\w+\s+(?:\w+ed|\w+en|\w+|to\s+\w+)', S, re.I)
            if m: return m.group(0)
            m = re.search(r'\b(had|have|has|got|get|gets|made|make|let|help|helped)\b', S, re.I)
            if m: return m.group(0)
        if 'tag question' in L:
            m = re.search(r",\s+\w+(?:n't)?\s+\w+\?$", S)
            if m: return m.group(0)
        if 'hedging' in L:
            m = re.search(r'\b(?:it\s+could\s+be\s+argued|it\s+might\s+be\s+argued|it\s+seems\s+that|it\s+appears\s+that)\b', S, re.I)
            if m: return m.group(0)
            m = re.search(r'\b(may|might|could|would|seems?\s+to|appears?\s+to|tends?\s+to)\b', S, re.I)
            if m: return m.group(0)
        if 'inversion' in L:
            # Negative inversion: "Never have I…", "Rarely does she…"
            m = re.match(r'^(Never|Rarely|Hardly|Seldom|Not\s+only|Little|No\s+sooner|Only|Under\s+no|Nowhere|Scarcely|Barely)\b.*?\b(?:do|does|did|have|has|had|is|are|was|were|can|could|will|would|may|might|must|should)\b', S, re.I)
            if m: return m.group(0)
            # Locative inversion: "Down the road came a mysterious figure"
            # Highlight the leading PP + inverted verb.
            m = re.match(r'^(Down|Up|In|Into|On|Onto|Out|Off|Across|Around|Behind|Before|Above|Below|Among|Beside|Beyond|Through|Under|Over)\b[\w\s\'.]+?\b(?:came|come|stood|stands|sat|sits|lay|lies|hung|hangs|appeared|appears|emerged|rose|rises|ran|runs|flew|flies|walked|walks)\b', S, re.I)
            if m: return m.group(0)
            # Comparative/degree inversion: "So great was her talent that…",
            # "Such was the impact that…"
            m = re.match(r'^(So|Such)\b[\w\s]+?\b(?:was|were|is|are|had|has|did|does|do)\b', S, re.I)
            if m: return m.group(0)
        if 'emphatic do' in L:
            # Highlight emphatic do/does/did + bare verb: "I DO like…",
            # "She DID say…", "They DO understand…"
            m = re.search(r'\b(do|does|did)\s+\w+\b', S, re.I)
            if m: return m.group(0)

        # Verb-form rows (the 707 majority): highlight the matching verb
        # cluster so the learner sees exactly which token sequence is
        # being asked about. Patterns are keyed on the Label and matched
        # via a flexible verb-cluster regex.
        AUX = r'(?:am|is|are|was|were|have|has|had|do|does|did|will|would|shall|should|can|could|may|might|must|be|been|being|going)'
        # Map standard tense Labels → verb-cluster pattern
        # Each pattern includes the optional "n't" / "not" + main verb in
        # appropriate form (V/Ving/Ven). Pattern goal: greedy enough to
        # catch the whole construction, narrow enough to skip subject NPs.
        FORM_PATS = [
            ('present perfect continuous',     r"\b(?:has|have)(?:n't)?\s+been\s+\w+ing\b"),
            ('past perfect continuous',        r"\bhad(?:n't)?\s+been\s+\w+ing\b"),
            ('future perfect continuous',      r"\bwill(?:\s+not|\s+have(?:\s+been)?\s+\w+ing|\s+have\s+been\s+\w+ing)\b|\bwill\s+have\s+been\s+\w+ing\b"),
            ('conditional perfect continuous', r"\bwould(?:n't)?\s+have\s+been\s+\w+ing\b"),
            ('present perfect',                r"\b(?:has|have)(?:n't)?\s+(?:been\s+)?\w+(?:ed|en|own|ung|ought|aught|oken|orne|orn|one)\b|\b(?:has|have)(?:n't)?\s+\w+\b(?=\s|[\.,?!])"),
            ('past perfect',                   r"\bhad(?:n't)?\s+\w+(?:ed|en|own|ung|ought|aught|oken|orne|one)\b"),
            ('future perfect',                 r"\bwill\s+have\s+\w+(?:ed|en|own|ung|ought|oken|one)\b"),
            ('conditional perfect',            r"\bwould(?:n't)?\s+have\s+\w+(?:ed|en|own|ung|ought|oken|one)\b"),
            ('present continuous',             r"\b(?:am|is|are)(?:n't)?\s+\w+ing\b|\b(?:'m|'re|'s)\s+\w+ing\b"),
            ('past continuous',                r"\b(?:was|were)(?:n't)?\s+\w+ing\b"),
            ('future continuous',              r"\bwill\s+be\s+\w+ing\b"),
            ('conditional continuous',         r"\bwould\s+be\s+\w+ing\b"),
            ('future simple',                  r"\bwill(?:\s+not|n't)?\s+\w+\b|\b'll\s+\w+\b"),
            ('be going to',                    r"\b(?:am|is|are|was|were)(?:n't)?\s+going\s+to\s+\w+\b|\b(?:'m|'re|'s)\s+going\s+to\s+\w+\b"),
            ('future going to',                r"\b(?:am|is|are)(?:n't)?\s+going\s+to\s+\w+\b|\b(?:'m|'re|'s)\s+going\s+to\s+\w+\b"),
            ('past simple',                    r"\b(?:did(?:n't)?\s+\w+|was|were|wasn't|weren't|\w+ed)\b|\b\w+(?:ought|ame|ent|ot|ound|ade|ave|ought|ought|aw|ook|nown|hought|elt|ept|elt|aught|ame|ave)\b"),
            ('present simple',                 r"\b(?:do(?:n't)?|does(?:n't)?)\s+\w+\b|\b\w+s\b(?=\s|[\.,?!])"),
            ('conditional',                    r"\bwould(?:n't)?\s+\w+\b"),
            ('subjunctive',                    r"\b(?:were|be|have|do)(?:\s+not)?\s+\w+\b"),
            ('passive',                        r"\b(?:am|is|are|was|were|been|being|be)\s+\w+(?:ed|en|own|ung|ought|aught|oken|orne|one)(?:\s+by\s+\w+)?\b"),
            ('imperative',                     r"^[A-Z]\w+\b"),
            ('used to',                        r"\bused\s+to\s+\w+\b"),
            ('would (habitual)',               r"\bwould\s+\w+\b"),
            ('modal',                          r"\b(?:can(?:'t|not)?|could(?:n't)?|may|might|must(?:n't)?|should(?:n't)?|ought\s+to|need(?:n't)?|dare(?:n't)?|have\s+to|has\s+to|had\s+to)\s+\w+\b"),
            ('zero conditional',               r"\bif\s+[\w\s]+,\s*[\w\s]+"),
            ('first conditional',              r"\bif\s+[\w\s]+,\s*[\w\s]+will\s+\w+"),
            ('second conditional',             r"\bif\s+[\w\s]+,\s*[\w\s]+would\s+\w+"),
            ('third conditional',              r"\bif\s+[\w\s]+had\s+[\w\s]+,\s*[\w\s]+would\s+have\s+\w+"),
            ('mixed conditional',              r"\bif\s+[\w\s]+,\s*[\w\s]+would\s+\w+"),
            ('reported speech',                r"\b(?:said|told|asked|claimed|reported|mentioned|explained)\b\s+(?:that\s+)?[\w\s]+\b"),
            ('gerund',                         r"\b\w+ing\b"),
            ('infinitive',                     r"\bto\s+\w+\b"),
            ('participle',                     r"\b\w+(?:ed|ing|en)\b"),
        ]
        # Try the most-specific Labels first (longest match wins).
        # Sort patterns by Label length desc so 'present perfect continuous'
        # is tried before 'present perfect'.
        for key, pat in sorted(FORM_PATS, key=lambda x: -len(x[0])):
            if key in L:
                m = re.search(pat, S, re.I)
                if m:
                    return m.group(0)
        return ''

    def _focused_html(sentence: str, label: str) -> str:
        """Return Sentence with the focus span wrapped in <mark>. If no
        focus is extractable, returns the bare sentence (no highlight)."""
        focus = _extract_focus(sentence, label)
        if not focus:
            return sentence
        # Replace ONLY the first occurrence so we never double-mark.
        # re.escape so any special chars in focus are taken literally.
        pat = re.compile(re.escape(focus), re.I)
        return pat.sub(
            lambda m: f'<mark class="focus">{m.group(0)}</mark>',
            sentence, count=1,
        )

    # ── Grammatical category classifier (v3.1.0) ─────────────────────
    # English verb-system Labels conflate tense, aspect, mood, voice,
    # modality, and various sentence-level constructions. Premium
    # pedagogy demands precision: we classify each Label into one of
    # 12 grammatical categories so the prompt and the curriculum
    # progression are honest.
    #
    # Pedagogical sequence (CEFR-aligned):
    #   FOUNDATION        →  tense-aspect (the 12-cell grid)
    #   FUTURE EXPRESSION →  periphrastic-future, modal (will/be going to)
    #   PAST EXPRESSION   →  periphrastic-past-habit (used to, would)
    #   ADVANCED INDIC.   →  voice (passives), conditional
    #   NON-INDICATIVE    →  mood (subjunctive, imperative)
    #   NON-FINITE        →  non-finite (gerund, infinitive, participle)
    #   LEXICAL           →  phrasal-verb
    #   DISCOURSE         →  construction (cleft, existential, causative,
    #                        tag question, hedging, inversion, etc.)
    #   META              →  reported-speech, modal (other), phonology
    #
    # The 12-cell tense×aspect grid is the FIRST thing every learner
    # masters — everything else builds on it. Module sub-decks (01–13)
    # already roughly track this curriculum; this classifier surfaces
    # the same taxonomy in the prompt itself.
    _CATPATS = [
        # Order matters: more specific first. Each rule is a (pattern, category).
        (r'connected speech|reduction|contraction|stress|linking|t[- ]flap|weak form|schwa|elision|intonation|assimilation|silent letter|word stress|sentence stress|prosody|rhythm', 'phonology'),
        (r'phrasal verb|particle verb', 'phrasal-verb'),
        (r'reported speech|indirect speech|direct speech|backshift', 'reported-speech'),
        (r'cleft|existential|causative|tag question|hedging|inversion|fronting|catenative|emphatic|exclamative|pseudo-cleft|reverse pseudo|response form|comment clause|extraposition|locative|comparative.*invers|degree.*invers|so.*such', 'construction'),
        (r'gerund|infinitive|participle', 'non-finite'),
        (r'subjunctive|imperative', 'mood'),
        (r'passive|middle voice', 'voice'),
        (r'conditional|if[- ]clause|mixed cond|inverted cond', 'conditional'),
        (r'used to|would \(habitual\)|habitual past', 'periphrastic-past-habit'),
        (r'going to|be about to|be to\b|be due to|be on the verge', 'periphrastic-future'),
        (r"\bmodal\b|\bmust\b|\bshould\b|\bought\b|\bneed\b|\bdare\b|\bcan\b|\bcould\b|\bmay\b|\bmight\b|have to|has to|had to", 'modal'),
        # Future Simple uses 'will' as future marker — that's tense-aspect, NOT modal.
        # Anything else falls through to the canonical 12-cell grid.
    ]
    _CATPATS = [(re.compile(p, re.I), cat) for p, cat in _CATPATS]
    def _category_for(label: str) -> str:
        L = label.strip()
        # Future tenses are tense-aspect, not modal:
        if re.search(r'^future (?:simple|continuous|perfect)', L, re.I):
            return 'tense-aspect'
        for pat, cat in _CATPATS:
            if pat.search(L):
                return cat
        return 'tense-aspect'  # default: canonical grid

    # Honest, category-specific prompts. The phrase always names exactly
    # what kind of grammatical answer is expected — no more "Name this
    # verb form" when the answer is actually "Connected Speech".
    _CAT_PROMPTS_HIGHLIGHTED = {
        'tense-aspect':            'Identify the highlighted tense + aspect',
        'modal':                   'Identify the highlighted modal',
        'voice':                   'Identify the highlighted passive form',
        'mood':                    'Identify the highlighted mood',
        'conditional':             'Identify the highlighted conditional type',
        'non-finite':              'Identify the highlighted non-finite form',
        'periphrastic-future':     'Identify the highlighted future construction',
        'periphrastic-past-habit': 'Identify the highlighted past-habit construction',
        'construction':            'Identify the highlighted construction',
        'phrasal-verb':            'Identify the highlighted phrasal verb',
        'reported-speech':         'Identify the highlighted reported-speech form',
        'phonology':               'Identify the highlighted pronunciation feature',
    }
    _CAT_PROMPTS_BARE = {
        'tense-aspect':            'Name this tense + aspect',
        'modal':                   'Name this modal',
        'voice':                   'Name this passive form',
        'mood':                    'Name this mood',
        'conditional':             'Name this conditional type',
        'non-finite':              'Name this non-finite form',
        'periphrastic-future':     'Name this future construction',
        'periphrastic-past-habit': 'Name this past-habit construction',
        'construction':            'Name this construction',
        'phrasal-verb':            'Name this phrasal verb',
        'reported-speech':         'Name this reported-speech form',
        'phonology':               'Name this pronunciation feature',
    }
    def _prompt_for(focused_html: str, label: str, sentence: str) -> str:
        """Always-honest instruction: announces both the category of the
        expected answer AND whether a span is highlighted."""
        cat = _category_for(label)
        if '<mark' in focused_html:
            return _CAT_PROMPTS_HIGHLIGHTED[cat]
        return _CAT_PROMPTS_BARE[cat]

    # Recognition
    _, rec_rows = load_tsv('conjugations_recognition.txt')
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | WhenNotToUse | Tags
    suppressed_when_not = 0
    focus_hits = focus_misses = 0
    for row in rec_rows:
        if len(row) < 9:
            row += [''] * (9 - len(row))
        mods = row_modules(row[8])
        audio_f, ipa_f, tl_f = media_for_sentence(row[0], ipa_index, timeline_index, label=row[1])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        # Drop WhenNotToUse when it duplicates Contrast
        deduped_when = _dedupe_when_not(row[6], row[7])
        if deduped_when != row[7]:
            suppressed_when_not += 1
        # Wrap the targeted span in <mark> when extractable. Pick the
        # prompt CONDITIONALLY: 'Identify the highlighted form' only
        # when there IS a highlight; otherwise a category-appropriate
        # 'Name this verb form / pronunciation feature / construction'
        # so the question is always honest about what's on screen.
        focused = _focused_html(row[0], row[1])
        if focused != row[0]:
            focus_hits += 1
        else:
            focus_misses += 1
        prompt_text = _prompt_for(focused, row[1], row[0])
        category = _category_for(row[1])
        row_for_note = list(row)
        row_for_note[7] = deduped_when
        # Recognition fields: Sentence | Label | Aspect | Formula | MainUse |
        #   QuickCue | Contrast | WhenNotToUse | Tags | Audio | IPA |
        #   Timeline | FocusedSentence | Prompt | Category
        note = ap.Note(
            model=rec_model,
            fields=row_for_note[:9] + [audio_f, ipa_f, tl_f, focused, prompt_text, category],
            tags=row[8].split() + [f'cat:{category}'],
        )
        for _mod in mods:
            decks[(_mod, 'rec')].add_note(note)
        counts['rec'] += 1
    if suppressed_when_not:
        print(f'  [dedupe] suppressed {suppressed_when_not} WhenNotToUse '
              f'fields that duplicated Contrast')
    print(f'  [focus] highlighted span: {focus_hits} cards, '
          f'no highlight (whole sentence visible): {focus_misses} cards')

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
        rev_pro_note = ap.Note(
            model=rev_pro_model,
            fields=[sentence, sentence, formula, tags_str, audio_f, ipa_f, tl_f],
            tags=tags_set.split() if isinstance(tags_set, str) else list(tags_set),
        )
        for _mod in mods:
            decks[(_mod, 'pro')].add_note(rev_pro_note)
        rev_pro_count += 1
        existing_samples.add(sentence)

    # Contrast
    _, con_rows = load_tsv('conjugations_contrast.txt')
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    spot_error_count = 0
    for row in con_rows:
        if len(row) < 7:
            row += [''] * (7 - len(row))
        mods = row_modules(row[6])
        # For contrast, the "label" we map to a timeline is the Answer (column 3)
        audio_f, ipa_f, tl_f = media_for_sentence(row[0], ipa_index, timeline_index, label=row[3])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        
        # Create regular contrast note
        note = ap.Note(
            model=con_model,
            fields=row[:7] + [audio_f, ipa_f, tl_f],
            tags=row[6].split(),
        )
        for _mod in mods:
            decks[(_mod, 'con')].add_note(note)
        counts['con'] += 1
        
        # Create spot-the-error note if row has error-correction, l1-interference, or spot-the-error tag
        tags_set = set(row[6].split())
        error_tags = {'error-correction', 'l1-interference', 'spot-the-error'}
        if tags_set & error_tags:
            spot_note = ap.Note(
                model=spot_error_model,
                fields=row[:7] + [audio_f, ipa_f, tl_f],
                tags=row[6].split(),
            )
            for _mod in mods:
                decks[(_mod, 'con')].add_note(spot_note)
            spot_error_count += 1

    # Production
    _, pro_rows = load_tsv('conjugations_production.txt')
    # Fields: Prompt | Target | Aspect | Sample | Why | Tags
    for row in pro_rows:
        if len(row) < 6:
            row += [''] * (6 - len(row))
        mods = row_modules(row[5])
        # For production, audio/IPA come from the Sample (column 3); timeline from Target (column 1).
        audio_f, ipa_f, tl_f = media_for_sentence(row[3], ipa_index, timeline_index, label=row[1])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        note = ap.Note(
            model=pro_model,
            fields=row[:6] + [audio_f, ipa_f, tl_f],
            tags=row[5].split(),
        )
        for _mod in mods:
            decks[(_mod, 'pro')].add_note(note)
        counts['pro'] += 1

    # Cloze (Tier 3)
    counts['clz'] = 0
    cloze_path = Path('conjugations_cloze.txt')
    if cloze_path.exists():
        _, cloze_rows = load_tsv(str(cloze_path))
        for row in cloze_rows:
            if len(row) < 3:
                row += [''] * (3 - len(row))
            mods = row_modules(row[2])
            # For cloze, the spoken sentence is the cloze Text with the
            # {{c1::…}} markers stripped — that's the natural English audio.
            spoken = re.sub(r'\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}', r'\1', row[0])
            audio_f, ipa_f, tl_f = media_for_sentence(spoken, ipa_index, timeline_index, label='')
            if audio_f: media_counts['audio'] += 1
            if ipa_f: media_counts['ipa'] += 1
            note = ap.Note(
                model=cloze_model,
                fields=row[:3] + [audio_f, ipa_f, tl_f],
                tags=row[2].split(),
            )
            for _mod in mods:
                decks[(_mod, 'clz')].add_note(note)
            counts['clz'] += 1

    # Image-Cue (Module 14) was REMOVED in v2.7.0 — semantically random
    # Wikimedia matches actively misled learners. See MODULE_TAGS comment.
    img_count = 0
    if False and IMAGE_TSV.exists():
        img_index = load_image_index()
        _, img_rows = load_tsv(str(IMAGE_TSV))
        for row in img_rows:
            if len(row) < 6:
                row += [''] * (6 - len(row))
            tags_str = row[5]
            # Image cards always live in module 14, never per-L1 — even if
            # an l1-* tag slipped onto an image row.
            mods = ['14']
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
            note = ap.Note(
                model=img_model,
                fields=[row[0], caption, row[2], row[3], row[4], tags_str,
                        img_field, audio_f, ipa_f, attribution_field],
                tags=tags_str.split(),
            )
            for _mod in mods:
                decks[(_mod, 'img')].add_note(note)
            img_count += 1

    out = 'english_verb_system_anki.apkg'
    package = ap.Package(list(decks.values()))
    package.media_files = media_files
    package.write_to_file(out)

    # v2.0+: anki_packager (./anki_packager.py) builds the .apkg directly via
    # `anki.Collection`, so it's already in modern format with the FSRS
    # preset bound to every deck. No post-processing repackage step needed.

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
