import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MAX_DISPLAY_NAME_LENGTH,
    MAX_LINK_LENGTH,
    MAX_MEASUREMENT_UNIT_NAME_LENGTH,
    MAX_NAME_INGREDIENT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)
from .utils import get_recipe_media_path

User = get_user_model()


class Tag(models.Model):
    """Model representing a tag for categorizing recipes."""

    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_TAG_SLUG_LENGTH, unique=True, verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name[:MAX_DISPLAY_NAME_LENGTH]

    def __repr__(self) -> str:
        return f'<Tag(name={self.name!r}, slug={self.slug!r})>'


class Ingredient(models.Model):
    """Model representing an ingredient for a recipe."""

    name = models.CharField(
        max_length=MAX_NAME_INGREDIENT_LENGTH, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_NAME_LENGTH,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
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
    """
    Model for the many-to-many relationship between recipes and ingredients.
    """

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients_in_recipe',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipes_using_ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT),
        ),
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Связь ингредиент–рецепт'
        verbose_name_plural = 'Связи ингредиент–рецепт'
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
        verbose_name='Теги',
        related_name='recipes_with_tag',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='authored_recipes',
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through=IngredientRecipe,
        verbose_name='Ингредиенты',
        related_name='recipes_with_ingredient',
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH, verbose_name='Название', blank=False
    )
    image = models.ImageField(
        upload_to=get_recipe_media_path,
        verbose_name='Изображение',
        blank=False,
    )
    text = models.TextField(verbose_name='Текст', blank=False)
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ),
        blank=False,
    )
    publication_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )
    short_link = models.CharField(
        max_length=MAX_LINK_LENGTH,
        unique=True,
        verbose_name='Короткая ссылка',
    )

    class Meta:
        ordering = ('-publication_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def generate_short_link(self) -> str:
        """Generate a unique short link using a UUID."""
        while True:
            short_link = str(uuid.uuid4())[:MAX_LINK_LENGTH]
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def save(self, *args, **kwargs) -> None:
        if not self.short_link:
            self.short_link = self.generate_short_link()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name[:MAX_DISPLAY_NAME_LENGTH]

    def __repr__(self) -> str:
        return (
            f'<Recipe('
            f'name={self.name!r}, '
            f'author={self.author.username!r})>'
        )


class UserRecipeBaseClass(models.Model):
    """Abstract base class for models linking users to recipes."""

    class Meta:
        abstract = True
        ordering = ('user', 'recipe')
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_in_%(app_label)s_%(class)s',
            ),
        )

    def __str__(self) -> str:
        return (
            f'User {self.user} has '  # type: ignore
            f'{self.recipe} in {self.__class__.__name__}'  
        )

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}('
            f'user={self.user.username!r}, '  # type: ignore
            f'recipe={self.recipe.name!r})>'  # type: ignore
        )


class ShoppingCart(UserRecipeBaseClass):
    """Model representing a user's shopping cart."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_carts_with_recipe',
    )

    class Meta(UserRecipeBaseClass.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class Favorite(UserRecipeBaseClass):
    """Model representing a user's favorite recipes."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorited_by_users',
    )

    class Meta(UserRecipeBaseClass.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
