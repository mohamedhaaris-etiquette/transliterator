import speech_recognition as sr
from deep_translator import GoogleTranslator

recognizer = sr.Recognizer()


def supported_languages():
    try:
        return GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception:
        return {
            "english": "en", "tamil": "ta", "hindi": "hi", "malayalam": "ml",
            "telugu": "te", "kannada": "kn", "french": "fr", "spanish": "es",
            "german": "de", "japanese": "ja", "korean": "ko", "chinese (simplified)": "zh-CN",
        }


def transcribe(wav_path, source_lang="auto"):
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        language = None if source_lang in {"", "auto", None} else source_lang
        text = recognizer.recognize_google(audio, language=language) if language else recognizer.recognize_google(audio)
        return text.strip(), source_lang or "auto"
    except sr.UnknownValueError:
        return "", "auto"
    except Exception as exc:
        raise RuntimeError(f"Speech recognition failed: {exc}") from exc


def translate_text(text, target_lang):
    if not text:
        return ""
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as exc:
        raise RuntimeError(f"Translation failed: {exc}") from exc
