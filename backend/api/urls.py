from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientsViewset, RecipeViewset, TagViewset, UserViewset

router_V1 = DefaultRouter()

router_V1.register('users', UserViewset, basename='users')
router_V1.register('tags', TagViewset, basename='tags')
router_V1.register('recipes', RecipeViewset, basename='recipes')
router_V1.register('ingredients', IngredientsViewset, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_V1.urls)),
]
