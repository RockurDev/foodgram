from django.contrib import admin
from django.db.models import Count
from django.db.models.query import QuerySet
from rest_framework.request import Request

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin panel for the Tag model."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin panel for the Ingredient model."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
        'recipes_with_ingredient_count',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    readonly_fields = ('recipes_with_ingredient_count',)

    @admin.display(description='Число добавлений в рецепт')
    def recipes_with_ingredient_count(self, obj):
        return obj.annotated_recipes_count

    def get_queryset(self, request: Request) -> QuerySet:
        queryset = super().get_queryset(request)
        return queryset.annotate(
            annotated_recipes_count=Count('recipes_using_ingredient')
        )


class IngredientsInline(admin.TabularInline):
    model = Recipe.ingredients.through


@admin.register(Recipe)
class RecipieAdmin(admin.ModelAdmin):
    """Admin model recipie"""

    inlines = (IngredientsInline,)

    list_display = ('id', 'name', 'author', 'favorites_count', 'short_link')
    search_fields = ('name', 'tags', 'author', 'short_link')
    list_filter = ('tags', 'author', 'publication_date')
    readonly_fields = ('favorites_count', 'short_link')

    @admin.display(description='Число добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorites_count

    def get_queryset(self, request: Request) -> QuerySet:
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """Admin panel for the IngredientRecipe model."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin panel for the ShoppingCart model."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin panel for the Favorite model."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
