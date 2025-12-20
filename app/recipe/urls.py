"""
URL mappings for the recipe app.
"""

from rest_framework.routers import DefaultRouter

from recipe.views import IngredientViewSet, RecipeViewSet, TagViewSet


router = DefaultRouter()
router.register('recipes', viewset=RecipeViewSet)
router.register('tags', viewset=TagViewSet)
router.register('ingredients', viewset=IngredientViewSet)

app_name = 'recipe'

urlpatterns = router.urls
