from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("register", views.signup_view, name="register_legacy"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("forgotPassword", views.forgot_password_view, name="forgot_password_legacy"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("verifyOtp", views.verify_otp_view, name="verify_otp_legacy"),
    path("reset-password/", views.reset_password_view, name="reset_password"),
    path("resetPassword", views.reset_password_view, name="reset_password_legacy"),
]
