from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
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
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(
        field_name='favorited_by_users', method='filter_by_user_related_field'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopping_carts_with_recipe',
        method='filter_by_user_related_field',
    )

    class Meta:
        model = Recipe
        fields = ('tags',)

    def filter_by_user_related_field(self, queryset, name, value):
        user = self.request.user  # type: ignore
        if value and not isinstance(user, AnonymousUser):
            filter_kwargs = {f'{name}__user': user}
            return queryset.filter(**filter_kwargs)
        return queryset
