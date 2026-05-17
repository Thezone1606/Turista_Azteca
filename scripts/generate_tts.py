#!/usr/bin/env python3
"""
Generador de audios TTS para Turista Mundial Azteca.

Uso:
    python3 scripts/generate_tts.py              # genera los que falten
    python3 scripts/generate_tts.py --force      # regenera todos
    python3 scripts/generate_tts.py --only ags   # filtra por substring en el slug
    python3 scripts/generate_tts.py --list       # solo lista lo que generaría

Lee data/phrases.py y escribe MP3s a audio/<slug>.mp3.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "audio"

sys.path.insert(0, str(ROOT))
from data.phrases import ALL_PHRASES, VOICES  # noqa: E402


async def synth(text: str, voice: str, out_path: Path) -> None:
    tmp = out_path.with_suffix(".mp3.tmp")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(tmp))
    tmp.replace(out_path)


async def main_async(force: bool, only: str | None, list_only: bool) -> int:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    to_do: list[tuple[str, str, str]] = []
    skipped = 0
    for slug, voice_key, text in ALL_PHRASES:
        if only and only not in slug:
            continue
        out = AUDIO_DIR / f"{slug}.mp3"
        if out.exists() and not force:
            skipped += 1
            continue
        to_do.append((slug, VOICES[voice_key], text))

    if list_only:
        for slug, voice, text in to_do:
            print(f"{slug:30s}  [{voice}]  {text}")
        print(f"\n{len(to_do)} a generar, {skipped} ya existentes.")
        return 0

    if not to_do:
        print(f"Nada que hacer. {skipped} ya existen. Usa --force para regenerar.")
        return 0

    print(f"Generando {len(to_do)} archivos a {AUDIO_DIR} ({skipped} omitidos)...")
    for i, (slug, voice, text) in enumerate(to_do, 1):
        out = AUDIO_DIR / f"{slug}.mp3"
        print(f"  [{i:3d}/{len(to_do)}] {slug:30s}  ({voice})")
        try:
            await synth(text, voice, out)
        except Exception as e:
            print(f"      ! error: {e}", file=sys.stderr)
            return 1
    print("Listo.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="regenerar aunque exista")
    parser.add_argument("--only", help="filtra por substring del slug")
    parser.add_argument("--list", dest="list_only", action="store_true", help="solo listar")
    args = parser.parse_args()
    return asyncio.run(main_async(args.force, args.only, args.list_only))


if __name__ == "__main__":
    sys.exit(main())
