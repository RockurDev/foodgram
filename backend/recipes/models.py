import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import (
    AUTHORED_RECIPES,
    FAVORITED_BY_USERS,
    FAVORITES,
    INGREDIENTS_IN_RECIPE,
    MAX_DISPLAY_NAME_LENGTH,
    MAX_LINK_LENGTH,
    MAX_MEASUREMENT_UNIT_NAME_LENGTH,
    MAX_NAME_INGREDIENT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    RECIPES_USING_INGREDIENT,
    RECIPES_USING_TAG,
    RECIPES_WITH_INGREDIENT,
    RECIPES_WITH_TAG,
    SHOPPING_CART,
    SHOPPING_CARTS_WITH_RECIPE,
    TAGS_OF_RECIPE,
)
from .utils import get_recipe_media_path

User = get_user_model()


class RecipeShortLinks(models.Model):
    """Model to handle short links for recipes."""

    recipe = models.OneToOneField('Recipe', on_delete=models.CASCADE)
    short_link = models.CharField(
        max_length=MAX_LINK_LENGTH,
        unique=True,
        verbose_name='Короткая ссылка',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = _('Ссылка')
        verbose_name_plural = _('Ссылки')

    def generate_short_link(self) -> str:
        """Generate a unique short link using a UUID."""
        short_link = str(uuid.uuid4())[:MAX_LINK_LENGTH]
        while RecipeShortLinks.objects.filter(short_link=short_link).exists():
            short_link = str(uuid.uuid4())[:MAX_LINK_LENGTH]
        return short_link

    @classmethod
    def get_or_create_short_link(cls, recipe):
        """Retrieve or create a short link for a recipe."""
        short_link_instance, created = cls.objects.get_or_create(recipe=recipe)
        if created:
            short_link_instance.short_link = (
                short_link_instance.generate_short_link()
            )
            short_link_instance.save()
        return short_link_instance

    def __str__(self) -> str:
        return f'Recipe ID: {self.recipe.id}, Short Link: {self.short_link}'


class Tag(models.Model):
    """Model representing a tag for categorizing recipes."""

    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH, unique=True, verbose_name=_('Название')
    )
    slug = models.SlugField(
        max_length=MAX_TAG_SLUG_LENGTH, unique=True, verbose_name=_('Слаг')
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('Тег')
        verbose_name_plural = _('Теги')
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'slug'),
                name='unique_tag_name_and_slug',
            ),
        )

    def __str__(self) -> str:
        return self.name[:MAX_DISPLAY_NAME_LENGTH]

    def __repr__(self) -> str:
        return f'<Tag(name={self.name!r}, slug={self.slug!r})>'


class TagRecipe(models.Model):
    """Model for the many-to-many relationship between recipes and tags."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name=_('Рецепт'),
        related_name=TAGS_OF_RECIPE,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name=_('Тег'),
        related_name=RECIPES_USING_TAG,
    )

    class Meta:
        ordering = ('recipe', 'tag')
        verbose_name = _('Связь рецепт–тег')
        verbose_name_plural = _('Связи рецепт–тег')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_tag_recipe',
            )
        ]

    def clean(self) -> None:
        """Ensure that both recipe and tag are provided."""
        if not self.recipe or not self.tag:
            raise ValidationError(_('Both recipe and tag must be provided.'))

    def __str__(self) -> str:
        return f'Tag: {self.tag.name} -> Recipe: {self.recipe.name}'

    def __repr__(self) -> str:
        return f'<Tag(tag={self.tag.name!r}), recipe={self.recipe.name!r}>'


class Ingredient(models.Model):
    """Model representing an ingredient for a recipe."""

    name = models.CharField(
        max_length=MAX_NAME_INGREDIENT_LENGTH, verbose_name=_('Название')
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_NAME_LENGTH,
        verbose_name=_('Единицы измерения'),
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('Ингредиент')
        verbose_name_plural = _('Ингредиенты')
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_and_measurement_unit',
            ),
        )

    def __str__(self) -> str:
        return self.name[:MAX_DISPLAY_NAME_LENGTH]

    def __repr__(self) -> str:
        return (
            f'<Ingredient(name={self.name!r}, '
            f'measurement_unit={self.measurement_unit!r})>'
        )


class IngredientRecipe(models.Model):
    """Model for the many-to-many relationship between recipes and ingredients."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name=_('Рецепт'),
        related_name=INGREDIENTS_IN_RECIPE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name=_('Ингредиент'),
        related_name=RECIPES_USING_INGREDIENT,
    )
    amount = models.PositiveSmallIntegerField(
        _('Количество'), validators=(MinValueValidator(1),)
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = _('Связь ингредиент–рецепт')
        verbose_name_plural = _('Связи ингредиент–рецепт')
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe', 'amount'],
                name='unique_ingredient_recipe',
            )
        ]

    def __str__(self) -> str:
        return (
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'of {self.ingredient.name} for {self.recipe.name}'
        )

    def __repr__(self) -> str:
        return (
            f'<IngredientRecipe('
            f'ingredient={self.ingredient.name!r}, '
            f'recipe={self.recipe.name!r}, '
            f'amount={self.amount!r})>'
        )


class Recipe(models.Model):
    """Model representing a recipe."""

    tags = models.ManyToManyField(
        to=Tag,
        through=TagRecipe,
        verbose_name=_('Теги'),
        related_name=RECIPES_WITH_TAG,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Автор'),
        related_name=AUTHORED_RECIPES,
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through=IngredientRecipe,
        verbose_name=_('Ингредиенты'),
        related_name=RECIPES_WITH_INGREDIENT,
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH, verbose_name=_('Название')
    )
    image = models.ImageField(
        upload_to=get_recipe_media_path,
        verbose_name=_('Изображение'),
    )
    text = models.TextField(verbose_name=_('Текст'))
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name=_('Время приготовления'),
        validators=(MinValueValidator(1),),
    )
    publication_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Дата публикации')
    )

    class Meta:
        ordering = ('-publication_date',)
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')

    def __str__(self) -> str:
        return self.name[:MAX_DISPLAY_NAME_LENGTH]

    def __repr__(self) -> str:
        return (
            f'<Recipe('
            f'name={self.name!r}, '
            f'author={self.author.username!r})>'
        )


class ShoppingCart(models.Model):
    """Model representing a user's shopping cart."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name=SHOPPING_CART,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('Рецепт'),
        related_name=SHOPPING_CARTS_WITH_RECIPE,
    )

    class Meta:
        ordering = ('user', 'recipe')
        verbose_name = _('Корзина')
        verbose_name_plural = _('Корзины')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_in_shopping_cart',
            ),
        )

    def __str__(self) -> str:
        return f'User {self.user} has {self.recipe} in shopping cart'

    def __repr__(self) -> str:
        return (
            f'<ShoppingCart('
            f'user={self.user.username!r}, '
            f'recipe={self.recipe.name!r})>'
        )


class Favorite(models.Model):
    """Model representing a user's favorite recipes."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        related_name=FAVORITES,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name=_('Рецепт'),
        related_name=FAVORITED_BY_USERS,
    )

    class Meta:
        ordering = ('user', 'recipe')
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_in_favorite',
            ),
        )

    def __str__(self) -> str:
        return f'User {self.user} has {self.recipe} in favorites'

    def __repr__(self) -> str:
        return (
            f'<Favorite('
            f'user={self.user.username!r}, '
            f'recipe={self.recipe.name!r})>'
        )
