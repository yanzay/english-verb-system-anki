#!/usr/bin/env python3
"""
Tier-2 IPA helper for the English Verb System Anki package.

Computes a per-sentence IPA transcription (broad General-American) for every
unique English sentence in the corpus, plus a per-word lookup that surfaces
contraction expansions and the three -ed allomorphs (/t/ /d/ /ɪd/) that
typically trip up learners.

Output:
  media/ipa/<sha1[:12]>.txt    — one IPA string per sentence
  media/ipa_index.json         — { sha1[:12]: ipa_string }
  media/ipa_words.json         — { word_lowercase: ipa_string }   (audit)

Backend: `eng-to-ipa` library (Carnegie-Mellon dict + heuristic fallback).
The output is a *broad* transcription; for narrow/regional transcription
substitute a different backend (e.g. `phonemizer` with espeak-ng).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

MEDIA_DIR = Path("media/ipa")
INDEX_JSON = Path("media/ipa_index.json")
WORDS_JSON = Path("media/ipa_words.json")

# Sentence-final punctuation we strip before IPA conversion.
PUNCT_RE = re.compile(r"[\u2014\u2026\u201c\u201d\u2018\u2019\".,!?;:()\[\]\u2014\u2013]")

# ── OOV overrides ───────────────────────────────────────────────────────
# eng-to-ipa (CMUdict) doesn't know certain BrE spellings, contractions,
# proper nouns, abbreviations, or compound words. Provide hand-curated
# broad GA/RP transcriptions so we don't ship asterisked tokens. Keys
# must be lowercase; values may include primary stress (ˈ).
IPA_OVERRIDES = {
    # BrE spellings → AmE phonology
    "colours": "ˈkʌlərz",
    "organised": "ˈɔrgəˌnaɪzd",
    "organising": "ˈɔrgəˌnaɪzɪŋ",
    "finalised": "ˈfaɪnəˌlaɪzd",
    "encyclopaedias": "ɪnˌsaɪkləˈpidiəz",
    # Contractions / clitics
    "'ll": "əl",
    "daren't": "dɛrnt",
    # Common nouns missing from CMUdict
    "motorway": "ˈmoʊtərˌweɪ",
    "takeaway": "ˈteɪkəˌweɪ",
    "round-table": "ˈraʊnd ˈteɪbəl",
    "single-handedly": "ˈsɪŋgəl ˈhændɪdli",
    "user-acceptance": "ˈjuzər əkˈsɛptəns",
    # Verbs / participles
    "tidied": "ˈtaɪdid",
    # Proper nouns
    "messi": "ˈmɛsi",
    # Abbreviations / time expressions / typos
    "o'clock": "əˈklɑk",
    "oclock":  "əˈklɑk",
    "2pm":     "tu pi ɛm",
    "8pm":     "eɪt pi ɛm",
    "100°c":   "wʌn ˈhʌndrəd dɪˈgriz ˈsɛlsiəs",
    "q2":      "kju tu",
    "ubc":     "ju bi si",
    # Symbols
    "→": "tu",
    # eng-to-ipa / CMUdict transcription corrections (broad GA)
    "get":   "gɛt",
    "gets":  "gɛts",
    "just":  "dʒʌst",
    "poor":  "pʊr",
}


def _hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


def load_tsv(path: Path):
    import csv as _csv
    data_lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        data_lines.append(line)
    for row in _csv.reader(data_lines, delimiter="\t", quotechar='"'):
        yield row


CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")
BLANK_RE = re.compile(r"_{3,}|\[blank\]|\(blank\)", re.IGNORECASE)
CHOICE_ANNOTATION_RE = re.compile(r"\s*\([^)]*\)\s*$")


def strip_cloze(text: str) -> str:
    """Replace {{c1::form}} or {{c1::form::hint}} with just 'form' so the
    sentence is naturally readable / pronounceable."""
    return CLOZE_RE.sub(r"\1", text)


def _strip_choice_annotation(text: str) -> str:
    return CHOICE_ANNOTATION_RE.sub("", (text or "").strip()).strip()


def spoken_sentence(sentence: str, *, option_a: str = "", option_b: str = "", answer: str = "") -> str:
    spoken = strip_cloze((sentence or "").strip())
    if BLANK_RE.search(spoken):
        fill = (answer or "").strip()
        if fill == (option_a or "").strip():
            fill = option_a
        elif fill == (option_b or "").strip():
            fill = option_b
        fill = _strip_choice_annotation(fill)
        if fill:
            spoken = BLANK_RE.sub(fill, spoken)
    return spoken


def collect_sentences():
    sentences = set()
    rec_path = Path("conjugations_recognition.txt")
    if rec_path.exists():
        for row in load_tsv(rec_path):
            if row and row[0].strip():
                sentences.add(spoken_sentence(row[0].strip()))

    con_path = Path("conjugations_contrast.txt")
    if con_path.exists():
        for row in load_tsv(con_path):
            if row and row[0].strip():
                option_a = row[1] if len(row) > 1 else ""
                option_b = row[2] if len(row) > 2 else ""
                answer = row[3] if len(row) > 3 else ""
                sentences.add(
                    spoken_sentence(
                        row[0].strip(),
                        option_a=option_a,
                        option_b=option_b,
                        answer=answer,
                    )
                )

    pro_path = Path("conjugations_production.txt")
    if pro_path.exists():
        for row in load_tsv(pro_path):
            if len(row) >= 4 and row[3].strip():
                sentences.add(spoken_sentence(row[3].strip()))
    # Tier-3 cloze sentences (strip {{c1::…}} markers first)
    cloze_path = Path("conjugations_cloze.txt")
    if cloze_path.exists():
        for row in load_tsv(cloze_path):
            if row and row[0].strip():
                sentences.add(spoken_sentence(row[0].strip()))
    # Image-cue captions (col 1)
    img_path = Path("conjugations_image.txt")
    if img_path.exists():
        for row in load_tsv(img_path):
            if len(row) >= 2 and row[1].strip():
                sentences.add(spoken_sentence(row[1].strip()))
    return sorted(sentences)


def _apply_overrides_to_ipa_string(ipa_str: str, original_text: str) -> str:
    """Replace any 'word*' OOV tokens in ipa_str with our hand-curated
    transcription when the original lowercased word is in IPA_OVERRIDES.
    eng-to-ipa marks OOV tokens by appending '*' to the original word."""
    if "*" not in ipa_str:
        return ipa_str
    # Tokenise the original sentence in the same way eng-to-ipa does
    # (whitespace split after punctuation removal). Order is preserved.
    src_tokens = PUNCT_RE.sub("", original_text).split()
    out_tokens = ipa_str.split()
    if len(src_tokens) != len(out_tokens):
        # Token-count mismatch (e.g. eng-to-ipa expanded a contraction);
        # fall back to a per-token lookup by stripped form.
        fixed = []
        for tok in out_tokens:
            if tok.endswith("*"):
                key = tok[:-1].lower()
                fixed.append(IPA_OVERRIDES.get(key, tok))
            else:
                fixed.append(tok)
        return " ".join(fixed)
    fixed = []
    for src, tok in zip(src_tokens, out_tokens):
        if tok.endswith("*"):
            key = src.lower()
            fixed.append(IPA_OVERRIDES.get(key, tok))
        else:
            fixed.append(tok)
    return " ".join(fixed)


def _clean_for_ipa(text: str) -> str:
    """Strip punctuation but leave a space behind so word boundaries are
    preserved (e.g. 'leave—we' must not become 'leavewe'). Collapse runs
    of whitespace afterwards."""
    return re.sub(r"\s+", " ", PUNCT_RE.sub(" ", text)).strip()


def sentence_to_ipa(text: str) -> str:
    """Convert a sentence to broad GA IPA. Unknown words are kept as
    'asterisked' words, which is what eng-to-ipa returns for OOV tokens —
    except where we have a hand-curated override in IPA_OVERRIDES."""
    import eng_to_ipa as ipa
    cleaned = _clean_for_ipa(text)
    raw = ipa.convert(cleaned).strip()
    return _apply_overrides_to_ipa_string(raw, cleaned)


def collect_words(sentences):
    """Build a lower-cased word inventory from all sentences (for the
    per-word IPA index used in the WORDS_JSON audit file)."""
    words = set()
    for s in sentences:
        for w in _clean_for_ipa(s).split():
            w = w.strip().lower()
            if w:
                words.add(w)
    return sorted(words)


def main():
    ap = argparse.ArgumentParser(description="Tier-2 IPA builder")
    ap.add_argument("--limit", type=int, default=0, help="Limit to first N sentences")
    ap.add_argument("--force", action="store_true", help="Re-render even if file exists")
    args = ap.parse_args()

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    sentences = collect_sentences()
    if args.limit:
        sentences = sentences[:args.limit]

    print(f"Corpus: {len(sentences)} unique sentences. Computing IPA…")
    index = {}
    written = skipped = 0
    for i, text in enumerate(sentences, 1):
        h = _hash(text)
        out = MEDIA_DIR / f"{h}.txt"
        if out.exists() and not args.force:
            ipa_str = out.read_text(encoding="utf-8").strip()
            skipped += 1
        else:
            ipa_str = sentence_to_ipa(text)
            out.write_text(ipa_str + "\n", encoding="utf-8")
            written += 1
        index[h] = ipa_str
        if i % 200 == 0 or i == len(sentences):
            print(f"  [{i}/{len(sentences)}] written={written} skipped={skipped}")

    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    # Audit dictionary: per-word IPA so reviewers can spot OOV/odd entries.
    print("Building per-word audit dictionary…")
    import eng_to_ipa as ipa
    words = collect_words(sentences)
    def _word_ipa(w: str) -> str:
        if w in IPA_OVERRIDES:
            return IPA_OVERRIDES[w]
        v = ipa.convert(w)
        # eng-to-ipa returns 'word*' for OOV; honour overrides on the bare key.
        if v.endswith("*") and w in IPA_OVERRIDES:
            return IPA_OVERRIDES[w]
        return v
    word_index = {w: _word_ipa(w) for w in words}
    WORDS_JSON.write_text(json.dumps(word_index, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    print(f"\n✓ Done.  IPA files written: {written};  skipped: {skipped}.")
    print(f"  Per-sentence index: {INDEX_JSON}")
    print(f"  Per-word audit:     {WORDS_JSON}  ({len(words)} unique words)")

    # Surface OOV ratio
    oov = sum(1 for v in word_index.values() if "*" in v)
    print(f"  Out-of-dictionary words (kept with '*'): {oov}/{len(words)} "
          f"({100.0 * oov / max(1, len(words)):.1f}%)")


if __name__ == "__main__":
    main()
