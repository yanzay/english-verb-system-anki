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


def strip_cloze(text: str) -> str:
    """Replace {{c1::form}} or {{c1::form::hint}} with just 'form' so the
    sentence is naturally readable / pronounceable."""
    return CLOZE_RE.sub(r"\1", text)


def collect_sentences():
    sentences = set()
    for p, idx in [
        (Path("conjugations_recognition.txt"), 0),
        (Path("conjugations_contrast.txt"), 0),
        (Path("conjugations_production.txt"), 3),
    ]:
        if not p.exists():
            continue
        for row in load_tsv(p):
            if len(row) > idx and row[idx].strip():
                sentences.add(row[idx].strip())
    # Tier-3 cloze sentences (strip {{c1::…}} markers first)
    cloze_path = Path("conjugations_cloze.txt")
    if cloze_path.exists():
        for row in load_tsv(cloze_path):
            if row and row[0].strip():
                sentences.add(strip_cloze(row[0].strip()))
    return sorted(sentences)


def sentence_to_ipa(text: str) -> str:
    """Convert a sentence to broad GA IPA. Unknown words are kept as
    'asterisked' words, which is what eng-to-ipa returns for OOV tokens."""
    import eng_to_ipa as ipa
    cleaned = PUNCT_RE.sub("", text)
    return ipa.convert(cleaned).strip()


def collect_words(sentences):
    """Build a lower-cased word inventory from all sentences (for the
    per-word IPA index used in the WORDS_JSON audit file)."""
    words = set()
    for s in sentences:
        for w in PUNCT_RE.sub("", s).split():
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
    word_index = {w: ipa.convert(w) for w in words}
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
