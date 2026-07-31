from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class SignupForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirmPassword = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def _validate_10_chars(self, password):
        """Password must be exactly 10 characters (any type)."""
        if not password:
            return
        if len(password) != 10:
            raise forms.ValidationError("Password must be exactly 10 characters.")

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        self._validate_10_chars(password)
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirmPassword")
        if password and confirm and password != confirm:
            self.add_error("confirmPassword", "Passwords do not match.")
        return cleaned

    def save(self):
        name = self.cleaned_data["name"].strip()
        email = self.cleaned_data["email"]
        base_username = email.split("@", 1)[0][:120] or "user"
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username[:115]}{suffix}"
        parts = name.split(maxsplit=1)
        return User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data["password"],
            first_name=parts[0] if parts else "",
            last_name=parts[1] if len(parts) > 1 else "",
        )


class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email", "").strip().lower()
        password = cleaned.get("password", "")
        if password and len(password) != 10:
            raise forms.ValidationError("Password must be exactly 10 characters.")
        if email and password:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                self.user = authenticate(self.request, username=user.username, password=password)
            if not self.user:
                raise forms.ValidationError("Invalid email or password.")
            if not self.user.is_active:
                raise forms.ValidationError("This account is inactive.")
        return cleaned

    def get_user(self):
        return self.user


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()


class OTPVerificationForm(forms.Form):
    otp = forms.RegexField(regex=r"^\d{6}$", error_messages={"invalid": "Enter the 6-digit OTP."})


class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    confirmPassword = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password", "")
        confirm = cleaned.get("confirmPassword", "")
        if password and len(password) != 10:
            self.add_error("password", "Password must be exactly 10 characters.")
        if password and confirm and password != confirm:
            self.add_error("confirmPassword", "Passwords do not match.")
        return cleaned
