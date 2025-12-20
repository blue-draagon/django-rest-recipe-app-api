"""
Recipe API views
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag ids to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient ids to filter'
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe API"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, params):
        return [int(str_id) for str_id in params.split(',')]

    def get_queryset(self):
        """Retrieve only recipes of authenticate user"""
        query_params = self.request.query_params
        queryset = self.queryset
        tags_param = query_params.get('tags')
        ingredients_param = query_params.get('ingredients')
        if tags_param:
            tag_ids = self._params_to_ints(tags_param)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients_param:
            ingredient_ids = self._params_to_ints(ingredients_param)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        user_recipes = queryset.filter(user=self.request.user).distinct()
        return user_recipes.order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer
        if self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request,pk=None):
        """Upload recipe image action"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='filter by items assigned to recipe.'
            ),
        ]
    )
)
class BaseRecipeAttributesViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Base Viewset for recipe many-to-many attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve only items of authenticate user"""
        assigned_only = bool(
            int(self.request.query_params.get(
                'assigned_only', 0
            ))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        user_items = queryset.filter(user=self.request.user).distinct()
        return user_items.order_by('name')

    def perform_create(self, serializer):
        """Create a new item"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttributesViewSet):
    """View for manage tag API"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttributesViewSet):
    """View for manage ingredient API"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
