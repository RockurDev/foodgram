from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    RecipeShortLinks,
    ShoppingCart,
    Tag,
    TagRecipe,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin panel for the Tag model."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    """Admin panel for the TagRecipe model."""

    list_display = ('id', 'recipe', 'tag', 'get_tag_slug')
    search_fields = ('recipe__name', 'tag__name')
    list_filter = ('tag',)

    @admin.display(description='Тег -> Слаг', ordering='tag__slug')
    def get_tag_slug(self, obj):
        return obj.tag.slug


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin panel for the Ingredient model."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipieAdmin(admin.ModelAdmin):
    """Admin model recipie"""

    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'tags', 'author')
    list_filter = ('tags', 'author', 'publication_date')
    readonly_fields = ('favorites_count',)

    @admin.display(description='Число добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorited_by_users.count()


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


@admin.register(RecipeShortLinks)
class RecipeShortLinksAdmin(admin.ModelAdmin):
    """Admin panel for RecipeShortLinks model"""

    list_display = ('id', 'recipe', 'short_link')
    search_fields = ('recipe__name', 'short_link')
