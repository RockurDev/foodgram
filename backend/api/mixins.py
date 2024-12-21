import base64
import binascii
import io
import uuid
from collections import Counter
from typing import Optional

from django.core.files.base import ContentFile
from django.http import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import serializers
from rest_framework.request import Request

from recipes.models import Recipe
from users.models import User


class Base64DecoderMixin:
    """Provides functionality to decode a base64-encoded string."""

    def decode_string(self, encoded_string: str, field_name: str) -> bytes:
        if (
            not isinstance(encoded_string, str)
            or ';base64,' not in encoded_string
        ):
            raise serializers.ValidationError(
                {field_name: 'Invalid base64 string format.'}
            )
        _, base64_str = encoded_string.split(';base64,')
        try:
            return base64.b64decode(base64_str)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError(
                {field_name: 'The base64 string is corrupted or invalid.'}
            )


class ImageDecoderMixin(Base64DecoderMixin):
    """
    Provides functionality to decode base64-encoded images
    into ContentFile objects.
    """

    def get_image_file(
        self, encoded_string: str, field_name: str = 'image'
    ) -> ContentFile:
        decoded_data = self.decode_string(encoded_string, field_name)
        mime_type, _ = encoded_string.split(';', 1)
        file_extension = mime_type.split('/')[-1]
        file_name = f'{uuid.uuid4()}.{file_extension}'
        return ContentFile(decoded_data, name=file_name)


class RecipesDataMixin:
    """Provides utility methods for retrieving recipes data for a user."""

    def get_recipes_count(self, obj) -> int:
        return obj.subscribed_to.authored_recipes.count()

    def get_recipes(self, obj: Recipe):
        from api.serializers import ShortRecipeSerializer

        request = self.context.get('request')  # type: ignore

        recipes_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None

        queryset = obj.subscribed_to.authored_recipes.all()  # type: ignore
        recipes = queryset[:recipes_limit] if recipes_limit else queryset

        return ShortRecipeSerializer(recipes, many=True).data


class UserDataMixin:
    """Provides utility methods for retrieving user data."""

    def get_user_data(self, user) -> dict:
        request = self.context.get('request')  # type: ignore
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_subscribed': self.is_user_subscribed(user),
            'avatar': self.get_user_avatar(user, request),
        }

    def is_user_subscribed(self, user) -> bool:
        from users.models import UserSubscriptions

        request = self.context.get('request')  # type: ignore
        if not request or not request.user.is_authenticated:
            return False
        return UserSubscriptions.objects.filter(
            subscriber=request.user, subscribed_to=user
        ).exists()

    def get_user_avatar(
        self, user: User, request: Optional[Request]
    ) -> Optional[str]:
        return user.avatar.url if user.avatar else None


class ShoppingListGeneratorMixin:
    def generate_shopping_list(self, request: Request) -> FileResponse:
        buffer = io.BytesIO()

        c = canvas.Canvas(buffer, pagesize=A4)

        pdfmetrics.registerFont(TTFont('Georgia', 'fonts/georgia.ttf'))

        c.setFont('Georgia', 14)

        # Add some title and separator in the PDF
        username = request.user.username
        c.drawString(
            100,
            750,
            f'Список ингредиентов для покупок пользователя {username}',
        )
        c.drawString(100, 730, '-' * 50)

        # Get the shopping cart text with ingredients and recipes
        text = self._get_shopping_cart_text(request.user)

        # Start from the Y-coordinate 710 and decrease it for each line of text
        lines = text.split('\n')
        y_position = 710
        for line in lines:
            c.drawString(100, y_position, line)
            y_position -= 14  # Adjust line height (12 pt font + some margin)

        c.save()

        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f'shopping_cart_{request.user.username}.pdf',
        )

    def _get_shopping_cart_text(self, user) -> str:
        recipes = self.request.user.shopping_cart.all()  # type: ignore
        ingredients_counter = Counter()

        # Collect and count ingredients across all recipes
        for recipe in recipes:
            for ingredient in recipe.recipe.ingredients.all():
                ingredients_counter[ingredient.name] += 1

        # Format the ingredients and recipes list
        shopping_cart = []
        for recipe in recipes:
            name = recipe.recipe.name
            cooking_time = recipe.recipe.cooking_time
            recipe_info = (
                f'Рецепт: {name} | Время приготовления: {cooking_time} мин'
            )
            shopping_cart.append(recipe_info)

        shopping_cart.append('\nИнгредиенты: \n')
        for ingredient, count in ingredients_counter.items():
            shopping_cart.append(f'{ingredient}: {count}')

        return '\n'.join(shopping_cart)
