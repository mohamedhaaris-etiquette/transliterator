from django.urls import path

from . import views


app_name = "subscriptions"


urlpatterns = [
    path(
        "plans/",
        views.plans,
        name="plans",
    ),

    path(
        "plans/free/",
        views.choose_free,
        name="choose_free",
    ),

    path(
        "payment/",
        views.payment,
        name="payment",
    ),

    path(
        "payment/success/",
        views.payment_success,
        name="payment_success",
    ),

    path(
        "subscription/",
        views.subscription_dashboard,
        name="dashboard",
    ),

    path(
        "subscription/admin/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
]