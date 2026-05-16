#!/usr/bin/env python3
"""
Tier-2 audio builder for the English Verb System Anki package.

Generates one MP3 per unique English sentence appearing in:
  - conjugations_recognition.txt   (field 0: Sentence)
  - conjugations_contrast.txt      (field 0: Sentence)
  - conjugations_production.txt    (field 3: Sample)
  - conjugations_cloze.txt         (field 0: Text, with {{c…::…}} stripped)

Output:
  media/audio/<sha1[:12]>.mp3       — natural-rate native voice
  media/audio_manifest.json         — per-hash record of synthesis params + file fingerprint

Backend: Google Cloud Text-to-Speech, Neural2/Studio voices.
Auth: gcloud auth application-default login
      (or set GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON)

Idempotent + incremental:
  * Filename hash = sha1(text)[:12]  (text-only, stable across re-renders).
  * The manifest stores, per hash, the params used (voice / rate / lang) plus
    a sha256 of the resulting MP3.  On every run we:
      - render any sentence that is missing on disk;
      - re-render any sentence whose recorded params differ from the current
        target params (voice/rate/lang drift);
      - re-render any sentence whose on-disk MP3 sha256 no longer matches the
        manifest (file corruption / external tampering);
      - prune any orphan MP3s whose hash is not in the current corpus
        (use --no-prune to disable; auto-skipped when --limit is in effect);
      - leave everything else untouched (no API call, no rewrite).

Cost note: at ~16 USD / 1 M chars Neural2, the full corpus (~1,200 sentences
× ~80 chars ≈ 100 K chars) costs roughly 1.50 USD per full re-render.
Use --dry-run first to see what would change.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ── Tunables (env or CLI) ────────────────────────────────────────────────
DEFAULT_VOICE        = os.environ.get("EVS_TTS_VOICE", "en-US-Neural2-F")  # warm female
DEFAULT_VOICE_ALT    = os.environ.get("EVS_TTS_VOICE_ALT", "en-US-Neural2-D")  # male
DEFAULT_LANG         = os.environ.get("EVS_TTS_LANG", "en-US")
DEFAULT_RATE         = 1.00
DEFAULT_AUDIO_ENC    = "MP3"

DRY_RUN = bool(os.environ.get("EVS_TTS_DRY_RUN", "").strip())

MEDIA_DIR      = Path("media/audio")
MANIFEST_PATH  = Path("media/audio_manifest.json")

MANIFEST_VERSION = 1


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


# ── Hashing helpers ──────────────────────────────────────────────────────
def text_hash(text: str) -> str:
    """Stable 12-char id for a sentence; used as the MP3 filename stem."""
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── TTS ──────────────────────────────────────────────────────────────────
def synth_mp3(text: str, out_path: Path, *, rate: float, voice_name: str,
              language_code: str = DEFAULT_LANG) -> bool:
    """Synthesize one MP3 with SSML <prosody rate>. Always overwrites
    out_path. Returns True if a file was written, False on dry-run no-op."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        print(f"  [dry-run] {voice_name} rate={rate:.2f} → {out_path.name}: {text[:60]!r}")
        return False

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
    """Yield data rows (skipping #-comment lines and the #columns: header)."""
    data_lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        data_lines.append(line)
    reader = csv.reader(data_lines, delimiter="\t", quotechar='"')
    for row in reader:
        yield row


_CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")
_BLANK_RE = re.compile(r"_{3,}|\[blank\]|\(blank\)", re.IGNORECASE)
_CHOICE_ANNOTATION_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _strip_choice_annotation(text: str) -> str:
    return _CHOICE_ANNOTATION_RE.sub("", (text or "").strip()).strip()


def _spoken_sentence(sentence: str, *, option_a: str = "", option_b: str = "", answer: str = "") -> str:
    """Return the natural spoken sentence used for audio hashing/rendering."""
    spoken = (sentence or "").strip()
    if not spoken:
        return ""
    spoken = _CLOZE_RE.sub(r"\1", spoken)

    if _BLANK_RE.search(spoken):
        fill = (answer or "").strip()
        if fill == (option_a or "").strip():
            fill = option_a
        elif fill == (option_b or "").strip():
            fill = option_b
        fill = _strip_choice_annotation(fill)
        if fill:
            spoken = _BLANK_RE.sub(fill, spoken)
    return spoken


def collect_sentences() -> List[str]:
    """Return a sorted list of unique English sentences across all 4 files."""
    sentences = set()
    rec = Path("conjugations_recognition.txt")
    con = Path("conjugations_contrast.txt")
    pro = Path("conjugations_production.txt")
    clz = Path("conjugations_cloze.txt")
    if rec.exists():
        for row in load_tsv(rec):
            if row and row[0].strip():
                sentences.add(_spoken_sentence(row[0].strip()))
    if con.exists():
        for row in load_tsv(con):
            if row and row[0].strip():
                option_a = row[1] if len(row) > 1 else ""
                option_b = row[2] if len(row) > 2 else ""
                answer = row[3] if len(row) > 3 else ""
                sentences.add(
                    _spoken_sentence(
                        row[0].strip(),
                        option_a=option_a,
                        option_b=option_b,
                        answer=answer,
                    )
                )
    if pro.exists():
        for row in load_tsv(pro):
            if len(row) >= 4 and row[3].strip():
                sentences.add(_spoken_sentence(row[3].strip()))
    if clz.exists():
        for row in load_tsv(clz):
            if row and row[0].strip():
                sentences.add(_spoken_sentence(row[0].strip()))
    # Image-cue captions (column 1) — also need TTS audio so the back of
    # the image card can play the model pronunciation.
    img = Path("conjugations_image.txt")
    if img.exists():
        for row in load_tsv(img):
            if len(row) >= 2 and row[1].strip():
                sentences.add(_spoken_sentence(row[1].strip()))
    return sorted(sentences)


# ── Manifest I/O ─────────────────────────────────────────────────────────
def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if data.get("version") == MANIFEST_VERSION and "entries" in data:
                return data
        except json.JSONDecodeError:
            pass
    return {"version": MANIFEST_VERSION, "entries": {}}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["entries"] = dict(sorted(manifest["entries"].items()))
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def manifest_entry(text: str, *, voice: str, rate: float, lang: str,
                   mp3_path: Path) -> dict:
    return {
        "text": text,
        "voice": voice,
        "rate": round(float(rate), 4),
        "lang": lang,
        "sha256": file_sha256(mp3_path) if mp3_path.exists() and mp3_path.stat().st_size > 0 else "",
        "size": mp3_path.stat().st_size if mp3_path.exists() else 0,
    }


def entry_matches(entry: dict, *, text: str, voice: str, rate: float, lang: str,
                  mp3_path: Path, verify_sha: bool) -> Tuple[bool, str]:
    """Return (ok, reason_if_not_ok)."""
    if not mp3_path.exists():
        return False, "missing-file"
    if mp3_path.stat().st_size == 0:
        return False, "zero-byte-file"
    if entry.get("text") != text:
        return False, "text-changed"
    if entry.get("voice") != voice:
        return False, "voice-changed"
    if round(float(entry.get("rate", 0)), 4) != round(float(rate), 4):
        return False, "rate-changed"
    if entry.get("lang") != lang:
        return False, "lang-changed"
    if verify_sha:
        recorded = entry.get("sha256", "")
        if not recorded:
            return False, "no-recorded-sha"
        if file_sha256(mp3_path) != recorded:
            return False, "sha-mismatch"
    return True, "ok"


# ── Driver ───────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Tier-2 audio builder (idempotent + incremental)")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="Google TTS voice name (default: en-US-Neural2-F)")
    ap.add_argument("--lang", default=DEFAULT_LANG,
                    help="BCP-47 language code (default en-US)")
    ap.add_argument("--rate", type=float, default=DEFAULT_RATE,
                    help="Speech rate (default 1.00)")
    ap.add_argument("--limit", type=int, default=0,
                    help="Limit to first N sentences (0 = all). Useful for cost-controlled smoke runs. "
                         "When set, prune is automatically disabled.")
    ap.add_argument("--force", action="store_true",
                    help="Re-render every MP3 even if params + sha already match")
    ap.add_argument("--no-prune", action="store_true",
                    help="Keep MP3s whose sentence is no longer in the corpus (default: prune them)")
    ap.add_argument("--no-verify-sha", action="store_true",
                    help="Skip sha256 verification of existing MP3s (faster on huge corpora)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't call the API and don't modify files; show what WOULD change")
    ap.add_argument("--rehash", action="store_true",
                    help="Recompute manifest sha256/size for all on-disk MP3s without re-synthesizing. "
                         "Use after externally regenerating audio or when bootstrapping the manifest.")
    args = ap.parse_args()

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True

    full_sentences = collect_sentences()
    sentences = full_sentences[:args.limit] if args.limit else full_sentences

    manifest = load_manifest()
    entries: Dict[str, dict] = manifest["entries"]

    # ── Rehash mode: rebuild manifest from on-disk files, no synthesis ──
    if args.rehash:
        print("Rehash mode: rebuilding manifest from on-disk MP3s (no synthesis).")
        text_by_hash = {text_hash(s): s for s in full_sentences}
        rebuilt = 0
        for mp3 in sorted(MEDIA_DIR.glob("*.mp3")):
            h = mp3.stem
            text = text_by_hash.get(h, entries.get(h, {}).get("text", ""))
            entries[h] = {
                "text": text,
                "voice": args.voice,
                "rate": round(float(args.rate), 4),
                "lang": args.lang,
                "sha256": file_sha256(mp3),
                "size": mp3.stat().st_size,
            }
            rebuilt += 1
        if not DRY_RUN:
            save_manifest(manifest)
        print(f"  Rehashed {rebuilt} entries → {MANIFEST_PATH}")
        return

    print(f"Corpus: {len(sentences)} unique English sentences "
          f"(voice={args.voice} lang={args.lang} rate={args.rate}).")

    written = up_to_date = stale = missing = 0
    reasons: Dict[str, int] = {}

    for i, text in enumerate(sentences, 1):
        h = text_hash(text)
        out = MEDIA_DIR / f"{h}.mp3"
        existing = entries.get(h)

        need = True
        reason = "new"
        if not args.force and existing is not None and out.exists():
            ok, why = entry_matches(existing,
                                    text=text, voice=args.voice,
                                    rate=args.rate, lang=args.lang,
                                    mp3_path=out,
                                    verify_sha=not args.no_verify_sha)
            if ok:
                need = False
            else:
                reason = why
        elif not out.exists():
            reason = "missing-file"
        elif args.force:
            reason = "force"

        if need:
            reasons[reason] = reasons.get(reason, 0) + 1
            if reason == "missing-file":
                missing += 1
            elif reason != "new":
                stale += 1
            wrote = synth_mp3(text, out,
                              rate=args.rate, voice_name=args.voice,
                              language_code=args.lang)
            if wrote:
                written += 1
                entries[h] = manifest_entry(text,
                                            voice=args.voice, rate=args.rate,
                                            lang=args.lang, mp3_path=out)
        else:
            up_to_date += 1
            # Backfill manifest entry if it was missing fields (e.g. legacy run).
            if existing is None or "sha256" not in existing or not existing.get("sha256"):
                entries[h] = manifest_entry(text,
                                            voice=args.voice, rate=args.rate,
                                            lang=args.lang, mp3_path=out)

        if i % 100 == 0 or i == len(sentences):
            print(f"  [{i}/{len(sentences)}] written={written} "
                  f"up-to-date={up_to_date} stale-rerendered={stale} "
                  f"missing-rendered={missing}")

    # ── Prune orphans ──
    # IMPORTANT: prune is always computed against the FULL corpus, never the
    # --limit-truncated subset; and --limit auto-disables prune as a safety net
    # so a smoke run like `--limit 3` doesn't wipe the rest of the corpus.
    desired = {text_hash(s) for s in full_sentences}
    pruned = 0
    if args.limit and not args.no_prune:
        if not DRY_RUN:
            print("  (prune skipped because --limit was used; run without --limit to prune)")
        args.no_prune = True
    if not args.no_prune and MEDIA_DIR.exists():
        for mp3 in sorted(MEDIA_DIR.glob("*.mp3")):
            if mp3.stem not in desired:
                if DRY_RUN:
                    print(f"  [dry-run] would prune orphan audio/{mp3.name}")
                else:
                    mp3.unlink()
                pruned += 1
                entries.pop(mp3.stem, None)

    if not DRY_RUN:
        save_manifest(manifest)

    print(f"\n✓ Done. written={written}  up-to-date={up_to_date}  pruned={pruned}")
    if reasons:
        details = ", ".join(f"{k}={v}" for k, v in sorted(reasons.items()))
        print(f"  re-render reasons: {details}")
    print(f"  Manifest: {MANIFEST_PATH}")
    print(f"  Output dir: {MEDIA_DIR}/")


if __name__ == "__main__":
    main()
