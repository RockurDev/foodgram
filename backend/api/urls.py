from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteViewset,
    IngredientsViewset,
    RecipeViewset,
    ShoppingCartViewset,
    SubscriptionsViewset,
    TagViewset,
    UserViewset,
    get_recipe_short_link,
)

router_V1 = DefaultRouter()

router_V1.register('users', UserViewset, basename='users')
router_V1.register('tags', TagViewset, basename='tags')
router_V1.register('recipes', RecipeViewset, basename='recipes')
router_V1.register('ingredients', IngredientsViewset, basename='ingredients')

urlpatterns = [
    path(
        'users/me/avatar/',
        UserViewset.as_view(
            {'put': 'update_avatar', 'delete': 'delete_avatar'}
        ),
    ),
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        ShoppingCartViewset.as_view(
            {'post': 'create', 'get': 'list', 'delete': 'destroy'}
        ),
        name='shopping_cart',
    ),
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartViewset.as_view({'get': 'retrieve'}),
        name='download_shopping_cart',
    ),
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteViewset.as_view(
            {'post': 'create', 'get': 'list', 'delete': 'destroy'}
        ),
        name='shopping_cart',
    ),
    path(
        'recipes/<int:recipe_id>/get-link/',
        get_recipe_short_link,
        name='get_recipe_short_link',
    ),
    path(
        'users/<int:user_id>/subscribe/',
        SubscriptionsViewset.as_view({'post': 'create', 'delete': 'destroy'}),
        name='subscribe',
    ),
    path(
        'users/subscriptions/',
        SubscriptionsViewset.as_view({'get': 'list'}),
        name='subscriptions',
    ),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_V1.urls)),
]
