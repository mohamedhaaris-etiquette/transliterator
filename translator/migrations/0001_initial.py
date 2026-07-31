from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="TranslationSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_language", models.CharField(default="auto", max_length=20)),
                ("target_language", models.CharField(default="en", max_length=20)),
                ("audio_source", models.CharField(choices=[("system", "System Audio"), ("mic", "Microphone"), ("both", "System Audio and Microphone")], default="system", max_length=10)),
                ("status", models.CharField(choices=[("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="running", max_length=12)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translation_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="Transcript",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("audio_source", models.CharField(default="system", max_length=20)),
                ("original_text", models.TextField()),
                ("translated_text", models.TextField()),
                ("detected_language", models.CharField(blank=True, default="auto", max_length=20)),
                ("target_language", models.CharField(default="en", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transcripts", to="translator.translationsession")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
