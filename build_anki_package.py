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

VERSION = '3.2.12'
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
    # ── v3.2.0 CURRICULUM-FIRST DECK STRUCTURE ───────────────────────
    # Replaces the legacy 12 thematic modules with a sequenced
    # curriculum derived directly from the grammatical category
    # taxonomy (see _category_for() in build_decks). Order matters:
    # Foundation comes FIRST — every learner masters the canonical
    # 12-cell tense+aspect grid before unlocking the layered modules.
    # All non-Foundation, non-L1 decks ship with the "opt-in" preset
    # (0 new cards/day) so the user explicitly enables each layer
    # only when they're ready. This pedagogy mirrors how Cambridge,
    # Oxford, and Pearson sequence English-as-a-Foreign-Language
    # syllabi (CEFR A1→C2).
    '00': 'English Verb System::00 - Foundation',
    '01': 'English Verb System::01 - Periphrastic Futures',
    '02': 'English Verb System::02 - Past Habits',
    '03': 'English Verb System::03 - Modal Verbs',
    '04': 'English Verb System::04 - Conditionals',
    '05': 'English Verb System::05 - Passive Voice',
    '06': 'English Verb System::06 - Mood',
    '07': 'English Verb System::07 - Non-Finite Forms',
    '08': 'English Verb System::08 - Reported Speech',
    '09': 'English Verb System::09 - Phrasal Verbs',
    '10': 'English Verb System::10 - Discourse Constructions',
    '11': 'English Verb System::11 - Phonology & Connected Speech',
    '12': 'English Verb System::12 - Transformation & Register',
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

# v3.2.0: maps every grammatical category (see _category_for) to a
# numeric module code. The order in MODULE_NAMES IS the curriculum
# sequence — Foundation first, then layers in pedagogically motivated
# order (futures → past habits → modals → conditionals → passive →
# mood → non-finite → reported speech → phrasal verbs → discourse
# constructions → phonology → transformation/register).
CATEGORY_MODULE = {
    'tense-aspect':            '00',  # Foundation: the 12-cell grid
    'aux-form':                '00',  # Aux choice IS tense+aspect (am/is/are/has/etc.)
    'periphrastic-future':     '01',
    'periphrastic-past-habit': '02',
    'modal':                   '03',
    'conditional':             '04',
    'voice':                   '05',
    'mood':                    '06',
    'non-finite':              '07',
    'reported-speech':         '08',
    'phrasal-verb':            '09',
    'construction':            '10',
    'phonology':               '11',
    'transformation':          '12',
    'register':                '12',
}


def row_modules(tags_str, category=None):
    """Returns ALL deck codes a row should be added to.

    L1-interference cards (cards specifically about how a particular
    L1 trips its speakers up) always route to per-language sub-decks
    of '13 - L1 Interference', regardless of the card's grammatical
    category. This lets a Russian speaker, say, drill ONLY the
    contrasts that catch Russian speakers, separately from their main
    curriculum progression.

    Non-L1 cards route purely by grammatical category: Foundation
    (12-cell grid), then the 12 layered modules in pedagogical order.
    """
    tags = set(tags_str.split())
    if 'l1-interference' in tags or any(t in L1_LANG_SUFFIX for t in tags):
        mods = ['13' + L1_LANG_SUFFIX[t] for t in tags if t in L1_LANG_SUFFIX]
        return mods if mods else ['13']
    # Pure category-routing for non-L1 cards. The category is supplied
    # by the caller (computed via _category_for() on Label/Answer/Target/
    # tags), guaranteeing alignment with the prompt-classification.
    if category is not None:
        return [CATEGORY_MODULE.get(category, '00')]
    # Fallback for code paths that don't have a category yet (legacy):
    # everything goes to Foundation.
    return ['00']


def row_module(tags_str, category=None):
    """Returns the single primary deck code for a row (legacy compatibility).

    Same behaviour as row_modules()[0]. Kept because some non-deck
    code paths (e.g. tag generation, statistics) still call this.
    """
    return row_modules(tags_str, category=category)[0]


# ── Tier-2 media plumbing ───────────────────────────────────────────────
MEDIA_AUDIO_DIR = Path('media/audio')
MEDIA_IPA_INDEX = Path('media/ipa_index.json')
MEDIA_TIMELINES_DIR = Path('media/timelines')
MEDIA_TIMELINES_INDEX = Path('media/timelines_index.json')
MEDIA_IMAGES_DIR = Path('media/images')
MEDIA_IMAGES_INDEX = Path('media/images_index.json')
IMAGE_TSV = Path('conjugations_image.txt')
_BLANK_RE = re.compile(r'_{3,}|\[blank\]|\(blank\)', re.IGNORECASE)
_CHOICE_ANNOTATION_RE = re.compile(r'\s*\([^)]*\)\s*$')


def _sentence_hash(text):
    return hashlib.sha1((text or '').strip().encode('utf-8')).hexdigest()[:12]


def _strip_choice_annotation(text):
    return _CHOICE_ANNOTATION_RE.sub('', (text or '').strip()).strip()


def spoken_sentence(sentence, *, option_a='', option_b='', answer=''):
    """Resolve authored prompts to natural spoken text for media lookup."""
    spoken = (sentence or '').strip()
    if not spoken:
        return ''
    spoken = re.sub(r'\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}', r'\1', spoken)
    if _BLANK_RE.search(spoken):
        fill = (answer or '').strip()
        if fill == (option_a or '').strip():
            fill = option_a
        elif fill == (option_b or '').strip():
            fill = option_b
        fill = _strip_choice_annotation(fill)
        if fill:
            spoken = _BLANK_RE.sub(fill, spoken)
    return spoken


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


def media_for_sentence(sentence, ipa_index, timeline_index, label='', option_a='', option_b='', answer=''):
    """Return (audio_field, ipa_field, timeline_field) for a sentence.
    Audio field uses Anki's [sound:filename.mp3] tag; timeline uses <img>."""
    spoken = spoken_sentence(sentence, option_a=option_a, option_b=option_b, answer=answer)
    h = _sentence_hash(spoken)
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
        2056102016,  # bumped (was 2056102005): added Instruction +
                     # Category fields. v3.1.1 brings the v3.1.0
                     # taxonomy from Recognition to Contrast cards too,
                     # so the prompt names the EXPECTED answer category
                     # ("Which tense + aspect fits…?" vs "Which modal
                     # fits…?") instead of the muddled "Which form
                     # fits this sentence?".
        'Verb System · Contrast (v3)',
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
            {'name': 'Instruction'},  # category-aware: "Which X fits this sentence?"
            {'name': 'Category'},     # one of 15 grammatical categories
        ],
        templates=[{
            'name': 'Contrast Card',
            'qfmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
<div class="sentence">{{Sentence}}</div>
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
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
        2056102017,  # bumped (was 2056102007): added Instruction +
                     # Category fields. v3.1.1 makes the cloze prompt
                     # name the expected answer category — e.g. "Fill
                     # in the missing tense + aspect" instead of the
                     # generic "Fill in the missing form".
        'Verb System · Cloze (v2)',
        fields=[
            {'name': 'Text'},
            {'name': 'Hint'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
            {'name': 'Instruction'},  # category-aware: "Fill in the missing X"
            {'name': 'Category'},
        ],
        templates=[{
            'name': 'Cloze Card',
            'qfmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
<div class="sentence">{{cloze:Text}}</div>
{{#Hint}}<div class="hint-row">💡 {{Hint}}</div>{{/Hint}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
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
        2056102018,  # bumped (was 2056102011): added Instruction +
                     # Category fields. v3.1.1 makes the production
                     # prompt name the expected answer category — e.g.
                     # "Write a sentence using the target tense + aspect"
                     # vs "...using the target modal" vs "...using the
                     # target conditional type".
        'Verb System · Production (v4)',
        fields=[
            {'name': 'Prompt'},        # the sentence-stem (NL or schema task)
            {'name': 'Target'},
            {'name': 'Aspect'},
            {'name': 'Sample'},
            {'name': 'Why'},
            {'name': 'Tags'},
            {'name': 'Audio'},
            {'name': 'IPA'},
            {'name': 'Timeline'},
            {'name': 'Instruction'},   # category-aware: "Write a sentence using the target X"
            {'name': 'Category'},
        ],
        templates=[{
            'name': 'Production Card',
            'qfmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
{{type:Sample}}
</div>
''',
            'afmt': '''
<div class="front">
<div class="instruction">{{Instruction}}</div>
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
        # v3.2.0: Foundation deck (12-cell tense+aspect grid) at code '00'.
        # Every other module ('01'..'12') is a layered curriculum unit
        # that ships opted-out (0 new cards/day) until the user enables it.
        ('00', 'rec'): 2056101001, ('00', 'con'): 2056101002, ('00', 'pro'): 2056101003, ('00', 'clz'): 2056101004,
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
        # ── Verb-cluster regexes (rebuilt v3.2.9) ──────────────────────
        # Every multi-word verb cluster needs to behave correctly across
        # FOUR clause shapes:
        #   (a) declarative positive: "She has been working."
        #   (b) declarative negative: "She has not been working." / "...hasn't been..."
        #   (c) yes/no question:      "Has she been working?"
        #   (d) wh-question:          "What has she been working on?"
        # The auxiliary chain stays contiguous in (a) and (b); in (c) and
        # (d) the SUBJECT is inserted between the first auxiliary and the
        # rest. Rather than try to skip the subject (which causes greedy
        # over-matching on long subjects), we explicitly allow ONE
        # optional intervening NP token (`(?:\s+\w+)?`) between the
        # leading auxiliary and the rest of the cluster. This covers the
        # 99% case (single-word subject pronouns: he/she/it/you/we/they/I)
        # without false positives.
        #
        # `(?:\s+not|n't)?` slots into the natural negation position of
        # each tense so the negation marker is part of the highlight, not
        # a terminator. The previous patterns (v3.0–v3.2.8) used
        # `\bwill(?:\s+not|...)\b` as alternation, which made `will not`
        # a complete match on its own and stopped before the actual verb.
        SUBJ = r"(?:\s+(?:I|you|we|they|he|she|it|[A-Z]\w+))?"  # optional inverted subject
        NEG  = r"(?:\s+not|n't)?"                               # optional negation
        # Curated irregular past participles. Recognising these by literal
        # tokens (rather than by suffix heuristics that miss "lost", "left",
        # "found", "bought", "gone", "seen", "done", "made") is essential
        # for the perfect-tense highlighters to grab the WHOLE cluster.
        IRREG_PP = (r"(?:been|had|done|gone|seen|made|said|got|gotten|known|grown|"
                    r"thrown|drawn|flown|shown|blown|driven|written|ridden|risen|"
                    r"chosen|frozen|broken|spoken|stolen|woken|bitten|hidden|"
                    r"forbidden|fallen|eaten|beaten|forgotten|taken|shaken|mistaken|"
                    r"lost|left|kept|slept|felt|meant|brought|bought|caught|fought|"
                    r"taught|sought|thought|sent|spent|built|burnt|dealt|dreamt|"
                    r"learnt|leant|swept|crept|bent|lent|put|cut|hit|set|let|read|"
                    r"shut|hurt|cost|spread|burst|cast|quit|fit|spat|swum|run|come|"
                    r"become|begun|drunk|sung|rung|stung|sunk|stuck|won|held|fled|"
                    r"led|fed|bred|shed|paid|laid|said|made|met|sat|bought|wept|"
                    r"told|sold|found|wound|bound|ground|stood|understood|withdrawn|"
                    r"undertaken|overcome|been)")
        # Built from a list-then-or for clarity; ed/d-suffixed regulars are
        # handled by the generic `\w+ed` alternative.
        FORM_PATS = [
            # Perfect tenses with contraction support: 've = have, 's = has,
            # 'd = had/would (disambiguated by following form). The
            # contracted form attaches to the preceding subject token, so
            # the highlight needs to cover "subject + 've + ..." rather
            # than start at "have".
            ('present perfect continuous',     rf"\b(?:has|have|haven't|hasn't){NEG}{SUBJ}\s+been\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'(?:ve|s)\s+(?:not\s+)?been\s+\w+ing\b"),
            ('past perfect continuous',        rf"\bhad{NEG}{SUBJ}\s+been\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'d\s+(?:not\s+)?been\s+\w+ing\b"),
            ('future perfect continuous',      rf"\bwill{NEG}{SUBJ}{NEG}\s+have\s+been\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'ll\s+(?:not\s+)?have\s+been\s+\w+ing\b"),
            ('conditional perfect continuous', rf"\bwould{NEG}{SUBJ}{NEG}\s+have\s+been\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'d\s+(?:not\s+)?have\s+been\s+\w+ing\b"),
            ('present perfect',                rf"\b(?:has|have|haven't|hasn't){NEG}{SUBJ}{NEG}\s+(?:been\s+)?(?:already\s+|just\s+|never\s+|ever\s+|still\s+|yet\s+|recently\s+|lately\s+)?(?:{IRREG_PP}|\w+ed)\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'(?:ve|s)\s+(?:not\s+)?(?:already\s+|just\s+|never\s+|ever\s+|still\s+|yet\s+|recently\s+|lately\s+)?(?:been\s+)?(?:{IRREG_PP}|\w+ed)\b"),
            ('past perfect',                   rf"\bhad{NEG}{SUBJ}{NEG}\s+(?:already\s+|just\s+)?(?:{IRREG_PP}|\w+ed)\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'d\s+(?:not\s+)?(?:already\s+|just\s+)?(?:{IRREG_PP}|\w+ed)\b"),
            ('future perfect',                 rf"\bwill{NEG}{SUBJ}{NEG}\s+have\s+(?:{IRREG_PP}|\w+ed)\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'ll\s+(?:not\s+)?have\s+(?:{IRREG_PP}|\w+ed)\b"),
            ('conditional perfect',            rf"\bwould{NEG}{SUBJ}{NEG}\s+have\s+(?:{IRREG_PP}|\w+ed)\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'d\s+(?:not\s+)?have\s+(?:{IRREG_PP}|\w+ed)\b"),
            ('present continuous',             rf"\b(?:am|is|are){NEG}{SUBJ}{NEG}\s+(?:always\s+|forever\s+|constantly\s+|continually\s+)?\w+ing\b|\b(?:'m|'re|'s)\s+(?:always\s+|forever\s+|constantly\s+|continually\s+)?\w+ing\b"),
            ('past continuous',                rf"\b(?:was|were){NEG}{SUBJ}{NEG}\s+\w+ing\b"),
            ('future continuous',              rf"\bwill{NEG}{SUBJ}{NEG}\s+be\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'ll\s+(?:not\s+)?be\s+\w+ing\b"),
            ('conditional continuous',         rf"\bwould{NEG}{SUBJ}{NEG}\s+be\s+\w+ing\b"
                                               + rf"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)'d\s+(?:not\s+)?be\s+\w+ing\b"),
            # Future simple: will/'ll + (not)? + bare verb. We require a
            # main verb after the optional negation so "will not" alone
            # never matches — it must extend to the verb that follows.
            ('future simple',                  rf"\bwill{NEG}\s+\w+\b|\b'll\s+\w+\b"),
            ('be going to',                    rf"\b(?:am|is|are|was|were){NEG}{SUBJ}{NEG}\s+going\s+to\s+\w+\b|\b(?:'m|'re|'s)\s+going\s+to\s+\w+\b"),
            ('future going to',                rf"\b(?:am|is|are){NEG}{SUBJ}{NEG}\s+going\s+to\s+\w+\b|\b(?:'m|'re|'s)\s+going\s+to\s+\w+\b"),
            # Past simple: prefer the precise auxiliary forms first; the
            # bare `\w+ed` fallback is intentionally LAST so it only fires
            # if no auxiliary cluster is present (irregular past forms
            # like "went", "saw", "took" are caught by the irregular set).
            # Past simple: cluster matchers first (most specific), then a
            # subject + irregular-past fallback, then a bare-V-ed fallback.
            ('past simple',                    r"\bdid(?:n't|\s+not)?" + SUBJ + r"\s+\w+\b"
                                               + r"|\b(?:wasn't|weren't|was\s+not|were\s+not|was|were)\s+\w+\b"
                                               + r"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)\s+"
                                                 r"(?:was|were|had|did|came|went|got|gave|took|made|said|"
                                                 r"saw|found|told|brought|broke|fell|held|ran|kept|"
                                                 r"left|paid|sold|sat|stood|ate|drank|thought|spoke|"
                                                 r"wrote|read|met|cut|put|set|let|bet|hurt|cost|hit|"
                                                 r"shut|read|ate|drank|sang|swam|knew|grew|threw|drew|"
                                                 r"flew|showed|blew|drove|rode|chose|froze|stole|woke|"
                                                 r"bit|hid|forbade|fell|lost|bought|caught|fought|"
                                                 r"taught|sought|sent|spent|built|burnt|dealt|dreamt|"
                                                 r"learnt|swept|crept|bent|lent|won|held|fled|led|fed|"
                                                 r"bred|laid|wept|withdrew|undertook|overcame|\w+ed)\b"
                                               + r"|\b\w+ed\b"),
            # Present simple: do/does/don't/doesn't aux first, then bare
            # subject + verb, then a 3sg "verb-s" fallback. The bare
            # subject + verb pattern catches "I eat rice." / "I drink
            # coffee" / "We use pens" — sentences where there's no aux.
            ('present simple',                 r"\b(?:do(?:n't|\s+not)?|does(?:n't|\s+not)?)" + SUBJ + r"\s+\w+\b"
                                               + r"|\b(?:I|you|we|they|he|she|it|[A-Z]\w+)\s+"
                                                 r"(?:am|is|are|have|has|do|does|"
                                                 r"\w+s|\w+(?<!ing)(?<!ed)(?<!en))\b"
                                               + r"|\b\w+s\b(?=\s|[\.,?!])"),
            ('conditional',                    rf"\bwould{NEG}{SUBJ}{NEG}\s+\w+\b"),
            ('subjunctive',                    rf"\b(?:were|be|have|do){NEG}\s+\w+\b"),
            ('passive',                        rf"\b(?:am|is|are|was|were|been|being|be){NEG}{SUBJ}{NEG}\s+\w+(?:ed|en|own|ung|ought|aught|oken|orne|one)(?:\s+by\s+\w+)?\b"),
            ('imperative',                     r"^[A-Z]\w+\b"),
            ('used to',                        r"\bused\s+to\s+\w+\b"),
            ('would (habitual)',               rf"\bwould{NEG}\s+\w+\b"),
            ('modal',                          rf"\b(?:can(?:'t|not)?|could(?:n't)?|may{NEG}?|might{NEG}?|must(?:n't)?|should(?:n't)?|ought\s+to|need(?:n't)?|dare(?:n't)?|have\s+to|has\s+to|had\s+to){SUBJ}\s+\w+\b"),
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
        # Passive labels carry both a tense ("present simple", "past simple",
        # …) and "passive". The naive longest-match-key sort would pick the
        # tense-only pattern first and stop at "is" / "are" rather than
        # extend to "is grown" / "are recommended". Route passive labels
        # straight to the passive cluster matcher.
        if 'passive' in L:
            pat = (rf"\b(?:am|is|are|was|were|been|being|be|get|gets|got|"
                   rf"gotten|getting){NEG}{SUBJ}{NEG}\s+(?:{IRREG_PP}|\w+ed|"
                   rf"\w+(?:en|own|ung|aught|oken|orne))(?:\s+by\s+\w+)?\b")
            m = re.search(pat, S, re.I)
            if m:
                return m.group(0)

        # Perfect Infinitive / Gerund / Participle short-circuit: these
        # labels would otherwise be claimed by the generic 'infinitive' /
        # 'gerund' / 'participle' keys in FORM_PATS, producing "to have"
        # without the participle. Run the perfect-cluster matcher first.
        if re.search(r'\bperfect (?:infinitive|gerund|participle)\b', L):
            m = re.search(rf"\b(?:to\s+have|having)\s+(?:{IRREG_PP}|\w+ed)\b", S, re.I)
            if m:
                return m.group(0)

        # Try the most-specific Labels first (longest match wins).
        # Sort patterns by Label length desc so 'present perfect continuous'
        # is tried before 'present perfect'.
        for key, pat in sorted(FORM_PATS, key=lambda x: -len(x[0])):
            if key in L:
                m = re.search(pat, S, re.I)
                if m:
                    return m.group(0)

        # ── Sub-form & wish/if-only/about-to/etc. fallbacks ────────────
        # Many Recognition rows carry richer Labels than the canonical
        # 12-cell grid (e.g. "Wish (Past Regret)", "Be About To",
        # "Time Clause (Future)"). The above pattern table can't reasonably
        # name every variant, so we try a set of high-precision keyword
        # matches before giving up.
        SUB = [
            # Wish + past simple/perfect/were
            (r'\bwish\b.*?\b(present|present unreal|past regret|past)',
             rf"\bwish(?:es|ed)?{SUBJ}\s+(?:I|you|we|they|he|she|it|[A-Z]\w+)?\s*"
             rf"(?:had{NEG}\s+(?:{IRREG_PP}|\w+ed)\b|were\b|(?:was|were){NEG}\s+\w+|"
             rf"\w+ed\b|could\s+\w+\b|would\s+\w+\b)"),
            # If only — highlight from "If only" through the verb cluster
            (r'\bif only\b',
             r"\bif\s+only\b\s+\w+\s+(?:had{NEG}\s+\w+|could\s+\w+|would\s+\w+|\w+ed)"),
            # Be About To — highlight "is/are/was/were about to + V"
            (r'\babout to\b',
             r"\b(?:am|is|are|was|were|'m|'s|'re)\s+about\s+to\s+\w+\b"),
            # Was/Were Going To
            (r'\bwas/were going to\b|\bwas going to\b|\bwere going to\b',
             rf"\b(?:was|were){NEG}\s+going\s+to\s+\w+\b"),
            # Get-Passive
            (r'\bget-passive\b|\bget passive\b',
             rf"\b(?:get|gets|got|gotten|getting){SUBJ}\s+\w+(?:ed|en|own|ung|"
             rf"ought|aught|oken)\b"),
            # Modal (Be Able To / Be Supposed To / Had Better)
            (r'\bbe able to\b',     r"\b(?:am|is|are|was|were|'m|'s|'re)\s+able\s+to\s+\w+\b"),
            (r'\bbe supposed to\b', r"\b(?:am|is|are|was|were|'m|'s|'re)\s+supposed\s+to\s+\w+\b"),
            (r'\bhad better\b|\bhad\b.*\bbetter\b',
             r"\b(?:'d|had|had\s+better|'d\s+better)(?:\s+not)?\s+\w+\b"),
            # Modal (Would — Past Habit) — already partially handled but
            # legacy 'would (habitual)' key may not align with this label
            (r'\bwould\b.*\bhabit\b|\bpast habit\b',
             rf"\bwould{NEG}\s+\w+\b"),
            # Due To (Formal Future)
            (r'\bdue to\b',         r"\b(?:am|is|are)\s+due\s+to\s+\w+\b"),
            # Time Clause — highlight the temporal subordinator + clause verb
            (r'\btime clause\b',
             r"\b(?:when|after|before|until|as soon as|by the time|once|while)\s+"
             r"[\w\s]+?\s+(?:\w+s\b|\w+ed\b|will\s+\w+|have\s+\w+|had\s+\w+|\w+\b)"),
            # Conditionals (zero / first / second / third / mixed) —
            # generic: highlight the if-clause verb cluster.
            (r'\bconditional\b|\bunless\b|\bas long as\b|\bprovided that\b',
             r"\b(?:if|unless|as\s+long\s+as|provided\s+that|on\s+condition\s+that)\s+"
             r"[\w'\s]+?(?:,|\s+(?:will|would|can|could|may|might|should))"),
            # Reported Speech (Suggest/Recommend) — subjunctive bare verb
            (r'\bsuggest\b|\brecommend\b',
             r"\b(?:suggest|suggests|suggested|recommend|recommends|recommended|"
             r"insist|insists|insisted|demand|demands|demanded|propose|proposes|proposed)"
             r"\s+that\s+\w+\s+\w+\b"),
            # Stative-aspect Present Simple ('look', 'prefer', 'suppose', 'love', etc.)
            (r'\bstative\b',
             r"\b(?:I|you|we|they|he|she|it|[A-Z]\w+)\s+"
             r"(?:look|looks|seem|seems|prefer|prefers|love|loves|hate|hates|"
             r"like|likes|believe|believes|know|knows|think|thinks|need|needs|"
             r"want|wants|own|owns|have|has|understand|understands|suppose|"
             r"supposes|remember|remembers|forget|forgets|recognise|recognises|"
             r"recognize|recognizes|consist|consists|contain|contains|cost|"
             r"costs|matter|matters|mean|means|deserve|deserves)\b"),
            # Present Perfect with adverbs (Just / Still / Already / Yet)
            (r'\b(just|still|already|yet|ever|never|recently|lately)\b',
             rf"\b(?:has|have|haven't|hasn't|'ve|'s)\s+"
             rf"(?:just|still|already|yet|ever|never|recently|lately)?\s*"
             rf"(?:been\s+)?(?:{IRREG_PP}|\w+ed)\b"),
            # Present Continuous (Complaint) — "she's always Ving"
            (r'\bcomplaint\b',
             r"\b(?:'s|'re|is|are|was|were)\s+(?:always|forever|constantly|continually)\s+\w+ing\b"),
            # Light Verb (Take/Make/Have/Give/Do) — "take a breath",
            # "make a decision", "have a look", "give a smile", "do a check".
            (r'\blight verb\b',
             r"\b(?:take|takes|took|taken|taking|"
             r"make|makes|made|making|"
             r"have|has|had|having|"
             r"give|gives|gave|given|giving|"
             r"do|does|did|done|doing)\s+"
             r"(?:a|an|the|some|two|three|several|another)\s+\w+\b"),
            # Modal (Would Sooner / Would Rather) — "He'd sooner resign…"
            (r'\bwould sooner\b|\bwould rather\b',
             r"\b(?:would|'d)\s+(?:sooner|rather)(?:\s+not)?\s+\w+\b"),
            # Phrasal-verb labels carry the literal phrasal in parentheses,
            # e.g. "Phrasal Verb (look forward to)". The handler below
            # (after this list) extracts that and matches against the sentence.
            # Mandative subjunctive: "It's essential that he submit..."
            (r'\bmandative\b|\bsubjunctive\b',
             r"\b(?:essential|important|crucial|vital|necessary|imperative|"
             r"mandatory|recommended|advisable|insist|insists|insisted|"
             r"suggest|suggests|suggested|demand|demands|demanded|"
             r"propose|proposes|proposed|require|requires|required)\b"
             r"[\s\w']*?\bthat\b\s+\w+\s+\w+\b"),
            # Bare Infinitive (Let/Make/Help/See/Hear/etc.)
            (r'\bbare infinitive\b',
             r"\b(?:let|lets|made|make|makes|help|helps|helped|see|saw|sees|"
             r"hear|heard|hears|watch|watches|watched|feel|feels|felt)"
             r"\s+(?:I|you|we|they|he|she|it|the|a|an|my|your|his|her|its|our|"
             r"their|[A-Z]\w+|\w+)\s+\w+\b"),
            # Perfect Infinitive / Gerund / Participle — take the whole
            # "to have V-en" / "having V-en" cluster. Case-insensitive
            # search (the wider pipeline uses re.I), so capital "Having"
            # at sentence start is handled by the same alternative.
            (r'\bperfect (?:infinitive|gerund|participle)\b',
             rf"\b(?:to\s+have|having)\s+(?:{IRREG_PP}|\w+ed)\b"),
            # Implicit Conditional (Coordination): "One more X and Y" / "Do X or Y"
            (r'\bimplicit conditional\b|\bcoordination\b',
             r"\b(?:one\s+more\s+\w+|another\s+\w+|do\s+that|stop\s+\w+ing)"
             r"\s+(?:and|or)\s+\w+(?:'ll|\s+will)\s+\w+\b"),
            # Passive forms: be + V-en (regular) or irregular participle
            (r'\bpassive\b',
             rf"\b(?:am|is|are|was|were|been|being|be|get|gets|got|gotten|getting)"
             rf"{NEG}{SUBJ}{NEG}\s+(?:{IRREG_PP}|\w+ed|\w+(?:en|own|ung|aught|"
             rf"oken|orne))(?:\s+by\s+\w+)?\b"),
        ]
        for label_pat, sent_pat in SUB:
            if re.search(label_pat, L):
                m = re.search(sent_pat, S, re.I)
                if m:
                    return m.group(0).rstrip(',')

        # ── Phrasal-verb labels ────────────────────────────────────────
        # The Label carries the canonical phrasal in parentheses, e.g.
        # "Phrasal Verb (look forward to)". We pull that out, build a
        # regex tolerant of inflection (look/looks/looked/looking) and
        # of intervening object pronouns (took it on, looked it up), and
        # match it back into the sentence so the highlight covers the
        # entire multi-word verb.
        if 'phrasal verb' in L or 'phrasal-verb' in L:
            mp = re.search(r'\(([^)]+)\)', label)
            if mp:
                parts = mp.group(1).strip().lower().split()
                if parts:
                    head = parts[0]
                    particles = parts[1:]
                    # Curated irregular forms for common phrasal heads, plus
                    # a generic regular-inflection fallback (V/V-s/V-ed/V-ing).
                    IRREG_VERB_FORMS = {
                        'be':    ['be', 'am', 'is', 'are', 'was', 'were', 'been', 'being'],
                        'have':  ['have', 'has', 'had', 'having'],
                        'do':    ['do', 'does', 'did', 'done', 'doing'],
                        'go':    ['go', 'goes', 'went', 'gone', 'going'],
                        'come':  ['come', 'comes', 'came', 'coming'],
                        'get':   ['get', 'gets', 'got', 'gotten', 'getting'],
                        'give':  ['give', 'gives', 'gave', 'given', 'giving'],
                        'take':  ['take', 'takes', 'took', 'taken', 'taking'],
                        'make':  ['make', 'makes', 'made', 'making'],
                        'put':   ['put', 'puts', 'putting'],
                        'set':   ['set', 'sets', 'setting'],
                        'see':   ['see', 'sees', 'saw', 'seen', 'seeing'],
                        'find':  ['find', 'finds', 'found', 'finding'],
                        'tell':  ['tell', 'tells', 'told', 'telling'],
                        'bring': ['bring', 'brings', 'brought', 'bringing'],
                        'break': ['break', 'breaks', 'broke', 'broken', 'breaking'],
                        'fall':  ['fall', 'falls', 'fell', 'fallen', 'falling'],
                        'hold':  ['hold', 'holds', 'held', 'holding'],
                        'run':   ['run', 'runs', 'ran', 'running'],
                        'keep':  ['keep', 'keeps', 'kept', 'keeping'],
                        'leave': ['leave', 'leaves', 'left', 'leaving'],
                        'pay':   ['pay', 'pays', 'paid', 'paying'],
                        'sell':  ['sell', 'sells', 'sold', 'selling'],
                        'sit':   ['sit', 'sits', 'sat', 'sitting'],
                        'stand': ['stand', 'stands', 'stood', 'standing'],
                        'eat':   ['eat', 'eats', 'ate', 'eaten', 'eating'],
                        'drink': ['drink', 'drinks', 'drank', 'drunk', 'drinking'],
                        'think': ['think', 'thinks', 'thought', 'thinking'],
                        'speak': ['speak', 'speaks', 'spoke', 'spoken', 'speaking'],
                        'write': ['write', 'writes', 'wrote', 'written', 'writing'],
                        'read':  ['read', 'reads', 'reading'],
                        'meet':  ['meet', 'meets', 'met', 'meeting'],
                        'cut':   ['cut', 'cuts', 'cutting'],
                    }
                    if head in IRREG_VERB_FORMS:
                        head_pat = '(?:' + '|'.join(re.escape(f) for f in IRREG_VERB_FORMS[head]) + ')'
                    else:
                        # Regular verb: V / V-s / V-ed / V-ing
                        # If head ends in 'e', drop it for -ing form (look→looking
                        # but make→making). For -ed, just append "d" to e-final.
                        h = re.escape(head)
                        if head.endswith('e'):
                            head_pat = (rf'(?:{h}|{h}s|{h}d|{re.escape(head[:-1])}ing)')
                        else:
                            head_pat = rf'(?:{h}|{h}s|{h}ed|{h}ing)'
                    # Particles must appear in order, with up to 4
                    # intervening object-NP tokens between adjacent particles
                    # AND between head and first particle.
                    if particles:
                        particle_pat = r'(?:\s+\w+){0,4}\s+'.join(re.escape(p) for p in particles)
                        pat = rf"\b{head_pat}(?:\s+\w+){{0,4}}\s+{particle_pat}\b"
                    else:
                        pat = rf"\b{head_pat}\b"
                    m = re.search(pat, S, re.I)
                    if m:
                        return m.group(0)

        # ── Last-resort generic verb-cluster fallback ──────────────────
        # If we still haven't extracted a focus, find ANY plausible verb
        # cluster in the sentence: subject (or aux) + main verb. This is
        # better than leaving the highlight empty, since the learner's
        # task on Recognition is "identify the highlighted verb form" —
        # we owe them a span even if our taxonomy didn't predict the
        # exact pattern.
        for pat in (
            # Aux + (subject)? + (not)? + (been)? + V(ing|ed|en|...)
            rf"\b(?:has|have|had|will|would|shall|should|can|could|may|might|must|"
            rf"do|does|did|am|is|are|was|were){NEG}{SUBJ}{NEG}\s+"
            rf"(?:been\s+)?(?:going\s+to\s+)?(?:about\s+to\s+)?\w+(?:ing|ed|en)?\b",
            # Bare past simple verb at clause start (e.g. "Plants die...")
            r"\b[a-z]\w+(?:ed|s)\b(?=\s|[\.,?!])",
        ):
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

    # ── Grammatical category classifier (v3.1.0+) ────────────────────
    # Module-level so Recognition + Contrast + Cloze + Production all
    # share the same taxonomy. Plus a few extra rules for the wider
    # vocabulary used by Contrast (Formal/Informal, single-word answers
    # like "have"/"are") and Production (Modal Paraphrase, Tense Change).
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
        # Register / pragmatic axis (Contrast cards):
        (r'^(formal|informal|neutral|colloquial|academic|spoken|written|literary)$', 'register'),
        # Aux-verb single-word answers in Contrast (am/is/are/was/were/has/have/had/do/does/did)
        # Bare aux-form (Contrast/Cloze single-word answers). Modals
        # (will/would/shall/should/can/could/may/might/must/ought/need)
        # are handled by the explicit \bmodal\b rule below so they
        # land in Module 03 Modals, not Foundation.
        (r'^(am|is|are|was|were|has|have|had|do|does|did)$', 'aux-form'),
        # Production targets
        (r'modal paraphrase|tense change|contraction expansion|register shift|active.{0,4}passive|passive.{0,4}active|paraphrase|transformation|nominalisation|nominalization', 'transformation'),
        # Discourse semantics
        (r'epistemic|deontic|dynamic.{0,4}modality', 'modal'),
        (r'connected speech|reduction|contraction|stress|linking|t[- ]flap|weak form|schwa|elision|intonation|assimilation|silent letter|word stress|sentence stress|prosody|rhythm', 'phonology'),
        (r'phrasal verb|particle verb', 'phrasal-verb'),
        (r'reported speech|indirect speech|direct speech|backshift', 'reported-speech'),
        (r'cleft|existential|causative|tag question|hedging|inversion|fronting|catenative|emphatic|exclamative|pseudo-cleft|reverse pseudo|response form|comment clause|extraposition|locative|comparative.*invers|degree.*invers|so.*such|time clause|narrative layering|reduced relative|caption present|headline present|stage direction|recipe imperative|historical present|performative', 'construction'),
        (r'gerund|infinitive|participle', 'non-finite'),
        (r'subjunctive|imperative', 'mood'),
        (r'passive|middle voice', 'voice'),
        (r'conditional|if[- ]clause|mixed cond|inverted cond|supposing|suppose|providing|provided that|imagine|hypothetical|in case|unless|^wish\b|\bwish (i|you|he|she|we|they)|wish \(|if only|as if|as though|would rather|sooner.{0,4}than', 'conditional'),
        (r'used to|would \(habitual\)|habitual past', 'periphrastic-past-habit'),
        (r'going to|be about to|be to\b|be due to|be on the verge', 'periphrastic-future'),
        (r"\bmodal\b|\bmust\b|\bshould\b|\bought\b|\bneed\b|\bdare\b|\bcan\b|\bcould\b|\bmay\b|\bmight\b|have to|has to|had to", 'modal'),
        # Future Simple uses 'will' as future marker — that's tense-aspect, NOT modal.
        # Anything else falls through to the canonical 12-cell grid.
    ]
    _CATPATS = [(re.compile(p, re.I), cat) for p, cat in _CATPATS]
    # Words that genuinely belong to the canonical 12-cell grid. Used
    # as a strict gate before falling through to 'tense-aspect': if the
    # label contains NONE of these, it does NOT belong in Foundation.
    # Otherwise advanced labels with no recognised category (e.g.
    # 'Supposing (Hypothetical)') would silently land in Foundation
    # and confuse beginner learners.
    _TENSE_ASPECT_GATE = re.compile(
        r'\b(present|past|future|simple|continuous|progressive|perfect|'
        r'present-?perfect|past-?perfect|future-?perfect|'
        r'narrative|historical|stative|dynamic)\b', re.I)

    # Some Recognition Labels in the source TSVs include a USE clause
    # ('Present Simple for Schedule', 'Present Continuous for Future
    # Arrangement') or a regional VARIANT marker ('Past Simple
    # (American Variant)', 'Present Perfect (British Variant)'). These
    # are valid pedagogical micro-distinctions but they conflate the
    # answer (the form name) with the function/variant — the
    # recognition prompt becomes unanswerable because there are too
    # many things to identify.
    #
    # Strip them from the displayed Label so the answer is JUST the
    # canonical form name. The function/variant info is already in
    # the MainUse field (or trivially derivable from it).
    _LABEL_USE_RE = re.compile(
        r'\s+for\s+(Schedule|Future Arrangement|Future Plan|Background|'
        r'Repeated Action|Polite Request|General Truth|Permanent State|'
        r'Habit|Future Reference|Annoyance|Emphasis|Storytelling|'
        r'Effect|Result|Recent Action|News|Personal Experience|Schedule)$',
        re.I)
    _LABEL_VARIANT_RE = re.compile(
        r'\s*\((American|British|Australian|Canadian|Irish|Scottish|'
        r'Indian|African|US|UK|AmE|BrE)\s*Variant\)$', re.I)
    # Strip parenthetical *use* / *style* notes that aren't variants
    # but still pollute the answer. The grammatical form is canonical;
    # the parenthetical is supplementary.
    #
    # Greedy: strip ANY trailing parenthetical that does NOT name a
    # major grammatical form (Continuous, Perfect, Passive, Subjunctive,
    # etc.). 'Past Simple (Polite Distancing)' → 'Past Simple', but
    # 'Future Simple Passive' is left alone (the 'Passive' word is the
    # form name itself).
    _LABEL_USE_PAREN_RE = re.compile(
        r'\s*\((?!('
        r'Continuous|Progressive|Perfect|Simple|Passive|Active|'
        r'Subjunctive|Imperative|Gerund|Infinitive|Participle|'
        r'Past|Present|Future|Modal|Conditional'
        r')\)$)[^()]+\)$',
        re.I)

    def _normalize_label(label: str) -> str:
        if not label: return label
        L = _LABEL_VARIANT_RE.sub('', label)
        L = _LABEL_USE_PAREN_RE.sub('', L)
        L = _LABEL_USE_RE.sub('', L)
        return L.strip()

    def _category_for(label: str) -> str:
        L = label.strip()
        # Passive trumps everything — 'Future Simple Passive' is voice,
        # not tense-aspect.
        if re.search(r'\bpassive\b|\bmiddle voice\b', L, re.I):
            return 'voice'
        # Future tenses are tense-aspect, not modal:
        if re.search(r'^future (?:simple|continuous|perfect)', L, re.I):
            return 'tense-aspect'
        for pat, cat in _CATPATS:
            if pat.search(L):
                return cat
        # Strict fallback: only land in Foundation if the label
        # mentions a tense/aspect word. Anything else is a layered
        # construction by default. This guarantees beginner Foundation
        # decks are never polluted by advanced Labels (e.g. Supposing,
        # Existential There, Cleft, Inversion) that happen to escape
        # every regex above.
        if _TENSE_ASPECT_GATE.search(L):
            return 'tense-aspect'
        return 'construction'

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
        'register':                'Identify the highlighted register',
        'aux-form':                'Identify the highlighted auxiliary',
        'transformation':          'Identify the highlighted transformation',
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
        'register':                'Name this register',
        'aux-form':                'Name this auxiliary',
        'transformation':          'Name this transformation',
    }
    # Per-card-type prompts (Contrast/Cloze/Production are not "Name X"
    # — they're "Choose / Fill / Write a sentence X").
    _CAT_PROMPTS_CONTRAST = {
        'tense-aspect':            'Which tense + aspect fits this sentence?',
        'modal':                   'Which modal fits this sentence?',
        'voice':                   'Which voice fits this sentence?',
        'mood':                    'Which mood fits this sentence?',
        'conditional':             'Which conditional type fits this sentence?',
        'non-finite':              'Which non-finite form fits this sentence?',
        'periphrastic-future':     'Which future construction fits this sentence?',
        'periphrastic-past-habit': 'Which past-habit construction fits this sentence?',
        'construction':            'Which construction fits this sentence?',
        'phrasal-verb':            'Which phrasal verb fits this sentence?',
        'reported-speech':         'Which reported-speech form fits this sentence?',
        'phonology':               'Which pronunciation feature fits this sentence?',
        'register':                'Which register fits this sentence?',
        'aux-form':                'Which auxiliary fits this sentence?',
        'transformation':          'Which transformation fits this sentence?',
    }
    _CAT_PROMPTS_CLOZE = {
        'tense-aspect':            'Fill in the missing tense + aspect',
        'modal':                   'Fill in the missing modal',
        'voice':                   'Fill in the missing passive form',
        'mood':                    'Fill in the missing mood',
        'conditional':             'Fill in the missing conditional form',
        'non-finite':              'Fill in the missing non-finite form',
        'periphrastic-future':     'Fill in the missing future construction',
        'periphrastic-past-habit': 'Fill in the missing past-habit construction',
        'construction':            'Fill in the missing construction',
        'phrasal-verb':            'Fill in the missing phrasal verb',
        'reported-speech':         'Fill in the missing reported-speech form',
        'phonology':               'Fill in the missing pronunciation feature',
        'register':                'Fill in the missing register',
        'aux-form':                'Fill in the missing auxiliary',
        'transformation':          'Fill in the missing form',
    }
    _CAT_PROMPTS_PROD = {
        'tense-aspect':            'Write a sentence using the target tense + aspect',
        'modal':                   'Write a sentence using the target modal',
        'voice':                   'Write a sentence using the target passive form',
        'mood':                    'Write a sentence using the target mood',
        'conditional':             'Write a sentence using the target conditional type',
        'non-finite':              'Write a sentence using the target non-finite form',
        'periphrastic-future':     'Write a sentence using the target future construction',
        'periphrastic-past-habit': 'Write a sentence using the target past-habit construction',
        'construction':            'Write a sentence using the target construction',
        'phrasal-verb':            'Write a sentence using the target phrasal verb',
        'reported-speech':         'Write a sentence using the target reported-speech form',
        'phonology':               'Write a sentence using the target pronunciation feature',
        'register':                'Write a sentence in the target register',
        'aux-form':                'Write a sentence using the target auxiliary',
        'transformation':          'Apply the target transformation',
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
        # Normalize Label: 'Present Simple for Schedule' → 'Present
        # Simple', 'Past Simple (American Variant)' → 'Past Simple'.
        # The use/variant info already lives in MainUse (col 4); the
        # answer to the recognition question becomes a clean form name.
        row[1] = _normalize_label(row[1])
        category = _category_for(row[1])
        mods = row_modules(row[8], category=category)
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
        # category was computed above (used for deck routing)
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
        
        # Reverse production keeps the same routing as the source
        # Recognition row: classify on Label, route by category.
        rev_cat = _category_for(label)
        mods_rev = row_modules(tags_str, category=rev_cat)
        audio_f, ipa_f, tl_f = media_for_sentence(sentence, ipa_index, timeline_index, label=label)
        
        # Create reverse production note. Add cat:* tag so Foundation
        # alignment audits show this card correctly classified (the
        # only auto-generated note type that previously lacked it).
        # Fields: Prompt | Sample | Why | Tags | Audio | IPA | Timeline
        rev_tags = (tags_set.split() if isinstance(tags_set, str)
                    else list(tags_set))
        if not any(t.startswith('cat:') for t in rev_tags):
            rev_tags.append(f'cat:{rev_cat}')
        rev_pro_note = ap.Note(
            model=rev_pro_model,
            fields=[sentence, sentence, formula, tags_str, audio_f, ipa_f, tl_f],
            tags=rev_tags,
        )
        for _mod in mods_rev:
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
        # Normalize OptionA / OptionB / Answer (cols 1, 2, 3) so the
        # contrast options shown to the learner read 'Present Simple'
        # vs 'Present Continuous' (not '… for Schedule' vs '… for
        # Future Arrangement'). The semantic distinction stays in the
        # ContrastInfo column where it belongs as supplementary context.
        row[1] = _normalize_label(row[1])
        row[2] = _normalize_label(row[2])
        row[3] = _normalize_label(row[3])
        # Compute category FIRST so deck routing aligns with prompt.
        cat = _category_for(row[3])
        mods = row_modules(row[6], category=cat)
        # For contrast, the "label" we map to a timeline is the Answer (column 3)
        audio_f, ipa_f, tl_f = media_for_sentence(
            row[0],
            ipa_index,
            timeline_index,
            label=row[3],
            option_a=row[1] if len(row) > 1 else '',
            option_b=row[2] if len(row) > 2 else '',
            answer=row[3] if len(row) > 3 else '',
        )
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        
        # Create regular contrast note. The Instruction is
        # "Which X fits this sentence?" with X = the answer category.
        instruction = _CAT_PROMPTS_CONTRAST[cat]
        note = ap.Note(
            model=con_model,
            fields=row[:7] + [audio_f, ipa_f, tl_f, instruction, cat],
            tags=row[6].split() + [f'cat:{cat}'],
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
        # Normalize Target field (col 1): 'Present Simple for Schedule'
        # → 'Present Simple'. The 'use the target tense+aspect' prompt
        # then asks for the form, not the form-plus-function.
        row[1] = _normalize_label(row[1])
        # Production: classify on Target field (col 1). Compute category
        # FIRST so deck routing aligns with prompt.
        cat = _category_for(row[1])
        mods = row_modules(row[5], category=cat)
        # For production, audio/IPA come from the Sample (column 3); timeline from Target (column 1).
        audio_f, ipa_f, tl_f = media_for_sentence(row[3], ipa_index, timeline_index, label=row[1])
        if audio_f: media_counts['audio'] += 1
        if ipa_f: media_counts['ipa'] += 1
        if tl_f: media_counts['timeline'] += 1
        instruction = _CAT_PROMPTS_PROD[cat]
        note = ap.Note(
            model=pro_model,
            fields=row[:6] + [audio_f, ipa_f, tl_f, instruction, cat],
            tags=row[5].split() + [f'cat:{cat}'],
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
            # Cloze: classify from the row's Hint + tags. Compute
            # category FIRST so deck routing aligns with prompt.
            cloze_tags = row[2]
            cloze_label = (row[1] or '') + ' ' + cloze_tags
            cat = _category_for(cloze_label)
            mods = row_modules(row[2], category=cat)
            # For cloze, the spoken sentence is the cloze Text with the
            # {{c1::…}} markers stripped — that's the natural English audio.
            audio_f, ipa_f, tl_f = media_for_sentence(row[0], ipa_index, timeline_index, label='')
            if audio_f: media_counts['audio'] += 1
            if ipa_f: media_counts['ipa'] += 1
            instruction = _CAT_PROMPTS_CLOZE[cat]
            note = ap.Note(
                model=cloze_model,
                fields=row[:3] + [audio_f, ipa_f, tl_f, instruction, cat],
                tags=row[2].split() + [f'cat:{cat}'],
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
