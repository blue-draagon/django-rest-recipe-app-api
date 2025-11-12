"""
Test for the user API
"""
from core.tools import test_ok

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create_user')
TOKEN_URL = reverse('user:token')
PROFILE_URL = reverse('user:profile')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


def get_user(email):
    """Create and return a new user"""
    return get_user_model().objects.get(email=email)


def filter_users(email):
    """Create and return a new user"""
    return get_user_model().objects.filter(email=email)


class PublicUserApiTests(TestCase):
    """Test public features user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user"""
        payload = {
            'email': 'test@eveil.com',
            'password': 'test1234',
            'name': 'Test name',
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user(payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)
        test_ok("test_create_user_success")

    def test_user_email_already_exist_error(self):
        """Test get error if user with email exist"""
        payload = {
            'email': 'test@eveil.com',
            'password': 'test1234',
            'name': 'Test name',
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        test_ok("test_user_email_already_exist_error")

    def test_password_too_short_error(self):
        """Test get error if password  less than 5 chars"""
        payload = {
            'email': 'test@eveil.com',
            'password': 'test',
            'name': 'Test name',
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = filter_users(payload['email']).exists()
        self.assertFalse(user_exists)
        test_ok("test_password_too_short_error")

    def test_create_token_for_user(self):
        """Test generate token for user valid credentials."""
        user_details = {
            'email': 'test@eveil.com',
            'password': 'test123',
            'name': 'Test name',
        }
        create_user(**user_details)
        payload = {
            'email': 'test@eveil.com',
            'password': 'test123',
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        test_ok("test_create_token_for_user")

    def test_create_token_bad_credentials(self):
        """Test get error if invalid credentials"""
        user_details = {
            'email': 'test@eveil.com',
            'password': 'test123',
        }
        create_user(**user_details)
        payload = {
            'email': 'badinfo',
            'password': 'badinfo',
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        test_ok("test_create_token_bad_credentials")

    def test_using_blank_password(self):
        """Test return error if password is blank"""
        payload = {
            'email': 'test@eveil.com',
            'password': '',
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        test_ok("test_using_blank_password ")

    def test_user_retrieve_authentication_required(self):
        """Test authentication is required to retrieve user"""
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticateUserApiTests(TestCase):
    """Test api request for authenticate user"""

    def setUp(self):
        user_details = {
            'email': 'test@eveil.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = create_user(**user_details)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_user_retrieve_profile_success(self):
        """Test authenticate user success retrieve profile"""
        response = self.client.get(PROFILE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_not_allowed_on_profile(self):
        """Test POST method not allowed on profile endpoint"""
        response = self.client.post(PROFILE_URL)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_user_update_profile_success(self):
        """Test authenticate user success update his profile"""
        payload = {'name': 'new name', 'password': 'newpass'}
        response = self.client.patch(PROFILE_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
