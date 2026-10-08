from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    AdminNotification,
    Payment,
    SubscriptionPlan,
    UserSubscription,
)
from .services import activate_plan, get_usage_state


@login_required
def plans(request):
    state = get_usage_state(request.user)

    return render(
        request,
        "subscription_plans.html",
        {
            "plans": SubscriptionPlan.objects.filter(is_active=True),
            "current_plan": state["plan"].code,
            "usage_state": state,
        },
    )


@login_required
def choose_free(request):
    if request.method != "POST":
        raise Http404

    plan = get_object_or_404(
        SubscriptionPlan,
        code=SubscriptionPlan.PlanCode.FREE,
        is_active=True,
    )
    activate_plan(request.user, plan)
    return redirect("/main/")


@login_required
def payment(request):
    plan_code = (
        request.POST.get("plan")
        or request.GET.get("plan")
        or ""
    ).strip().lower()

    plan = get_object_or_404(
        SubscriptionPlan,
        code=plan_code,
        is_active=True,
    )

    if plan.code == SubscriptionPlan.PlanCode.FREE:
        return redirect("subscriptions:plans")

    if request.method == "POST":
        method = request.POST.get("payment_method", "")
        valid_methods = {value for value, _ in Payment.Method.choices}

        if method not in valid_methods:
            return render(
                request,
                "payment.html",
                {
                    "plan": plan,
                    "payment_methods": Payment.Method.choices,
                    "error": "Select a valid payment method.",
                },
                status=400,
            )

        payment_record = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            payment_method=method,
            status=Payment.Status.PENDING,
        )

        if getattr(settings, "SUBSCRIPTION_TEST_PAYMENT_MODE", False):
            payment_record.status = Payment.Status.SUCCESS
            payment_record.paid_at = timezone.now()
            payment_record.provider_payment_id = f"test_{payment_record.pk}"
            payment_record.save()

            activate_plan(request.user, plan, payment_record)
            return redirect("subscriptions:payment_success")

        return render(
            request,
            "payment.html",
            {
                "plan": plan,
                "payment_methods": Payment.Method.choices,
                "error": "Razorpay live integration is not enabled yet.",
            },
            status=503,
        )

    return render(
        request,
        "payment.html",
        {
            "plan": plan,
            "payment_methods": Payment.Method.choices,
        },
    )


@login_required
def payment_success(request):
    return render(
        request,
        "payment_success.html",
        {"usage_state": get_usage_state(request.user)},
    )


@login_required
def subscription_dashboard(request):
    return render(
        request,
        "subscription_dashboard.html",
        {
            "usage_state": get_usage_state(request.user),
            "payments": Payment.objects.filter(
                user=request.user
            ).select_related("plan")[:20],
        },
    )


def super_admin_required(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(super_admin_required)
def admin_dashboard(request):
    successful_payments = Payment.objects.filter(
        status=Payment.Status.SUCCESS
    )

    return render(
        request,
        "subscription_admin_dashboard.html",
        {
            "total_subscriptions": UserSubscription.objects.count(),
            "active_subscriptions": UserSubscription.objects.filter(
                status=UserSubscription.Status.ACTIVE
            ).count(),
            "free_users": UserSubscription.objects.filter(
                plan__code=SubscriptionPlan.PlanCode.FREE
            ).count(),
            "paid_users": UserSubscription.objects.exclude(
                plan__code=SubscriptionPlan.PlanCode.FREE
            ).count(),
            "revenue": successful_payments.aggregate(
                total=Sum("amount")
            )["total"] or 0,
            "recent_payments": Payment.objects.select_related(
                "user", "plan"
            )[:20],
            "notifications": AdminNotification.objects.select_related(
                "user"
            )[:20],
        },
    )
