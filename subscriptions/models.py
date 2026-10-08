from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    class PlanCode(models.TextChoices):
        FREE = "free", "Free"
        BASIC = "basic", "Basic"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    code = models.CharField(max_length=20, choices=PlanCode.choices, unique=True)
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    validity_days = models.PositiveIntegerField(null=True, blank=True)

    daily_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    total_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    fair_use_minutes = models.PositiveIntegerField(null=True, blank=True)

    allowed_languages = models.JSONField(default=list, blank=True)
    all_languages = models.BooleanField(default=False)

    ai_voice = models.BooleanField(default=False)
    export_enabled = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    team_users = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "price"]

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="current_subscription",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="user_subscriptions",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    total_used_seconds = models.PositiveBigIntegerField(default=0)
    auto_renew = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_currently_active(self):
        if self.status != self.Status.ACTIVE:
            return False
        return not self.expires_at or self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.user} - {self.plan.name}"


class DailyUsage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_daily_usage",
    )
    usage_date = models.DateField(default=timezone.localdate)
    used_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "usage_date"],
                name="unique_daily_subscription_usage",
            )
        ]
        ordering = ["-usage_date"]

    def __str__(self):
        return f"{self.user} - {self.usage_date}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        GPAY = "gpay", "Google Pay"
        PHONEPE = "phonepe", "PhonePe"
        PAYTM = "paytm", "Paytm"
        UPI = "upi", "UPI"
        CREDIT_CARD = "credit_card", "Credit Card"
        DEBIT_CARD = "debit_card", "Debit Card"
        NET_BANKING = "net_banking", "Net Banking"
        RAZORPAY = "razorpay", "Razorpay"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    payment_method = models.CharField(max_length=30, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    provider_order_id = models.CharField(max_length=150, blank=True)
    provider_payment_id = models.CharField(max_length=150, blank=True)
    provider_signature = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.plan.name} - {self.status}"


class SubscriptionHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_history",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="history_records",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_history_records",
    )
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AdminNotification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_admin_notifications",
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
