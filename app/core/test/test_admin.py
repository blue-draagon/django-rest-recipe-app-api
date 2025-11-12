"""
Test for the django admin modifications.
"""
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.tools import test_ok


class AdminSiteTests(TestCase):
    """Tests for Django admin."""

    def setUp(self):
        """Create user and client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            'admin@example.com',
            'test123'
        )
        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email="user@eveil.com",
            password="test123",
            name="Test user"
        )

    def test_users_list(self):
        """Test users listed on the page"""
        url = reverse("admin:core_user_changelist")
        response = self.client.get(url)
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)
        test_ok("test_users_list")

    def test_edit_user_page(self):
        """Test user displaying and editing page work"""
        url = reverse("admin:core_user_change", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        test_ok("test_edit_user_page")

    def test_create_user_page(self):
        """Test user creating page work"""
        url = reverse("admin:core_user_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        test_ok("test_create_user_page")
