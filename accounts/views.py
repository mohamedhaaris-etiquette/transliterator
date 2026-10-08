from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import (
    EmailLoginForm,
    ForgotPasswordForm,
    OTPVerificationForm,
    ResetPasswordForm,
    SignupForm,
)
from .models import PasswordResetOTP


User = get_user_model()


def signup_view(request):
    """
    New user account create view.

    
    """

    if request.user.is_authenticated:
        return redirect("subscriptions:plans")

    form = SignupForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        messages.success(
            request,
            "Your account was created successfully.",
        )

        # 
        return redirect("subscriptions:plans")

    return render(
        request,
        "signup.html",
        {
            "form": form,
        },
    )


def login_view(request):
    """
    Existing user login view.

    
    """

    if request.user.is_authenticated:
        return redirect("subscriptions:plans")

    form = EmailLoginForm(
        request.POST or None,
        request=request,
    )

    if request.method == "POST" and form.is_valid():
        login(
            request,
            form.get_user(),
        )

        messages.success(
            request,
            "Login successful.",
        )

        # Requirement:
        # 
        return redirect("subscriptions:plans")

    error = (
        form.non_field_errors()[0]
        if form.non_field_errors()
        else ""
    )

    return render(
        request,
        "login.html",
        {
            "form": form,
            "error": error,
            "email": request.POST.get(
                "email",
                "",
            ),
            "next_url": "",
        },
    )


@login_required
def logout_view(request):
    """
    User logout view.
    """

    logout(request)

    return redirect(
        "accounts:login"
    )


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect("subscriptions:plans")

    form = ForgotPasswordForm(request.POST or None)
    error_message = None

    if request.method == "POST" and form.is_valid():
        email = (
            form.cleaned_data["email"]
            .strip()
            .lower()
        )

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).first()

        if user:
            PasswordResetOTP.objects.filter(
                user=user,
                used_at__isnull=True,
            ).delete()

            otp_record, code = PasswordResetOTP.create_for_user(user)

            request.session["reset_otp_id"] = otp_record.pk
            request.session["reset_user_id"] = user.pk

            send_mail(
                "Your SIGNAL password reset code",
                (
                    f"Your SIGNAL verification code "
                    f"is {code}. It expires in 10 minutes."
                ),
                None,
                [user.email],
                fail_silently=False,
            )

            messages.info(
                request,
                "A 6-digit verification code has been sent to your email."
            )
            return redirect("accounts:verify_otp")
        else:
            error_message = "Invalid email address."

    return render(
        request,
        "forgot.html",
        {
            "form": form,
            "error": error_message,
        },
    )


def verify_otp_view(request):
   

    if request.user.is_authenticated:
        return redirect("subscriptions:plans")

    otp_id = request.session.get(
        "reset_otp_id"
    )

    user_id = request.session.get(
        "reset_user_id"
    )

    if not otp_id or not user_id:
        return redirect(
            "accounts:forgot_password"
        )

    form = OTPVerificationForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        otp_record = PasswordResetOTP.objects.filter(
            pk=otp_id,
            user_id=user_id,
        ).first()

        if otp_record and otp_record.verify(
            form.cleaned_data["otp"]
        ):
            request.session[
                "reset_verified"
            ] = True

            return redirect(
                "accounts:reset_password"
            )

        messages.error(
            request,
            (
                "Invalid, expired, or "
                "over-attempted OTP."
            ),
        )

    return render(
        request,
        "Verifyotp.html",
        {
            "form": form,
        },
    )


def reset_password_view(request):
   

    if request.user.is_authenticated:
        return redirect("subscriptions:plans")

    user_id = request.session.get(
        "reset_user_id"
    )

    reset_verified = request.session.get(
        "reset_verified"
    )

    if not user_id or not reset_verified:
        return redirect(
            "accounts:login"
        )

    user = User.objects.filter(
        pk=user_id,
        is_active=True,
    ).first()

    if not user:
        return redirect(
            "accounts:forgot_password"
        )

    form = ResetPasswordForm(
        request.POST or None,
        user=user,
    )

    if request.method == "POST" and form.is_valid():
        user.set_password(
            form.cleaned_data["password"]
        )

        user.save(
            update_fields=["password"]
        )

        for key in (
            "reset_otp_id",
            "reset_user_id",
            "reset_verified",
        ):
            request.session.pop(
                key,
                None,
            )

        messages.success(
            request,
            (
                "Password updated successfully. "
                "You can now log in."
            ),
        )

        return redirect(
            "accounts:login"
        )

    return render(
        request,
        "Resetpassword.html",
        {
            "form": form,
        },
    )