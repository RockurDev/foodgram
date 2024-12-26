import io

from django.db.models import F, Sum
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.request import Request

from recipes.models import IngredientRecipe


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
        # Query ingredients and their total amounts
        # for the user's shopping cart
        ingredient_amount_queryset = (
            IngredientRecipe.objects.filter(
                recipes__shopping_carts_with_recipe__user=user
            )
            .values('ingredient__name')
            .annotate(total_amount=Sum(F('amount')))
            .order_by('ingredient__name')
        )

        shopping_cart = []

        # Iterate over recipes in the user's shopping cart
        for recipe in user.shopping_cart.values(
            'recipe__name', 'recipe__cooking_time'
        ):
            recipe_name = recipe['recipe__name']
            cooking_time = recipe['recipe__cooking_time']
            recipe_info = ' | '.join(
                (
                    f'Рецепт: {recipe_name}',
                    f'Время приготовления: {cooking_time} мин',
                )
            )
            shopping_cart.append(recipe_info)

        shopping_cart.append('\nИнгредиенты:\n')

        # Iterate over ingredient queryset and format output
        for ingredient_entry in ingredient_amount_queryset:
            ingredient = ingredient_entry['ingredient__name']
            total_amount = ingredient_entry['total_amount']
            shopping_cart.append(f'{ingredient}: {total_amount}')

        return '\n'.join(shopping_cart)
