from django.contrib.auth import get_user_model

from django_filters import rest_framework as filters
from rest_framework.request import Request

from recipes.models import Recipe, Tag

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Filter for recipes based on tags, author, and user-related fields."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug', queryset=Tag.objects.all()
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
        fields = ('tags__slug',)

    def filter_by_user_related_field(self, queryset, name, value):
        self.request: Request
        if self.request.user.is_anonymous:
            return queryset.none()
        if value:
            filter_kwargs = {f'{name}__user': self.request.user}
            qs = queryset.filter(**filter_kwargs)
            return qs
        return queryset
