from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientsViewset, RecipeViewset, TagViewset, UserViewset

router = DefaultRouter()

router.register('users', UserViewset, basename='users')
router.register('tags', TagViewset, basename='tags')
router.register('recipes', RecipeViewset, basename='recipes')
router.register('ingredients', IngredientsViewset, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
