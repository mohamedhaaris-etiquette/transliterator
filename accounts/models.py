from datetime import timedelta
import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_otps")
    otp_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def create_for_user(cls, user):
        code = f"{secrets.randbelow(1_000_000):06d}"
        record = cls.objects.create(
            user=user,
            otp_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        return record, code

    def verify(self, code):
        if self.used_at or self.expires_at <= timezone.now() or self.attempts >= 5:
            return False
        self.attempts += 1
        valid = secrets.compare_digest(
            self.otp_hash,
            hashlib.sha256(str(code).strip().encode("utf-8")).hexdigest(),
        )
        if valid:
            self.used_at = timezone.now()
        self.save(update_fields=["attempts", "used_at"])
        return valid

    def __str__(self):
        return f"OTP for {self.user.email or self.user.username}"
