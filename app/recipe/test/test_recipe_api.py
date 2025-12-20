"""
Test for recipe API
"""
from decimal import Decimal
from os import path
import tempfile

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return url for specific recipe id"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """Return url for specific recipe id"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a recipe"""
    defaults = {
        'title': 'Recipe title',
        'description': 'Recipe description',
        'time_minutes': 22,
        'price': Decimal('5.21'),
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test recipe API for no authenticated user"""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_is_required(self):
        """Test authencation is required to access Recipe API"""
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRecipeAPITests(TestCase):
    """Test recipe API for authenticated user"""

    def setUp(self):
        user_details = {
            'email': 'test@eveil.com',
            'password': 'test123',
        }
        self.user = create_user(**user_details)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # Test recipe CRUD operations
    # ---------------------------------------------------------------------
    def test_retrieve_recipe_list(self):
        """Test retrieving the list of recipes"""
        create_recipe(self.user)
        create_recipe(self.user)
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_user_only_access_self_recipe(self):
        """Test list of recipes is only for authencated user"""
        user_details = {
            'email': 'other@eveil.com',
            'password': 'test123',
        }
        other_user = create_user(**user_details)
        create_recipe(user=other_user)
        create_recipe(user=self.user)
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_recipe_detail(self):
        """Test get detail of recipe"""
        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'Recipe title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
        }
        response = self.client.post(RECIPES_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating part of recipe object"""
        original_link = 'http://example.com/recipe.pdf'
        time_minutes = 25
        recipe = create_recipe(
            user=self.user,
            title='Recipe title',
            time_minutes=time_minutes,
            price=Decimal('5.21'),
            link=original_link
        )
        payload = {'title': 'new title', 'price': Decimal('4.31')}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.time_minutes, time_minutes)
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_fully_update_recipe(self):
        """Test totaly updating recipe object"""
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'new title',
            'description': 'new title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
            'link': 'http://example.com/new-recipe.pdf',
        }
        update_url = detail_url(recipe.id)
        response = self.client.put(update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_recipe_user_not_success(self):
        """Test no change if trying to update recipe user"""
        recipe = create_recipe(user=self.user)
        user_details = {
            'email': 'newuser@eveil.com',
            'password': 'test123',
        }
        new_user = create_user(**user_details)
        payload = {'user': new_user}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe_success(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        delete_url = detail_url(recipe.id)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test error when try to delete others users recipe"""
        user_details = {
            'email': 'newuser@eveil.com',
            'password': 'test123',
        }
        new_user = create_user(**user_details)
        recipe = create_recipe(user=new_user)
        delete_url = detail_url(recipe.id)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    # Test recipe and tag relationship
    # ---------------------------------------------------------------------
    def test_create_recipe_with_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Recipe title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
            'tags': [
                {'name': 'Thai'},
                {'name': 'Dinner'},
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                user=self.user,
                name=tag['name']
            ).exists())

    def test_create_recipe_with_existing_tag(self):
        """Test creating recipe with an existing tag"""
        tag_dinner = Tag.objects.create(user=self.user, name='Dinner')
        payload = {
            'title': 'Recipe title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
            'tags': [
                {'name': 'Dinner'},
                {'name': 'Breakfast'},
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_dinner, recipe.tags.all())
        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                user=self.user,
                name=tag['name']
            ).exists())

    def test_create_tag_on_recipe_update(self):
        """Test creating a tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_with_existing_tag(self):
        """Test assiging an existing tag when update recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test update recipe clear all tags"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        payload = {'tags': []}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    # Test recipe and ingredient relationship
    # ---------------------------------------------------------------------
    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            'title': 'Recipe title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
            'ingredients': [
                {'name': 'Salt'},
                {'name': 'Sugar'},
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists())

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating recipe with an existing ingredient"""
        salt = Ingredient.objects.create(user=self.user, name='Salt')
        payload = {
            'title': 'Recipe title',
            'time_minutes': 22,
            'price': Decimal('5.21'),
            'ingredients': [
                {'name': 'Salt'},
                {'name': 'Sugar'},
            ]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=response.data['id'])
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(salt, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists())

    def test_create_ingredient_on_recipe_update(self):
        """Test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Salt'}]}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        ingredient = Ingredient.objects.get(user=self.user, name='Salt')
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_update_recipe_with_existing_ingredient(self):
        """Test assiging an existing ingredient when update recipe"""
        salt = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(salt)
        sugar = Ingredient.objects.create(user=self.user, name='Sugar')
        payload = {'ingredients': [{'name': 'Sugar'}]}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertIn(sugar, recipe.ingredients.all())
        self.assertNotIn(salt, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test update recipe clear all ingredients"""
        salt = Ingredient.objects.create(user=self.user, name='Salt')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(salt)
        payload = {'ingredients': []}
        update_url = detail_url(recipe.id)
        response = self.client.patch(update_url, payload, format='json')
        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filter recipes by tags"""
        recipe_1 = create_recipe(self.user, title='Curry')
        recipe_2 = create_recipe(self.user, title='Tahini')
        recipe_3 = create_recipe(self.user, title='Fish')
        tag_1 = Tag.objects.create(user=self.user, name='Vegan')
        tag_2 = Tag.objects.create(user=self.user, name='Vegetarian')
        recipe_1.tags.add(tag_1)
        recipe_2.tags.add(tag_2)
        params = {'tags': f'{tag_1.id},{tag_2.id}'}
        response = self.client.get(RECIPES_URL, params)
        recipe_1_serialize = RecipeSerializer(recipe_1)
        recipe_2_serialize = RecipeSerializer(recipe_2)
        recipe_3_serialize = RecipeSerializer(recipe_3)
        self.assertIn(recipe_1_serialize.data, response.data)
        self.assertIn(recipe_2_serialize.data, response.data)
        self.assertNotIn(recipe_3_serialize.data, response.data)

    def test_filter_by_ingredients(self):
        """Test filter recipes by ingredients"""
        recipe_1 = create_recipe(self.user, title='Curry')
        recipe_2 = create_recipe(self.user, title='Tahini')
        recipe_3 = create_recipe(self.user, title='Fish')
        ingredient_1 = Ingredient.objects.create(
            user=self.user, name='Tomato'
        )
        ingredient_2 = Ingredient.objects.create(
            user=self.user, name='Cheese'
        )
        recipe_1.ingredients.add(ingredient_1)
        recipe_2.ingredients.add(ingredient_2)
        params = {'ingredients': f'{ingredient_1.id},{ingredient_2.id}'}
        response = self.client.get(RECIPES_URL, params)
        recipe_1_serialize = RecipeSerializer(recipe_1)
        recipe_2_serialize = RecipeSerializer(recipe_2)
        recipe_3_serialize = RecipeSerializer(recipe_3)
        self.assertIn(recipe_1_serialize.data, response.data)
        self.assertIn(recipe_2_serialize.data, response.data)
        self.assertNotIn(recipe_3_serialize.data, response.data)



class UploadImageAPITests(TestCase):
    """Test updload image for authenticated user"""

    def setUp(self):
        user_details = {
            'email': 'test@eveil.com',
            'password': 'test123',
        }
        self.user = create_user(**user_details)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_recipe_image(self): 
        """Test uploading an recipe image"""
        upload_url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10, 10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            response = self.client.post(
                upload_url, payload, format='multipart'
            )
        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self): 
        """Test uploading invalid image return bad request"""
        upload_url = image_upload_url(self.recipe.id)
        payload = {'image': "not_an_image"}
        response = self.client.post(
            upload_url, payload, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
