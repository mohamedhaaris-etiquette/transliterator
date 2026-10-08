from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    AdminNotification,
    DailyUsage,
    SubscriptionHistory,
    SubscriptionPlan,
    UserSubscription,
)


class SubscriptionLimitExceeded(Exception):
    pass


def get_free_plan():
    return SubscriptionPlan.objects.get(
        code=SubscriptionPlan.PlanCode.FREE,
        is_active=True,
    )


@transaction.atomic
def get_or_create_subscription(user):
    subscription = (
        UserSubscription.objects
        .select_for_update()
        .select_related("plan")
        .filter(user=user)
        .first()
    )

    if subscription is None:
        free_plan = get_free_plan()
        subscription = UserSubscription.objects.create(
            user=user,
            plan=free_plan,
            status=UserSubscription.Status.ACTIVE,
            started_at=timezone.now(),
            expires_at=None,
            total_used_seconds=0,
        )

        SubscriptionHistory.objects.create(
            user=user,
            plan=free_plan,
            started_at=subscription.started_at,
            expires_at=None,
            status=subscription.status,
        )

    if (
        subscription.status == UserSubscription.Status.ACTIVE
        and subscription.expires_at
        and subscription.expires_at <= timezone.now()
    ):
        subscription.status = UserSubscription.Status.EXPIRED
        subscription.save(update_fields=["status", "updated_at"])

    return subscription


@transaction.atomic
def activate_plan(user, plan, payment=None):
    now = timezone.now()
    expires_at = now + timedelta(days=plan.validity_days) if plan.validity_days else None

    subscription, _ = UserSubscription.objects.select_for_update().get_or_create(
        user=user,
        defaults={
            "plan": plan,
            "status": UserSubscription.Status.ACTIVE,
            "started_at": now,
            "expires_at": expires_at,
            "total_used_seconds": 0,
        },
    )

    subscription.plan = plan
    subscription.status = UserSubscription.Status.ACTIVE
    subscription.started_at = now
    subscription.expires_at = expires_at
    subscription.total_used_seconds = 0
    subscription.save()

    SubscriptionHistory.objects.create(
        user=user,
        plan=plan,
        payment=payment,
        started_at=now,
        expires_at=expires_at,
        status=UserSubscription.Status.ACTIVE,
    )

    AdminNotification.objects.create(
        user=user,
        title="New Subscription Purchased",
        message=(
            f"User: {user}\n"
            f"Plan: {plan.name}\n"
            f"Amount: ₹{plan.price}\n"
            f"Payment Status: Success\n"
            f"Date: {timezone.localdate()}"
        ),
    )

    return subscription


def get_usage_state(user):
    subscription = get_or_create_subscription(user)
    plan = subscription.plan

    if not subscription.is_currently_active:
        return {
            "allowed": False,
            "reason": "subscription_expired",
            "subscription": subscription,
            "plan": plan,
            "remaining_seconds": 0,
        }

    if plan.code == SubscriptionPlan.PlanCode.FREE:
        daily_usage, _ = DailyUsage.objects.get_or_create(
            user=user,
            usage_date=timezone.localdate(),
        )
        limit_seconds = (plan.daily_limit_minutes or 0) * 60
        remaining = max(0, limit_seconds - daily_usage.used_seconds)

    elif plan.total_limit_minutes:
        limit_seconds = plan.total_limit_minutes * 60
        remaining = max(0, limit_seconds - subscription.total_used_seconds)

    elif plan.fair_use_minutes:
        limit_seconds = plan.fair_use_minutes * 60
        remaining = max(0, limit_seconds - subscription.total_used_seconds)

    else:
        remaining = None

    return {
        "allowed": remaining is None or remaining > 0,
        "reason": "" if remaining is None or remaining > 0 else "usage_limit_reached",
        "subscription": subscription,
        "plan": plan,
        "remaining_seconds": remaining,
    }


def can_use_language(user, language_code):
    state = get_usage_state(user)
    if not state["allowed"]:
        return False

    plan = state["plan"]
    return plan.all_languages or language_code in plan.allowed_languages


def has_feature(user, feature_name):
    state = get_usage_state(user)
    if not state["allowed"]:
        return False

    plan = state["plan"]
    features = {
        "ai_voice": plan.ai_voice,
        "export": plan.export_enabled,
        "api_access": plan.api_access,
        "team_users": plan.team_users,
        "priority_support": plan.priority_support,
    }
    return bool(features.get(feature_name, False))


@transaction.atomic
def record_usage(user, seconds):
    if seconds <= 0:
        return get_usage_state(user)

    state = get_usage_state(user)

    if not state["allowed"]:
        raise SubscriptionLimitExceeded(
            "Your subscription usage limit has been reached."
        )

    remaining = state["remaining_seconds"]
    if remaining is not None and seconds > remaining:
        raise SubscriptionLimitExceeded(
            "This usage would exceed your remaining plan allowance."
        )

    subscription = (
        UserSubscription.objects
        .select_for_update()
        .select_related("plan")
        .get(user=user)
    )

    if subscription.plan.code == SubscriptionPlan.PlanCode.FREE:
        daily_usage, _ = DailyUsage.objects.select_for_update().get_or_create(
            user=user,
            usage_date=timezone.localdate(),
        )
        daily_usage.used_seconds += seconds
        daily_usage.save(update_fields=["used_seconds", "updated_at"])
    else:
        subscription.total_used_seconds += seconds
        subscription.save(update_fields=["total_used_seconds", "updated_at"])

    return get_usage_state(user)
