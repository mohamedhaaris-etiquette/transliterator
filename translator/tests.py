from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class TranslatorViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", email="tester@example.com", password="SafePass!2468"
        )

    def test_landing_page(self):
        self.assertEqual(self.client.get(reverse("translator:landing")).status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("translator:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_history_for_authenticated_user(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("translator:history")).status_code, 200)
