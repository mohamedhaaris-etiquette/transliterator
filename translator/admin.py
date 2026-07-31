from django.contrib import admin
from .models import Transcript, TranslationSession


class TranscriptInline(admin.TabularInline):
    model = Transcript
    extra = 0
    readonly_fields = ("audio_source", "original_text", "translated_text", "detected_language", "target_language", "created_at")


@admin.register(TranslationSession)
class TranslationSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "audio_source", "source_language", "target_language", "status", "started_at", "ended_at")
    list_filter = ("status", "audio_source", "started_at")
    search_fields = ("user__email", "user__username")
    inlines = [TranscriptInline]


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("session", "audio_source", "detected_language", "target_language", "created_at")
    search_fields = ("original_text", "translated_text", "session__user__email")
