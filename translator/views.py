from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import json

from .models import TranslationSession
from .services.translation import supported_languages
from .services.tts import text_to_speech


def landing(request):
    return render(request, "landingpage.html")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    display_name = request.user.get_full_name().strip() or request.user.username
    initial = display_name[:1].upper() if display_name else "U"
    recent_sessions = TranslationSession.objects.filter(user=request.user)[:8]
    return render(request, "index.html", {
        "username": display_name,
        "user_initial": initial,
        "recent_sessions": recent_sessions,
    })


@login_required
def history(request):
    sessions = (
        TranslationSession.objects.filter(user=request.user)
        .prefetch_related("transcripts")[:50]
    )
    return render(request, "history.html", {"sessions": sessions})


@require_GET
def languages(request):
    return JsonResponse(supported_languages())


@login_required
@require_POST
def speak(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        text = str(payload.get("text", "")).strip()
        lang = str(payload.get("lang", "en")).strip() or "en"
        if not text:
            return JsonResponse({"error": "No text supplied."}, status=400)
        if len(text) > 2500:
            return JsonResponse({"error": "Text is too long for speech playback."}, status=400)
        path = text_to_speech(text, lang)
        response = FileResponse(open(path, "rb"), content_type="audio/mpeg")
        response["Content-Disposition"] = 'inline; filename="signal-translation.mp3"'
        return response
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
