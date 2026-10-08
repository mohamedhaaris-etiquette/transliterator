from django.conf import settings
from django.db import models

from .fields import EncryptedTextField


class TranslationSession(models.Model):
    SOURCE_CHOICES = [
        ("system", "System Audio"),
        ("mic", "Microphone"),
        ("both", "System Audio and Microphone"),
    ]
    STATUS_CHOICES = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="translation_sessions")
    source_language = models.CharField(max_length=20, default="auto")
    target_language = models.CharField(max_length=20, default="en")
    audio_source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default="system")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} · {self.source_language} → {self.target_language}"


class Transcript(models.Model):
    session = models.ForeignKey(TranslationSession, on_delete=models.CASCADE, related_name="transcripts")
    audio_source = models.CharField(max_length=20, default="system")
    original_text = EncryptedTextField()
    translated_text =EncryptedTextField()
    detected_language = models.CharField(max_length=20, blank=True, default="auto")
    target_language = models.CharField(max_length=20, default="en")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.original_text[:80]






