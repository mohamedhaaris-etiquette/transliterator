from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountFlowTests(TestCase):
    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(reverse("accounts:signup"), {
            "name": "Test User",
            "email": "test@example.com",
            "password": "SafePass!2468",
            "confirmPassword": "SafePass!2468",
        })
        self.assertRedirects(response, reverse("translator:dashboard"))
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_email_login(self):
        User.objects.create_user(username="person", email="person@example.com", password="SafePass!2468")
        response = self.client.post(reverse("accounts:login"), {
            "email": "person@example.com",
            "password": "SafePass!2468",
        })
        self.assertRedirects(response, reverse("translator:dashboard"))
