from django.shortcuts import get_object_or_404, redirect
from rest_framework.request import Request

from .models import Recipe
from api.utils import get_full_recipe_url


def redirect_short_url(request: Request, short_url: str):
    """
    Redirects a short URL to its corresponding full recipe URL.
    """

    recipe = get_object_or_404(Recipe, short_link=short_url)
    full_url = get_full_recipe_url(request, recipe)
    return redirect(full_url)
