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
import sys
import subprocess
from pathlib import Path


def ensure_genanki():
    try:
        import genanki  # noqa: F401
        return
    except ImportError:
        pass
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                           '--user', '--break-system-packages', 'genanki'])


def load_tsv(path):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    rows = [line for line in lines if line and not line.startswith('#')]
    reader = csv.reader(rows, delimiter='\t', quotechar='"')
    header = next(reader)
    return header, list(reader)


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
    '07': {'time-clause'},
    '08': {'modal', 'modal-deduction', 'modal-obligation', 'modal-permission',
           'modal-perfect', 'modal-ability', 'modal-past-habit', 'modal-production'},
    '09': {'subjunctive', 'wish-present', 'wish-past', 'wish-would', 'if-only',
           'would-rather', 'its-time', 'as-if', 'mandative', 'subjunctive-production'},
    '10': {'non-finite', 'gerund', 'infinitive', 'bare-infinitive',
           'perfect-infinitive', 'perfect-gerund', 'perfect-participle',
           'infinitive-of-purpose'},
    '11': {'phrasal-verb', 'pv-separable', 'pv-inseparable', 'pv-transitive',
           'pv-intransitive', 'pv-three-part', 'pv-figurative', 'pv-literal'},
    '12': {'discourse', 'historical-present', 'politeness', 'hedging', 'headline',
           'recipe', 'cleft', 'emphatic', 'narrative-shift', 'performative',
           'register-formal', 'register-informal'},
    '13': {'l1-interference', 'l1-spanish', 'l1-french', 'l1-german',
           'l1-russian', 'l1-mandarin', 'l1-japanese'},
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
}


def row_module(tags_str):
    tags = set(tags_str.split())
    # Check newer/more-specific modules first so e.g. a phrasal-verb card
    # tagged with both 'phrasal-verb' and 'modal' routes to module 11.
    for mod in ['13', '12', '11', '10', '09', '08', '07', '06', '05', '04', '03', '02']:
        if tags & MODULE_TAGS[mod]:
            return mod
    return '01'


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
'''

    # ------------------------------------------------------------------
    # RECOGNITION MODEL
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
    # ------------------------------------------------------------------
    rec_model = genanki.Model(
        2056102001,
        'Verb System · Recognition',
        fields=[
            {'name': 'Sentence'},
            {'name': 'Label'},
            {'name': 'Aspect'},
            {'name': 'Formula'},
            {'name': 'MainUse'},
            {'name': 'QuickCue'},
            {'name': 'Contrast'},
            {'name': 'Tags'},
        ],
        templates=[{
            'name': 'Recognition Card',
            'qfmt': '''
<div class="instruction">What tense or aspect is this?</div>
<div class="sentence">{{Sentence}}</div>
''',
            'afmt': '''
<div class="instruction">What tense or aspect is this?</div>
<div class="sentence">{{Sentence}}</div>
<hr id="answer">
<div class="answer-label">{{Label}}</div>
{{#Aspect}}<span class="answer-correct">{{Aspect}}</span>{{/Aspect}}
<div class="meta-grid">
  <span class="meta-key">Formula</span><span class="meta-val">{{Formula}}</span>
  <span class="meta-key">Main use</span><span class="meta-val">{{MainUse}}</span>
</div>
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
        2056102002,
        'Verb System · Contrast',
        fields=[
            {'name': 'Sentence'},
            {'name': 'OptionA'},
            {'name': 'OptionB'},
            {'name': 'Answer'},
            {'name': 'Why'},
            {'name': 'Tip'},
            {'name': 'Tags'},
        ],
        templates=[{
            'name': 'Contrast Card',
            'qfmt': '''
<div class="instruction">Which label fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
''',
            'afmt': '''
<div class="instruction">Which label fits this sentence?</div>
<div class="sentence">{{Sentence}}</div>
<div class="options">
  <div class="option"><span class="opt-letter">A.</span>{{OptionA}}</div>
  <div class="option"><span class="opt-letter">B.</span>{{OptionB}}</div>
</div>
<hr id="answer">
<span class="answer-correct">✓ {{Answer}}</span>
<div class="why-block"><span class="why-label">Why: </span>{{Why}}</div>
{{#Tip}}<div class="tip-block">{{Tip}}</div>{{/Tip}}
''',
        }],
        css=css,
    )

    # ------------------------------------------------------------------
    # PRODUCTION MODEL
    # Fields: Prompt | Target | Aspect | Sample | Why | Tags
    # ------------------------------------------------------------------
    pro_model = genanki.Model(
        2056102003,
        'Verb System · Production',
        fields=[
            {'name': 'Prompt'},
            {'name': 'Target'},
            {'name': 'Aspect'},
            {'name': 'Sample'},
            {'name': 'Why'},
            {'name': 'Tags'},
        ],
        templates=[{
            'name': 'Production Card',
            'qfmt': '''
<div class="instruction">Produce a sentence</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
''',
            'afmt': '''
<div class="instruction">Produce a sentence</div>
<div class="sentence">{{Prompt}}</div>
<div class="target-badge">{{Target}}</div>
<hr id="answer">
<div class="sample-label">Sample answer</div>
<div class="sample-answer">{{Sample}}</div>
<div class="why-block"><span class="why-label">Why this works: </span>{{Why}}</div>
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
    }
    TYPE_SUFFIX = {'rec': '::1 - Recognition', 'con': '::2 - Contrast', 'pro': '::3 - Production'}

    decks = {}
    for (mod, typ), did in DECK_IDS.items():
        name = MODULE_NAMES[mod] + TYPE_SUFFIX[typ]
        decks[(mod, typ)] = genanki.Deck(did, name)

    counts = {'rec': 0, 'con': 0, 'pro': 0}

    # Recognition
    _, rec_rows = load_tsv('conjugations_recognition.txt')
    # Fields: Sentence | Label | Aspect | Formula | MainUse | QuickCue | Contrast | Tags
    for row in rec_rows:
        if len(row) < 8:
            row += [''] * (8 - len(row))
        mod = row_module(row[7])
        note = genanki.Note(
            model=rec_model,
            fields=row[:8],
            tags=row[7].split(),
        )
        decks[(mod, 'rec')].add_note(note)
        counts['rec'] += 1

    # Contrast
    _, con_rows = load_tsv('conjugations_contrast.txt')
    # Fields: Sentence | OptionA | OptionB | Answer | Why | Tip | Tags
    for row in con_rows:
        if len(row) < 7:
            row += [''] * (7 - len(row))
        mod = row_module(row[6])
        note = genanki.Note(
            model=con_model,
            fields=row[:7],
            tags=row[6].split(),
        )
        decks[(mod, 'con')].add_note(note)
        counts['con'] += 1

    # Production
    _, pro_rows = load_tsv('conjugations_production.txt')
    # Fields: Prompt | Target | Aspect | Sample | Why | Tags
    for row in pro_rows:
        if len(row) < 6:
            row += [''] * (6 - len(row))
        mod = row_module(row[5])
        note = genanki.Note(
            model=pro_model,
            fields=row[:6],
            tags=row[5].split(),
        )
        decks[(mod, 'pro')].add_note(note)
        counts['pro'] += 1

    out = 'english_verb_system_anki.apkg'
    genanki.Package(list(decks.values())).write_to_file(out)

    print(f'Built {out}')
    print(f'  recognition: {counts["rec"]}')
    print(f'  contrast:    {counts["con"]}')
    print(f'  production:  {counts["pro"]}')
    print(f'  total:       {sum(counts.values())}')
    print()
    print('Decks:')
    for (mod, typ), deck in decks.items():
        n = len(deck.notes)
        if n:
            print(f'  {deck.name}: {n}')


if __name__ == '__main__':
    main()
