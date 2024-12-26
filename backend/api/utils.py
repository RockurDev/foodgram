from rest_framework.request import Request

from recipes.models import Recipe


def get_short_recipe_url(request: Request, recipe: Recipe) -> str:
    """Generate a short URL for a recipe."""

    return request.build_absolute_uri(f'/s/{recipe.short_link}')


def get_full_recipe_url(request: Request, recipe: Recipe) -> str:
    """Generate the full URL for a recipe."""

    return request.build_absolute_uri(f'/recipes/{recipe.id}')  # type: ignore
