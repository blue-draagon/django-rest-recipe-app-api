"""
Test for the Tag API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Return url for specific tag id"""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='test@eveil.com', password='test123'):
    """Create and return a user"""
    return get_user_model().objects.create_user(
        email=email, password=password
    )


def create_tag(user, name):
    return Tag.objects.create(user=user, name=name)


class PublicTagApiTests(TestCase):
    """Test for no authenticate Tag API"""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_is_required(self):
        """Test authencation is required to access Tag API"""
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTagAPITests(TestCase):
    """Test Tag API for authenticated user"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tag_list(self):
        """Test retrieving the list of tags"""
        create_tag(user=self.user, name='Vegan')
        create_tag(user=self.user, name='Dessert')
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = Tag.objects.all().order_by('name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_user_only_access_self_tags(self):
        """Test list of tags is only for authencated user"""
        user_details = {
            'email': 'other@eveil.com',
            'password': 'test123',
        }
        other_user = create_user(**user_details)
        create_tag(user=other_user, name='Vegan')
        create_tag(user=self.user, name='Dessert')
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_update_tag(self):
        """Test updating tag object"""
        tag = create_tag(user=self.user, name='Dessert')
        payload = {'name': 'Vegan'}
        update_url = detail_url(tag.id)
        response = self.client.patch(update_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

    def test_delete_tag_success(self):
        """Test deleting a tag"""
        tag = create_tag(user=self.user, name='To delete')
        delete_url = detail_url(tag.id)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test filter tags assigned to recipe"""
        tag_1 = create_tag(user=self.user, name='Breakfast')
        tag_2 = create_tag(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Apple Crumbe',
            time_minutes=5,
            price=Decimal('4.5'),
            user=self.user
        )
        recipe.tags.add(tag_1)
        response = self.client.get(
            TAGS_URL, {'assigned_only': 1}
        )
        tag_1_serializer = TagSerializer(tag_1)
        tag_2_serializer = TagSerializer(tag_2)
        self.assertIn(tag_1_serializer.data, response.data)
        self.assertNotIn(tag_2_serializer.data, response.data)

    def test_filtered_tags_is_unique(self):
        """Test filtered tags has no duplicate"""
        tag = create_tag(user=self.user, name='Breakfast')
        create_tag(user=self.user, name='Diner')
        recipe_1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=25,
            price=Decimal('14.5'),
            user=self.user
        )
        recipe_2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=50,
            price=Decimal('24.5'),
            user=self.user
        )
        recipe_1.tags.add(tag)
        recipe_2.tags.add(tag)
        response = self.client.get(
            TAGS_URL, {'assigned_only': 1}
        )
        self.assertEqual(len(response.data), 1)
