"""
Test for the Ingredient API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Return url for specific ingredient id"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='test@eveil.com', password='test123'):
    """Create and return a user"""
    return get_user_model().objects.create_user(
        email=email, password=password
    )


def create_ingredient(user, name):
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientApiTests(TestCase):
    """Test for no authenticate Ingredient API"""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_is_required(self):
        """Test authencation is required to access Ingredient API"""
        response = self.client.get(INGREDIENT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedIngredientAPITests(TestCase):
    """Test Ingredient API for authenticated user"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving the list of ingredients"""
        create_ingredient(user=self.user, name='Kale')
        create_ingredient(user=self.user, name='Vanilla')
        response = self.client.get(INGREDIENT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ingredients = Ingredient.objects.all().order_by('name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_user_only_access_self_ingredients(self):
        """Test list of ingredients is only for authencated user"""
        user_details = {'email': 'other@eveil.com'}
        other_user = create_user(**user_details)
        create_ingredient(user=other_user, name='Kale')
        create_ingredient(user=self.user, name='Vanilla')
        response = self.client.get(INGREDIENT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_update_ingredient(self):
        """Test updating ingredient object"""
        ingredient = create_ingredient(user=self.user, name='Vanilla')
        payload = {'name': 'Kale'}
        update_url = detail_url(ingredient.id)
        response = self.client.patch(update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredient_success(self):
        """Test deleting a ingredient"""
        ingredient = create_ingredient(user=self.user, name='To delete')
        delete_url = detail_url(ingredient.id)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filter ingredients assigned to recipe"""
        ingredient_1 = create_ingredient(user=self.user, name='Apple')
        ingredient_2 = create_ingredient(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            title='Apple Crumbe',
            time_minutes=5,
            price=Decimal('4.5'),
            user=self.user
        )
        recipe.ingredients.add(ingredient_1)
        response = self.client.get(
            INGREDIENT_URL, {'assigned_only': 1}
        )
        ingredient_1_serializer = IngredientSerializer(ingredient_1)
        ingredient_2_serializer = IngredientSerializer(ingredient_2)
        self.assertIn(ingredient_1_serializer.data, response.data)
        self.assertNotIn(ingredient_2_serializer.data, response.data)

    def test_filtered_ingredients_is_unique(self):
        """Test filtered ingredients has no duplicate"""
        ingredient = create_ingredient(user=self.user, name='Eggs')
        create_ingredient(user=self.user, name='Sugar')
        recipe_1 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=25,
            price=Decimal('14.5'),
            user=self.user
        )
        recipe_2 = Recipe.objects.create(
            title='Herb Eggs',
            time_minutes=50,
            price=Decimal('24.5'),
            user=self.user
        )
        recipe_1.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient)
        response = self.client.get(
            INGREDIENT_URL, {'assigned_only': 1}
        )
        self.assertEqual(len(response.data), 1)
