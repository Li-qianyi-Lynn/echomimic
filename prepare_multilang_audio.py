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
    # ── Original 8 ──────────────────────────────────────────────────────────
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
    # ── Added 22 ─────────────────────────────────────────────────────────────
    "pt": {
        "voice": "pt-BR-FranciscaNeural",
        "text": "O sol se põe lentamente sobre as montanhas distantes, pintando o céu com tons de laranja e dourado. Uma brisa suave move as folhas das árvores.",
        "note": "Portuguese (Brazilian)",
    },
    "ru": {
        "voice": "ru-RU-SvetlanaNeural",
        "text": "Солнце медленно садится за далёкие горы, окрашивая небо в оранжевые и золотые тона. Лёгкий ветерок шевелит листья деревьев.",
        "note": "Russian",
    },
    "it": {
        "voice": "it-IT-ElsaNeural",
        "text": "Il sole tramonta lentamente sulle montagne lontane, dipingendo il cielo di sfumature arancioni e dorate. Una leggera brezza muove le foglie degli alberi.",
        "note": "Italian",
    },
    "nl": {
        "voice": "nl-NL-ColetteNeural",
        "text": "De zon zakt langzaam achter de verre bergen en kleurt de lucht in tinten oranje en goud. Een zacht briesje beweegt door de bladeren.",
        "note": "Dutch",
    },
    "pl": {
        "voice": "pl-PL-ZofiaNeural",
        "text": "Słońce zachodzi powoli za odległe góry, malując niebo odcieniami pomarańczy i złota. Delikatny wiatr porusza liśćmi drzew.",
        "note": "Polish",
    },
    "tr": {
        "voice": "tr-TR-EmelNeural",
        "text": "Güneş uzaktaki dağların arkasına yavaşça inerken gökyüzünü turuncu ve altın rengi tonlarıyla boyuyor. Hafif bir esinti yaprakların arasından geçiyor.",
        "note": "Turkish",
    },
    "vi": {
        "voice": "vi-VN-HoaiMyNeural",
        "text": "Mặt trời lặn chậm rãi sau những ngọn núi xa, nhuộm bầu trời bằng sắc cam và vàng óng. Một cơn gió nhẹ thổi qua những chiếc lá.",
        "note": "Vietnamese",
    },
    "th": {
        "voice": "th-TH-PremwadeeNeural",
        "text": "ดวงอาทิตย์ค่อยๆ ลับขอบฟ้าหลังเทือกเขาที่อยู่ไกลออกไป ทาสีท้องฟ้าด้วยสีส้มและสีทอง สายลมอ่อนโยนพัดผ่านใบไม้",
        "note": "Thai",
    },
    "hi": {
        "voice": "hi-IN-SwaraNeural",
        "text": "सूर्य दूर के पहाड़ों के पीछे धीरे-धीरे अस्त होता है, आकाश को नारंगी और सुनहरे रंगों से रंग देता है। एक हल्की हवा पत्तियों से होकर गुज़रती है।",
        "note": "Hindi",
    },
    "id": {
        "voice": "id-ID-GadisNeural",
        "text": "Matahari terbenam perlahan di balik pegunungan yang jauh, mewarnai langit dengan nuansa jingga dan emas. Angin sepoi-sepoi bergerak di antara dedaunan.",
        "note": "Indonesian",
    },
    "ms": {
        "voice": "ms-MY-YasminNeural",
        "text": "Matahari terbenam perlahan-lahan di sebalik gunung-ganang yang jauh, melukis langit dengan warna jingga dan emas. Angin sepoi-sepoi bergerak melalui dedaunan.",
        "note": "Malay",
    },
    "sv": {
        "voice": "sv-SE-SofieNeural",
        "text": "Solen sjunker långsamt bakom de avlägsna bergen och målar himlen i nyanser av orange och guld. En mild bris rör sig genom löven.",
        "note": "Swedish",
    },
    "da": {
        "voice": "da-DK-ChristelNeural",
        "text": "Solen synker langsomt bag de fjerne bjerge og maler himlen i nuancer af orange og guld. En blid brise bevæger sig gennem bladene.",
        "note": "Danish",
    },
    "fi": {
        "voice": "fi-FI-NooraNeural",
        "text": "Aurinko laskee hitaasti kaukaisten vuorten taakse maalaten taivaan oranssin ja kullan sävyillä. Lempeä tuulenvire liikkuu lehtien läpi.",
        "note": "Finnish",
    },
    "nb": {
        "voice": "nb-NO-PernilleNeural",
        "text": "Solen synker sakte bak de fjerne fjellene og maler himmelen i nyanser av oransje og gull. En mild bris beveger seg gjennom bladene.",
        "note": "Norwegian (Bokmål)",
    },
    "cs": {
        "voice": "cs-CZ-VlastaNeural",
        "text": "Slunce pomalu zapadá za vzdálené hory a maluje oblohu odstíny oranžové a zlaté. Jemný vánek se pohybuje listím stromů.",
        "note": "Czech",
    },
    "hu": {
        "voice": "hu-HU-NoemiNeural",
        "text": "A nap lassan lenyugszik a távoli hegyek mögé, narancs és arany árnyalatokkal festve az eget. Enyhe szellő mozgatja a leveleket.",
        "note": "Hungarian",
    },
    "ro": {
        "voice": "ro-RO-AlinaNeural",
        "text": "Soarele apune încet peste munții îndepărtați, pictând cerul în nuanțe de portocaliu și auriu. O briză blândă mișcă frunzele copacilor.",
        "note": "Romanian",
    },
    "uk": {
        "voice": "uk-UA-PolinaNeural",
        "text": "Сонце повільно сідає за далекі гори, фарбуючи небо в помаранчеві та золоті відтінки. Легкий вітерець ворушить листя дерев.",
        "note": "Ukrainian",
    },
    "el": {
        "voice": "el-GR-AthinaNeural",
        "text": "Ο ήλιος δύει αργά πίσω από τα μακρινά βουνά, βάφοντας τον ουρανό με αποχρώσεις πορτοκαλί και χρυσού. Μια απαλή αύρα κινείται μέσα από τα φύλλα.",
        "note": "Greek",
    },
    "he": {
        "voice": "he-IL-HilaNeural",
        "text": "השמש שוקעת לאט מאחורי ההרים הרחוקים, צובעת את השמיים בגוני כתום וזהב. רוח קלה עוברת בין העלים.",
        "note": "Hebrew",
    },
    "bn": {
        "voice": "bn-IN-TanishaaNeural",
        "text": "সূর্য ধীরে ধীরে দূরের পাহাড়ের পিছনে অস্ত যায়, আকাশকে কমলা ও সোনালি রঙে রাঙিয়ে দেয়। একটি মৃদু বাতাস পাতার মধ্য দিয়ে বয়ে যায়।",
        "note": "Bengali",
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

    run_only = {"en", "zh", "ja", "ko", "es", "fr", "de", "ar"}
    tasks = [process_language(lang, cfg) for lang, cfg in LANGUAGES.items() if lang in run_only]
    await asyncio.gather(*tasks)

    # Summary
    print("\n=== Generated files ===")
    for lang, cfg in {k: v for k, v in LANGUAGES.items() if k in run_only}.items():
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
