from django.contrib import admin
from .models import (
    AdminNotification,
    DailyUsage,
    Payment,
    SubscriptionHistory,
    SubscriptionPlan,
    UserSubscription,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name", "code", "price", "validity_days",
        "is_active", "display_order",
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "plan", "status", "started_at",
        "expires_at", "total_used_seconds",
    )
    list_filter = ("status", "plan")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "user", "plan", "amount",
        "payment_method", "status", "created_at",
    )
    list_filter = ("status", "payment_method", "plan")


admin.site.register(DailyUsage)
admin.site.register(SubscriptionHistory)
admin.site.register(AdminNotification)
