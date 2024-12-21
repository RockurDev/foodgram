from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import RecipeFilter
from .mixins import ShoppingListGeneratorMixin
from .pagination import DefaultPagintaion
from .utils import get_short_recipe_url
from api.permissions import IsAuthorOrReadOnly, MeOnlyForAuthenticatedUsers
from api.serializers import (
    IngredientListSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserSerializer,
    UserSubscribeSerializer,
    UserSubscriptionsSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeShortLinks,
    ShoppingCart,
    Tag,
)
from users.models import UserSubscriptions

User = get_user_model()


class SubscriptionsViewset(viewsets.ModelViewSet):
    """Handles user subscription management."""

    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'delete']
    pagination_class = DefaultPagintaion
    lookup_url_kwarg = 'user_id'

    def get_serializer_class(self):
        return (
            UserSubscribeSerializer
            if self.action == 'create'
            else UserSubscriptionsSerializer
        )

    def get_queryset(self):
        """Get all subscriptions for the currently authenticated user."""
        return self.request.user.subscriptions.all()  # type: ignore

    def create(self, request: Request, user_id=None) -> Response:
        """Subscribe the authenticated user to another user."""
        subscribed_to_user = get_object_or_404(User, pk=user_id)

        if request.user == subscribed_to_user:
            return Response(
                {'detail': "You can't subscribe to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subscription = UserSubscriptions.subscribe(
                subscriber=request.user, subscribed_to=subscribed_to_user
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request: Request, user_id=None) -> Response:
        """Unsubscribe the authenticated user from another user."""
        subscribed_to_user = get_object_or_404(User, pk=user_id)

        if not UserSubscriptions.is_subscribed(
            subscriber=request.user, subscribed_to=subscribed_to_user
        ):
            return Response(
                {'detail': 'You are not subscribed to this user.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserSubscriptions.unsubscribe(
            subscriber=request.user, subscribed_to=subscribed_to_user
        )
        return Response(
            {'detail': 'Subscription deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT,
        )


class UserViewset(viewsets.ModelViewSet):
    """Handles user profile management."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = DefaultPagintaion
    permission_classes = (MeOnlyForAuthenticatedUsers,)

    def update_avatar(self, request: Request) -> Response:
        serializer = UserAvatarSerializer(
            instance=request.user, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete_avatar(self, request: Request) -> Response:
        self._clear_avatar_field(request.user.id)
        request.user.avatar = None  # type: ignore
        request.user.save()
        return Response(
            {'detail': 'Avatar was deleted'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @staticmethod
    def _clear_avatar_field(user_id) -> None:
        avatars_folder_path = (
            Path(settings.MEDIA_ROOT) / 'avatars' / str(user_id)
        )
        if avatars_folder_path.exists() and avatars_folder_path.is_dir():
            for file in avatars_folder_path.iterdir():
                if file.is_file():
                    file.unlink()
                avatars_folder_path.rmdir()


class TagViewset(viewsets.ReadOnlyModelViewSet):
    """Provides read-only access to tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    filterset_fields = ('name', 'slug')


class IngredientsViewset(viewsets.ReadOnlyModelViewSet):
    """Provides read-only access to ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientListSerializer
    pagination_class = None
    filterset_fields = ('name',)


@api_view(['GET'])
def get_recipe_short_link(request, recipe_id) -> Response:
    """Generates a short link for a recipe."""

    recipe = get_object_or_404(Recipe, pk=recipe_id)
    short_link_instance = RecipeShortLinks.get_or_create_short_link(recipe)
    full_short_link = get_short_recipe_url(request, short_link_instance)
    return Response({'short-link': full_short_link})


class RecipeViewset(viewsets.ModelViewSet):
    """Handles CRUD operations for recipes."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = DefaultPagintaion
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    http_method_names = ['get', 'post', 'patch', 'delete']
    filterset_class = RecipeFilter


class ShoppingCartViewset(ShoppingListGeneratorMixin, viewsets.ModelViewSet):
    """Manages recipes in the shopping cart."""

    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'recipe_id'

    def get_queryset(self):
        return self.request.user.shopping_cart.all()  # type: ignore

    def create(self, request: Request, *args, **kwargs) -> Response:
        recipe = get_object_or_404(Recipe, pk=kwargs.get('recipe_id'))

        recipe, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if created is False:
            return Response(
                {
                    'detail': (
                        'You are already have this recipe in shopping cart.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request) -> FileResponse:
        return self.generate_shopping_list(request)

    def destroy(self, request, *args, **kwargs) -> Response:
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if not self.request.user.shopping_cart.filter(  # type: ignore
            recipe=recipe
        ).exists():
            return Response(
                {
                    'detail': (
                        "You don't have this recipe in your shopping cart."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)


class FavoriteViewset(viewsets.ModelViewSet):
    """Manages favorite recipes."""

    serializer_class = ShortRecipeSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'recipe_id'

    def get_queryset(self):
        return self.request.user.favorites.all()  # type: ignore

    def create(self, request: Request, *args, **kwargs) -> Response:
        recipe = get_object_or_404(Recipe, pk=kwargs.get('recipe_id'))
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if created is False:
            return Response(
                {'detail': ('You are already have this recipe in favorite.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(recipe)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs) -> Response:
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = self.request.user
        if not user.favorites.filter(recipe=recipe).exists():  # type: ignore
            return Response(
                {'detail': "You don't have this recipe in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)
