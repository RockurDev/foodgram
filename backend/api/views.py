from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef
from django.db.models.query import QuerySet
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response

from .decorators import paginate
from .filters import RecipeFilter
from .mixins import ShoppingListGeneratorMixin
from .pagination import DefaultPagination
from .utils import get_short_recipe_url
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientListSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserSubscribeSerializer,
    UserSubscriptionsSerializer,
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import UserSubscriptions

User = get_user_model()


class UserViewset(DjoserUserViewSet):
    """Handles user profile management."""

    pagination_class = DefaultPagination

    def get_permissions(self):
        if 'me/' in self.request.path:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('PUT',),
        url_path='me/avatar',
    )
    def avatar(self, request: Request) -> Response:
        serializer = UserAvatarSerializer(
            instance=request.user, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
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
        avatars_folder_path = Path(settings.MEDIA_ROOT) / 'avatars'
        if avatars_folder_path.exists():
            avatar_path = avatars_folder_path / str(user_id)
            if avatar_path.is_file():
                avatar_path.unlink()

    @action(
        detail=True,
        methods=('POST',),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request: Request, id) -> Response:
        """Subscribe the authenticated user to another user."""
        subscribed_to_user = get_object_or_404(User, pk=id)

        if request.user == subscribed_to_user:
            return Response(
                {'detail': "You can't subscribe to yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipes_count = (
            subscribed_to_user.authored_recipes.count()  # type: ignore
        )
        serializer = UserSubscribeSerializer(
            data={
                'subscriber': request.user.pk,
                'subscribed_to': subscribed_to_user.pk,
            },
            context={'request': request, 'recipes_count': recipes_count},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @paginate
    @action(
        detail=False,
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
        serializer_class=UserSubscriptionsSerializer,
    )
    def get_subscriptions(self, request: Request):
        user = self.request.user
        subscriptions = user.subscriptions.annotate(  # type: ignore
            recipes_count=Count('subscribed_to__authored_recipes')
        ).order_by('id')

        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                return Response(
                    {
                        'detail': (
                            'Parameter recipes_limit must be a valid integer.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscriptions = subscriptions[:recipes_limit]

        return subscriptions

    @subscriptions.mapping.delete
    def delete_subscription(self, request: Request, id: int) -> Response:
        subscribed_to_user = get_object_or_404(User, pk=id)

        deleted_rows, _ = UserSubscriptions.objects.filter(
            subscriber=request.user, subscribed_to=subscribed_to_user
        ).delete()

        if not deleted_rows:
            return Response(
                {'detail': 'You are not subscribed to this user.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Subscription deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT,
        )


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


class RecipeViewset(ShoppingListGeneratorMixin, viewsets.ModelViewSet):
    """Handles CRUD operations for recipes."""

    serializer_class = RecipeSerializer
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        if not user.is_anonymous:
            favorites_queryset = user.favorites.filter(  # type: ignore
                recipe=OuterRef('pk')
            )
            shopping_cart_queryset = user.shopping_cart.filter(  # type: ignore
                recipe=OuterRef('pk')
            )
        else:
            favorites_queryset = shopping_cart_queryset = User.objects.none()

        return Recipe.objects.annotate(
            is_favorited=Exists(favorites_queryset),
            is_in_shopping_cart=Exists(shopping_cart_queryset),
        )

    @action(detail=True, url_path='get-link')
    def get_recipe_short_link(self, request: Request, pk: int) -> Response:
        """Generates a short link for a recipe."""

        recipe = get_object_or_404(Recipe, pk=pk)
        full_short_link = get_short_recipe_url(request, recipe)
        return Response({'short-link': full_short_link})

    @action(
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request: Request) -> FileResponse:
        return self.generate_shopping_list(request)

    @action(
        detail=True,
        methods=('POST',),
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,),
        serializer_class=ShortRecipeSerializer,
    )
    def shopping_cart(self, request: Request, pk: int) -> Response:
        recipe = get_object_or_404(Recipe, pk=pk)

        _, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
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

    @shopping_cart.mapping.get
    def get_shopping_cart(self, request: Request):
        return self.request.user.shopping_cart.all()  # type: ignore

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request: Request, pk: int) -> Response:
        recipe = get_object_or_404(Recipe, pk=pk)

        deleted_rows, _ = self.request.user.shopping_cart.filter(  # type: ignore # noqa: E501
            recipe=recipe
        ).delete()

        if not deleted_rows:
            return Response(
                {
                    'detail': (
                        "You don't have this recipe in your shopping cart."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Recipe was deleted from shopping cart'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=('POST',),
        url_path='favorite',
        permission_classes=(IsAuthenticated,),
        serializer_class=ShortRecipeSerializer,
    )
    def favorites(self, request: Request, pk: int) -> Response:
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )

        if not created:
            return Response(
                {'detail': ('You are already have this recipe in favorite.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorites.mapping.get
    def get_favorites(self, request: Request):
        return self.request.user.favorites.all()  # type: ignore

    @favorites.mapping.delete
    def delete_favorite(self, request: Request, pk: int) -> Response:
        recipe = get_object_or_404(Recipe, pk=pk)

        deleted_rows, _ = self.request.user.favorites.filter(  # type: ignore
            recipe=recipe
        ).delete()

        if not deleted_rows:
            return Response(
                {'detail': "You don't have this recipe in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Recipe was deleted from your favorites.'},
            status=status.HTTP_204_NO_CONTENT,
        )
