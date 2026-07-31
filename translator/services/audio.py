import os
import platform
import tempfile
import time
import wave

import numpy as np

CHUNK_SECONDS = 4


def _require_windows_audio():
    if platform.system() != "Windows":
        raise RuntimeError("System/microphone server capture in this build requires Windows. Run Django on the Windows PC whose audio you want to capture.")
    try:
        import pyaudiowpatch as pyaudio
        return pyaudio
    except ImportError as exc:
        raise RuntimeError("PyAudioWPatch is not installed. Run: pip install PyAudioWPatch") from exc


def record_loopback_chunk(stop_event, seconds=CHUNK_SECONDS):
    pyaudio = _require_windows_audio()
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not speakers.get("isLoopbackDevice", False):
            for loopback in p.get_loopback_device_info_generator():
                if speakers["name"] in loopback["name"]:
                    speakers = loopback
                    break
            else:
                raise RuntimeError("No WASAPI loopback device matches the default playback device.")
        return _record_device(p, pyaudio, speakers, stop_event, "system", threshold=250, seconds=seconds)
    finally:
        p.terminate()


def record_mic_chunk(stop_event, seconds=CHUNK_SECONDS):
    pyaudio = _require_windows_audio()
    p = pyaudio.PyAudio()
    try:
        mic = p.get_default_input_device_info()
        return _record_device(p, pyaudio, mic, stop_event, "mic", threshold=80, seconds=seconds)
    finally:
        p.terminate()


def _record_device(p, pyaudio, device, stop_event, prefix, threshold, seconds):
    channels = max(1, int(device.get("maxInputChannels", 1)))
    rate = int(device.get("defaultSampleRate", 16000))
    chunk_size = 1024
    max_frames = int(rate * seconds)
    frames = []
    read = 0
    silence_frames = 0
    has_audio = False
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=device["index"],
    )
    try:
        while read < max_frames and not stop_event.is_set():
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
            read += chunk_size
            audio_arr = np.frombuffer(data, dtype=np.int16)
            level = float(np.abs(audio_arr).mean()) if audio_arr.size else 0
            if level > threshold:
                has_audio = True
                silence_frames = 0
            elif has_audio:
                silence_frames += chunk_size
                if silence_frames > rate * 0.2:
                    break
            elif read > rate * 2.5:
                break
    finally:
        stream.stop_stream()
        stream.close()

    path = os.path.join(tempfile.gettempdir(), f"signal_{prefix}_{int(time.time() * 1000)}.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))
    return path


def audio_level(wav_path):
    try:
        with wave.open(wav_path, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        return float(np.abs(audio).mean()) if audio.size else 0.0
    except Exception:
        return 0.0
