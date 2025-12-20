"""
URL mappings for the user API.
"""
from django.urls import path

from . import views


app_name = "user"

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create_user'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
]
