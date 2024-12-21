from rest_framework.request import Request

from recipes.models import RecipeShortLinks


def get_short_recipe_url(
    request: Request, short_link_instance: RecipeShortLinks
) -> str:
    """
    Generate a short URL for a recipe.
    """

    domain = request.get_host()
    recipe_short_link = short_link_instance.short_link
    return f'http://{domain}/s/{recipe_short_link}'


def get_full_recipe_url(
    request: Request, short_link_instance: RecipeShortLinks
) -> str:
    """
    Generate the full URL for a recipe.
    """

    domain = request.get_host()
    recipe_id = short_link_instance.recipe.id
    return f'http://{domain}/recipes/{recipe_id}'
