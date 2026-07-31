import asyncio
import os
import threading
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import Transcript, TranslationSession
from .services.audio import audio_level, record_loopback_chunk, record_mic_chunk
from .services.translation import transcribe, translate_text


class TranslationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.stop_event = threading.Event()
        self.worker_threads = []
        self.session_id = None
        self.source_lang = "auto"
        self.target_lang = "en"
        self.audio_source = "system"
        self.running = False
        self.loop = asyncio.get_running_loop()
        await self.accept()
        await self.send_json({"type": "status", "running": False})

    async def disconnect(self, close_code):
        await self._stop(mark_status=True)

    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if action == "start_translation":
            await self._start(content)
        elif action == "stop_translation":
            await self._stop(mark_status=True)
        elif action == "change_target_language":
            self.target_lang = content.get("target_lang") or "en"
        elif action == "toggle_mute":
            await self._toggle_mute(bool(content.get("mute")))
        else:
            await self.send_json({"type": "error", "message": "Unknown WebSocket action."})

    async def _start(self, content):
        if self.running:
            return
        self.source_lang = content.get("source_lang") or "auto"
        self.target_lang = content.get("target_lang") or "en"
        self.audio_source = content.get("source") or "system"
        if self.audio_source not in {"system", "mic", "both"}:
            self.audio_source = "system"
        self.session_id = await self._create_session()
        self.stop_event.clear()
        self.running = True
        recorders = []
        if self.audio_source in {"system", "both"}:
            recorders.append((record_loopback_chunk, "system"))
        if self.audio_source in {"mic", "both"}:
            recorders.append((record_mic_chunk, "mic"))
        for recorder, label in recorders:
            thread = threading.Thread(target=self._worker, args=(recorder, label, self.session_id), daemon=True)
            self.worker_threads.append(thread)
            thread.start()
        await self.send_json({"type": "status", "running": True})

    async def _stop(self, mark_status=True):
        if not getattr(self, "running", False) and not getattr(self, "session_id", None):
            return
        self.stop_event.set()
        self.running = False
        session_id = self.session_id
        if mark_status and session_id:
            await self._finish_session(session_id, "completed", "")
        self.session_id = None
        self.worker_threads = []
        try:
            await self.send_json({"type": "status", "running": False})
        except Exception:
            pass

    def _worker(self, recorder, source_label, session_id):
        while not self.stop_event.is_set():
            wav_path = None
            try:
                wav_path = recorder(self.stop_event)
                level = audio_level(wav_path)
                silent = level < 20
                self._emit({
                    "type": "debug", "source": source_label, "level": round(level, 1),
                    "silent": silent, "timestamp": time.strftime("%H:%M:%S"),
                })
                if silent or self.stop_event.is_set():
                    continue
                text, detected = transcribe(wav_path, self.source_lang)
                if not text:
                    continue
                translated = translate_text(text, self.target_lang)
                payload = {
                    "type": "translation_result",
                    "source": source_label,
                    "original": text,
                    "detected_lang": detected,
                    "translated": translated,
                    "target_lang": self.target_lang,
                    "timestamp": time.strftime("%H:%M:%S"),
                }
                self._emit(payload)
                if session_id:
                    asyncio.run_coroutine_threadsafe(
                        self._save_transcript(session_id, source_label, text, translated, detected, self.target_lang), self.loop
                    )
            except Exception as exc:
                message = str(exc)
                self._emit({"type": "error", "message": f"[{source_label}] {message}"})
                if session_id:
                    asyncio.run_coroutine_threadsafe(self._finish_session(session_id, "failed", message), self.loop)
                self.stop_event.set()
                self.running = False
                self._emit({"type": "status", "running": False})
                break
            finally:
                if wav_path:
                    try:
                        os.remove(wav_path)
                    except OSError:
                        pass

    def _emit(self, payload):
        if not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.send_json(payload), self.loop)

    async def _toggle_mute(self, mute_state):
        try:
            import comtypes
            from pycaw.pycaw import AudioUtilities
            comtypes.CoInitialize()
            try:
                AudioUtilities.GetSpeakers().EndpointVolume.SetMute(1 if mute_state else 0, None)
            finally:
                comtypes.CoUninitialize()
            await self.send_json({"type": "info", "message": f"System sound {'muted' if mute_state else 'unmuted'}."})
        except Exception as exc:
            await self.send_json({"type": "error", "message": f"Mute is available only on a configured Windows host: {exc}"})

    @database_sync_to_async
    def _create_session(self):
        return TranslationSession.objects.create(
            user=self.user,
            source_language=self.source_lang,
            target_language=self.target_lang,
            audio_source=self.audio_source,
            status="running",
        ).pk

    @database_sync_to_async
    def _save_transcript(self, session_id, source, original, translated, detected, target):
        if TranslationSession.objects.filter(pk=session_id, user=self.user).exists():
            Transcript.objects.create(
                session_id=session_id,
                audio_source=source,
                original_text=original,
                translated_text=translated,
                detected_language=detected or "auto",
                target_language=target,
            )

    @database_sync_to_async
    def _finish_session(self, session_id, status, error_message):
        TranslationSession.objects.filter(pk=session_id, user=self.user, ended_at__isnull=True).update(
            status=status,
            error_message=error_message,
            ended_at=timezone.now(),
        )
