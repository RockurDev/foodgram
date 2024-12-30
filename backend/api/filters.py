from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Filter for recipes based on tags, author, and user-related fields."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(field_name='favorites__user')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopping_cart__user'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')
