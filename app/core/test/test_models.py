"""
Tests for models
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from unittest.mock import patch

from core import models


def create_user(email="test@example.com", password="test123"):
    """Create and return a user"""
    user = get_user_model().objects.create_user(
        email=email,
        password=password
    )
    return user


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email(self):
        """Test creating user with email"""
        email = "test@example.com"
        password = "test123"
        user = create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new user"""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = create_user(email=email)
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_error(self):
        """Test ValueError raises when creating a user without an email"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('')

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe success"""
        user = create_user()
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description',
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_recipe_tag(self):
        """Test creating a recipe tag success"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')
        self.assertEqual(str(tag), tag.name)

    def test_create_recipe_ingradient(self):
        """Test creating a recipe ingredient success"""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user, name='Ingradient 1'
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_image_file_name_uuid(self, mock_uuid):
        """Test generate image path using uuid"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_patch(None, 'sample.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
