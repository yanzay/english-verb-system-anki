#!/usr/bin/env python3
"""
Tier-2 audio builder for the English Verb System Anki package.

Generates one MP3 per unique English sentence appearing in:
  - conjugations_recognition.txt   (field 0: Sentence)
  - conjugations_contrast.txt      (field 0: Sentence)
  - conjugations_production.txt    (field 3: Sample)

Output:
  media/audio/<sha1[:12]>.mp3      — natural-rate native voice
  media/audio_slow/<sha1[:12]>.mp3 — slow rate (0.80×) variant for connected-speech study

Backend: Google Cloud Text-to-Speech, Neural2/Studio voices.
Auth: same Application Default Credentials as ~/projects/japanese-reading
      (gcloud auth application-default login).

Idempotent: skips files that already exist unless --force is given.

Cost note: at ~16 USD / 1 M chars Neural2, the full corpus (≈1,113 cards
× ~80 chars ≈ 90 K chars × 2 variants ≈ 180 K chars) costs roughly
3 USD per full re-render. Use --dry-run first.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
from pathlib import Path

# ── Tunables (env or CLI) ────────────────────────────────────────────────
DEFAULT_VOICE        = os.environ.get("EVS_TTS_VOICE", "en-US-Neural2-F")  # warm female
DEFAULT_VOICE_ALT    = os.environ.get("EVS_TTS_VOICE_ALT", "en-US-Neural2-D")  # male
DEFAULT_LANG         = os.environ.get("EVS_TTS_LANG", "en-US")
DEFAULT_RATE_FAST    = 1.00
DEFAULT_RATE_SLOW    = 0.80
DEFAULT_AUDIO_ENC    = "MP3"

DRY_RUN = bool(os.environ.get("EVS_TTS_DRY_RUN", "").strip())

MEDIA_DIR      = Path("media/audio")
MEDIA_DIR_SLOW = Path("media/audio_slow")


# ── Google client (lazy) ─────────────────────────────────────────────────
_CLIENT = None


def _client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    try:
        from google.cloud import texttospeech as tts  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Audio builder requires `google-cloud-texttospeech`.\n"
            "  pip install google-cloud-texttospeech\n"
            "and authenticate with `gcloud auth application-default login`."
        ) from e
    _CLIENT = tts.TextToSpeechClient()
    return _CLIENT


def _audio_encoding():
    from google.cloud import texttospeech as tts  # type: ignore
    return getattr(tts.AudioEncoding, DEFAULT_AUDIO_ENC)


def _hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


def synth_mp3(text: str, out_path: Path, *, rate: float, voice_name: str,
              language_code: str = DEFAULT_LANG) -> bool:
    """Synthesize one MP3 with SSML <prosody rate>. Returns True if a new
    file was written, False if skipped."""
    if out_path.exists():
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        print(f"  [dry-run] {voice_name} rate={rate:.2f} → {out_path.name}: {text[:60]!r}")
        out_path.write_bytes(b"")  # zero-byte placeholder
        return True

    from google.cloud import texttospeech as tts  # type: ignore
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    ssml = f'<speak><prosody rate="{rate:.2f}">{safe}</prosody></speak>'
    voice = tts.VoiceSelectionParams(language_code=language_code, name=voice_name)
    audio_config = tts.AudioConfig(audio_encoding=_audio_encoding())
    response = _client().synthesize_speech(
        input=tts.SynthesisInput(ssml=ssml),
        voice=voice,
        audio_config=audio_config,
    )
    out_path.write_bytes(response.audio_content)
    return True


# ── Corpus extraction ────────────────────────────────────────────────────
def load_tsv(path: Path):
    """Yield data rows (skipping #-comment lines and the #columns: header).
    Uses csv module so quoted tab-containing fields parse correctly."""
    import io
    data_lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        data_lines.append(line)
    reader = csv.reader(data_lines, delimiter="\t", quotechar='"')
    for row in reader:
        yield row


_CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def collect_sentences():
    """Return a sorted list of unique English sentences across all 4 files
    (recognition, contrast, production, and Tier-3 cloze)."""
    sentences = set()
    rec = Path("conjugations_recognition.txt")
    con = Path("conjugations_contrast.txt")
    pro = Path("conjugations_production.txt")
    clz = Path("conjugations_cloze.txt")
    if rec.exists():
        for row in load_tsv(rec):
            if row and row[0].strip():
                sentences.add(row[0].strip())
    if con.exists():
        for row in load_tsv(con):
            if row and row[0].strip():
                sentences.add(row[0].strip())
    if pro.exists():
        for row in load_tsv(pro):
            if len(row) >= 4 and row[3].strip():
                sentences.add(row[3].strip())
    if clz.exists():
        for row in load_tsv(clz):
            if row and row[0].strip():
                # Strip {{c1::form}} markers so the spoken sentence is natural.
                sentences.add(_CLOZE_RE.sub(r"\1", row[0].strip()))
    return sorted(sentences)


# ── Driver ───────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Tier-2 audio builder")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="Google TTS voice name (default: en-US-Neural2-F)")
    ap.add_argument("--rate-fast", type=float, default=DEFAULT_RATE_FAST,
                    help="Speech rate for the natural-speed variant (default 1.00)")
    ap.add_argument("--rate-slow", type=float, default=DEFAULT_RATE_SLOW,
                    help="Speech rate for the slow-speed variant (default 0.80)")
    ap.add_argument("--no-slow", action="store_true",
                    help="Skip generating the slow-speed variant")
    ap.add_argument("--limit", type=int, default=0,
                    help="Limit to first N sentences (0 = all). Useful for cost-controlled smoke runs.")
    ap.add_argument("--force", action="store_true",
                    help="Re-render even if the MP3 already exists")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't call the API; show what would be sent")
    args = ap.parse_args()

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True

    if args.force:
        # Wipe existing files so synth_mp3's idempotency check re-renders.
        for d in [MEDIA_DIR, MEDIA_DIR_SLOW]:
            if d.exists():
                for p in d.glob("*.mp3"):
                    p.unlink()

    sentences = collect_sentences()
    if args.limit:
        sentences = sentences[:args.limit]

    print(f"Corpus: {len(sentences)} unique English sentences.")
    written_fast = written_slow = skipped = 0
    for i, text in enumerate(sentences, 1):
        h = _hash(text)
        out_fast = MEDIA_DIR / f"{h}.mp3"
        out_slow = MEDIA_DIR_SLOW / f"{h}.mp3"

        wrote = synth_mp3(text, out_fast,
                          rate=args.rate_fast, voice_name=args.voice)
        if wrote:
            written_fast += 1
        else:
            skipped += 1

        if not args.no_slow:
            wrote_s = synth_mp3(text, out_slow,
                                rate=args.rate_slow, voice_name=args.voice)
            if wrote_s:
                written_slow += 1

        if i % 100 == 0 or i == len(sentences):
            print(f"  [{i}/{len(sentences)}] fast={written_fast} slow={written_slow} skipped={skipped}")

    print(f"\n✓ Done.  fast-MP3 written: {written_fast}; slow-MP3 written: {written_slow}; "
          f"skipped (already existed): {skipped}.")
    print(f"Output dirs: {MEDIA_DIR}/  {MEDIA_DIR_SLOW}/")


if __name__ == "__main__":
    main()
