from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import EmailLoginForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm, SignupForm
from .models import PasswordResetOTP

User = get_user_model()


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("translator:dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Your account was created successfully.")
        return redirect("translator:dashboard")
    return render(request, "signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("translator:dashboard")
    form = EmailLoginForm(request.POST or None, request=request)
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
            return redirect(next_url)
        return redirect("translator:dashboard")
    error = form.non_field_errors()[0] if form.non_field_errors() else ""
    return render(request, "login.html", {
        "form": form,
        "error": error,
        "email": request.POST.get("email", ""),
        "next_url": next_url,
    })


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("translator:dashboard")
    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            PasswordResetOTP.objects.filter(user=user, used_at__isnull=True).delete()
            otp_record, code = PasswordResetOTP.create_for_user(user)
            request.session["reset_otp_id"] = otp_record.pk
            request.session["reset_user_id"] = user.pk
            send_mail(
                "Your SIGNAL password reset code",
                f"Your SIGNAL verification code is {code}. It expires in 10 minutes.",
                None,
                [user.email],
                fail_silently=False,
            )
        messages.info(request, "If the email is registered, a 6-digit verification code has been sent.")
        return redirect("accounts:verify_otp")
    return render(request, "forgot.html", {"form": form})


def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect("translator:dashboard")
    otp_id = request.session.get("reset_otp_id")
    user_id = request.session.get("reset_user_id")
    if not otp_id or not user_id:
        return redirect("accounts:forgot_password")
    form = OTPVerificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        otp_record = PasswordResetOTP.objects.filter(pk=otp_id, user_id=user_id).first()
        if otp_record and otp_record.verify(form.cleaned_data["otp"]):
            request.session["reset_verified"] = True
            return redirect("accounts:reset_password")
        messages.error(request, "Invalid, expired, or over-attempted OTP.")
    return render(request, "Verifyotp.html", {"form": form})


def reset_password_view(request):
    if request.user.is_authenticated:
        return redirect("translator:dashboard")
    user_id = request.session.get("reset_user_id")
    if not user_id or not request.session.get("reset_verified"):
        return redirect("accounts:login")
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if not user:
        return redirect("accounts:forgot_password")
    form = ResetPasswordForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        user.set_password(form.cleaned_data["password"])
        user.save(update_fields=["password"])
        for key in ("reset_otp_id", "reset_user_id", "reset_verified"):
            request.session.pop(key, None)
        messages.success(request, "Password updated successfully. You can now log in.")
        return redirect("accounts:login")
    return render(request, "Resetpassword.html", {"form": form})
