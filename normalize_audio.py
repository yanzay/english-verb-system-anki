#!/usr/bin/env python3
"""
Loudness-normalize all MP3 files in media/audio/ to EBU R128 broadcast standard.

Usage:
  .venv/bin/python normalize_audio.py [--dry-run] [--limit N]

Normalizes each MP3 to -16 LUFS (EBU R128), mono, 24 kHz, 64 kbps.
Updates media/audio_manifest.json with new sha256 and "normalized": true.
Idempotent: skips files already marked normalized.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AUDIO_DIR = Path("media/audio")
MANIFEST_PATH = Path("media/audio_manifest.json")
FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"

def file_sha256(path: Path) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def normalize_mp3(in_path: Path, tmp_path: Path) -> bool:
    """
    Normalize an MP3 file using ffmpeg.
    Returns True if successful, False otherwise.
    """
    cmd = [
        FFMPEG_BIN,
        "-i", str(in_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-b:a", "64k",
        "-ar", "24000",
        "-ac", "1",
        "-y",
        str(tmp_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def load_manifest() -> dict:
    """Load the audio manifest."""
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"version": 1, "entries": {}}

def save_manifest(manifest: dict) -> None:
    """Save the audio manifest."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["entries"] = dict(sorted(manifest["entries"].items()))
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )

def process_audio_files(dry_run: bool = False, limit: int = None) -> tuple:
    """
    Process all audio files in media/audio/.
    Returns (processed, skipped, errors).
    """
    if not AUDIO_DIR.exists():
        print(f"Error: {AUDIO_DIR} does not exist")
        return 0, 0, []
    
    manifest = load_manifest()
    entries = manifest.get("entries", {})
    
    # Collect all MP3 files
    mp3_files = sorted(AUDIO_DIR.glob("*.mp3"))
    if limit:
        mp3_files = mp3_files[:limit]
    
    processed = 0
    skipped = 0
    errors = []
    
    print(f"Found {len(mp3_files)} MP3 file(s) to process", flush=True)
    print(f"Dry-run: {dry_run}", flush=True)
    print(flush=True)
    
    for idx, mp3_path in enumerate(mp3_files, 1):
        hash_key = mp3_path.stem
        entry = entries.get(hash_key, {})
        
        # Check if already normalized
        if entry.get("normalized"):
            skipped += 1
            if idx % 100 == 0:
                print(f"[{idx}/{len(mp3_files)}] processed={processed} skipped={skipped}", flush=True)
            continue
        
        if dry_run:
            processed += 1
            if idx % 100 == 0:
                print(f"[{idx}/{len(mp3_files)}] processed={processed} skipped={skipped}", flush=True)
            continue
        
        # Normalize main MP3
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            if not normalize_mp3(mp3_path, tmp_path):
                errors.append(f"{hash_key}: ffmpeg normalization failed")
                tmp_path.unlink(missing_ok=True)
                continue
            
            # Atomically replace original
            os.replace(tmp_path, mp3_path)
            
            # Update entry
            entry["sha256"] = file_sha256(mp3_path)
            entry["size"] = mp3_path.stat().st_size
            entry["normalized"] = True
            
            # Mark slow variant as normalized too (metadata only)
            if "slow" in entry:
                entry["slow"]["normalized"] = True
            
            entries[hash_key] = entry
            processed += 1
            
            if idx % 100 == 0:
                print(f"[{idx}/{len(mp3_files)}] processed={processed} skipped={skipped}", flush=True)
            # Checkpoint manifest every 50 normalized files so an interrupt
            # doesn't lose progress (loudnorm pass is slow + script may be
            # killed by an outer wrapper).
            if not dry_run and processed % 50 == 0 and processed > 0:
                manifest["entries"] = entries
                save_manifest(manifest)

        except Exception as e:
            errors.append(f"{hash_key}: {str(e)}")
            tmp_path.unlink(missing_ok=True)
    
    # Save updated manifest
    if not dry_run:
        manifest["entries"] = entries
        save_manifest(manifest)
    
    return processed, skipped, errors

def main():
    parser = argparse.ArgumentParser(description="Loudness-normalize MP3 files in media/audio/")
    parser.add_argument("--dry-run", action="store_true", help="Count files without processing")
    parser.add_argument("--limit", type=int, help="Process only N files (for smoke testing)")
    
    args = parser.parse_args()
    
    processed, skipped, errors = process_audio_files(
        dry_run=args.dry_run,
        limit=args.limit
    )
    
    print()
    print(f"Results:", flush=True)
    print(f"  Processed: {processed}", flush=True)
    print(f"  Skipped:   {skipped}", flush=True)
    print(f"  Errors:    {len(errors)}", flush=True)
    
    if errors:
        print()
        print("Errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}", flush=True)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more", flush=True)
    
    sys.exit(0 if len(errors) == 0 else 1)

if __name__ == "__main__":
    main()
