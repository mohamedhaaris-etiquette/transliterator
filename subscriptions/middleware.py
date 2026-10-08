from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect

from .services import get_usage_state


class SubscriptionAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefixes = getattr(
            settings,
            "SUBSCRIPTION_PROTECTED_PREFIXES",
            ["/main/", "/languages/", "/history/"],
        )

        should_check = (
            request.user.is_authenticated
            and any(request.path.startswith(prefix) for prefix in prefixes)
        )

        if should_check:
            state = get_usage_state(request.user)
            if not state["allowed"]:
                if request.headers.get("Accept") == "application/json":
                    return JsonResponse(
                        {
                            "error": state["reason"],
                            "message": "Your plan usage limit has been reached.",
                        },
                        status=403,
                    )
                return redirect("subscriptions:plans")

        return self.get_response(request)
