from django.shortcuts import get_object_or_404, redirect
from rest_framework.request import Request

from api.utils import get_full_recipe_url
from recipes.models import RecipeShortLinks


def redirect_short_url(request: Request, short_url: str):
    """
    Redirects a short URL to its corresponding full recipe URL.
    """

    short_link_instance = get_object_or_404(
        RecipeShortLinks, short_link=short_url
    )
    full_url = get_full_recipe_url(request, short_link_instance)
    return redirect(full_url)
