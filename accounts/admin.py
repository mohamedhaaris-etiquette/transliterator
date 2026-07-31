from django.contrib import admin
from .models import PasswordResetOTP


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at", "attempts")
    list_filter = ("used_at", "created_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("otp_hash", "created_at", "used_at", "attempts")
