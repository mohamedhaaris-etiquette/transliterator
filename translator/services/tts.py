import asyncio
import os
import tempfile
import edge_tts

VOICE_MAP = {
    "en": "en-US-JennyNeural", "hi": "hi-IN-SwaraNeural", "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural", "kn": "kn-IN-SapnaNeural", "ml": "ml-IN-SobhanaNeural",
    "fr": "fr-FR-DeniseNeural", "es": "es-ES-ElviraNeural", "de": "de-DE-KatjaNeural",
    "ja": "ja-JP-NanamiNeural", "zh-CN": "zh-CN-XiaoxiaoNeural",
}


async def _synthesize(text, voice, out_path):
    await edge_tts.Communicate(text, voice).save(out_path)


def text_to_speech(text, lang_code):
    voice = VOICE_MAP.get(lang_code, "en-US-JennyNeural")
    out_path = os.path.join(tempfile.gettempdir(), f"signal_tts_{abs(hash((text, lang_code)))}.mp3")
    asyncio.run(_synthesize(text, voice, out_path))
    return out_path
