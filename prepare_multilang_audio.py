#!/usr/bin/env python3
"""
Generate multilingual TTS audio for EchoMimic cross-lingual experiment.
Uses edge-tts to synthesize speech, then converts to mono WAV at 24000 Hz
to match the format of existing test audios.

Usage:
    pip install edge-tts pydub
    python prepare_multilang_audio.py

Output:
    assets/test_audios/multilang_<lang>.wav
"""

import asyncio
import os
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Experiment content: same sentence translated into each language.
# Chosen for phonetic richness (bilabials, fricatives, vowel variety).
# ---------------------------------------------------------------------------
LANGUAGES = {
    "en": {
        "voice": "en-US-JennyNeural",
        "text": "The sun sets slowly over the distant mountains, painting the sky with shades of orange and gold. A gentle breeze moves through the leaves.",
        "note": "English (American)",
    },
    "zh": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "text": "太阳缓缓落在远处的山峦之后，将天空染成橙色与金色。微风轻轻吹过树叶，带来一丝凉意。",
        "note": "Chinese (Mandarin)",
    },
    "ja": {
        "voice": "ja-JP-NanamiNeural",
        "text": "太陽がゆっくりと遠い山の向こうに沈み、空をオレンジ色と金色に染めます。そよ風が葉の間を静かに吹き抜けます。",
        "note": "Japanese",
    },
    "ko": {
        "voice": "ko-KR-SunHiNeural",
        "text": "태양이 먼 산 너머로 천천히 지며 하늘을 주황색과 금색으로 물들입니다. 부드러운 바람이 나뭇잎 사이를 지나갑니다.",
        "note": "Korean",
    },
    "es": {
        "voice": "es-ES-ElviraNeural",
        "text": "El sol se pone lentamente sobre las montañas lejanas, pintando el cielo de naranja y dorado. Una suave brisa mueve las hojas de los árboles.",
        "note": "Spanish",
    },
    "fr": {
        "voice": "fr-FR-DeniseNeural",
        "text": "Le soleil se couche lentement sur les montagnes lointaines, peignant le ciel de nuances d'orange et d'or. Une douce brise agite les feuilles des arbres.",
        "note": "French",
    },
    "de": {
        "voice": "de-DE-KatjaNeural",
        "text": "Die Sonne geht langsam hinter den fernen Bergen unter und malt den Himmel in Orange- und Goldtönen. Eine sanfte Brise bewegt die Blätter der Bäume.",
        "note": "German",
    },
    "ar": {
        "voice": "ar-SA-ZariyahNeural",
        "text": "تغرب الشمس ببطء خلف الجبال البعيدة، وتصبغ السماء بظلال البرتقالي والذهبي. نسيم لطيف يتحرك بين أوراق الأشجار.",
        "note": "Arabic",
    },
}

OUTPUT_DIR = Path("assets/test_audios")
SAMPLE_RATE = 24000  # match existing test audios


async def synthesize_mp3(lang: str, voice: str, text: str, tmp_path: Path):
    """Generate MP3 via edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(tmp_path))


def convert_to_wav(mp3_path: Path, wav_path: Path, sample_rate: int = SAMPLE_RATE):
    """Convert MP3 -> mono WAV at target sample rate using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(mp3_path),
        "-ac", "1",                   # mono
        "-ar", str(sample_rate),      # sample rate
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")


async def process_language(lang: str, cfg: dict):
    tmp_mp3 = OUTPUT_DIR / f"_tmp_{lang}.mp3"
    wav_out  = OUTPUT_DIR / f"multilang_{lang}.wav"

    print(f"[{lang}] Synthesizing: {cfg['note']} ...")
    await synthesize_mp3(lang, cfg["voice"], cfg["text"], tmp_mp3)

    print(f"[{lang}] Converting to WAV ({SAMPLE_RATE} Hz, mono) ...")
    convert_to_wav(tmp_mp3, wav_out)

    tmp_mp3.unlink(missing_ok=True)
    print(f"[{lang}] Done -> {wav_out}")


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check ffmpeg
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        raise EnvironmentError("ffmpeg not found. Install it: conda install -c conda-forge ffmpeg")

    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise ImportError("edge-tts not installed. Run: pip install edge-tts")

    tasks = [process_language(lang, cfg) for lang, cfg in LANGUAGES.items()]
    await asyncio.gather(*tasks)

    # Summary
    print("\n=== Generated files ===")
    for lang, cfg in LANGUAGES.items():
        wav = OUTPUT_DIR / f"multilang_{lang}.wav"
        if wav.exists():
            import wave
            with wave.open(str(wav)) as w:
                duration = round(w.getnframes() / w.getframerate(), 2)
            print(f"  {wav.name:30s} {duration:5.1f}s  ({cfg['note']})")
        else:
            print(f"  multilang_{lang}.wav  MISSING")


if __name__ == "__main__":
    asyncio.run(main())
