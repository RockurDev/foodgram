from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from djoser.serializers import UserCreateSerializer
from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError

from .mixins import ImageDecoderMixin, RecipesDataMixin, UserDataMixin
from recipes.constants import MAX_RECIPE_NAME_LENGTH
from recipes.models import (
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import UserSubscriptions

User = get_user_model()


class UserAuthTokenSerializer(serializers.Serializer):
    """Handles user authentication via email and password."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=False, style={'input_type': 'password'}
    )

    def validate(self, data):
        """Validate the provided email and password credentials."""

        email = data.get('email')
        password = data.get('password')

        self.user = User.objects.filter(email=email).first()

        if self.user is None or not check_password(
            password, self.user.password
        ):
            raise ValidationError('Invalid email or password.')

        return data


class UserAvatarSerializer(ImageDecoderMixin, serializers.ModelSerializer):
    """Handles serialization of user avatars, supporting base64 decoding."""

    avatar = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_internal_value(self, data):
        field_name = 'avatar'

        if not data or field_name not in data:
            raise serializers.ValidationError(
                {field_name: 'This field is required.'}
            )

        data[field_name] = self.get_image_file(data[field_name], field_name)
        return super().to_internal_value(data)


class UserRegistrationSerializer(UserCreateSerializer):
    """
    Serializer for user registration.

    Extends the Djoser `UserCreateSerializer`
    to include required fields for registering a new user,
    such as email, username, first name, last name, and password.
    """

    class Meta(UserCreateSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True, 'required': True},
        }


class UserSerializer(UserDataMixin, serializers.ModelSerializer):
    """
    Serializer for user data representation.

    subscription status, and avatar. Custom representation logic is applied.
    """

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )

    def to_representation(self, instance):
        return self.get_user_data(instance)


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for tag objects.

    Fields are marked as read-only to prevent modifications.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('name', 'slug')


class IngredientListSerializer(serializers.ModelSerializer):
    """
    Serializer for a list of ingredients.

    Fields are read-only to ensure data integrity.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class IngredientSerializer(serializers.ModelSerializer):
    """Provides serialized representation of ingredients with usage amounts."""

    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit')

    def get_amount(self, obj) -> int:
        """
        Retrieve the amount from the intermediate model.
        """
        return obj.recipes_using_ingredient.first().amount


class RecipeSerializer(
    ImageDecoderMixin,
    serializers.ModelSerializer,
):
    """
    Serializes recipes, including their tags, ingredients, and other details.
    """

    tags = TagSerializer(many=True, required=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True, validators=())
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    name = serializers.CharField(required=True, min_length=1, max_length=255)
    text = serializers.CharField(required=True, min_length=1)
    cooking_time = serializers.IntegerField(
        required=True, validators=(MinValueValidator(1),)
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, data):
        """
        Perform all validations in one place.
        """
        for field in self.Meta.fields:
            if field not in (
                'id',
                'author',
                'is_favorited',
                'is_in_shopping_cart',
            ) and not data.get(field, None):
                raise serializers.ValidationError(
                    {'tags': f"Field '{field}' is required."}
                )

        if len(data.get('name')) > MAX_RECIPE_NAME_LENGTH:
            raise serializers.ValidationError(
                {'name': f'Maximum name length is {MAX_RECIPE_NAME_LENGTH}.'}
            )

        if not (tag_ids := data.get('tags')):
            raise serializers.ValidationError(
                {'tags': 'At least one tag is required.'}
            )
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({'tags': 'Tags must be unique.'})
        for tag_id in tag_ids:
            if not Tag.objects.filter(pk=tag_id).exists():
                raise serializers.ValidationError(
                    {'tags': f'Tag with id {tag_id} does not exist.'}
                )

        cooking_time = data.get('cooking_time')

        try:
            cooking_time = float(cooking_time)
        except (ValueError, TypeError):
            raise ValidationError(
                {'cooking_time': 'Cooking_time must be a valid number'}
            )

        if cooking_time is not None and cooking_time <= 0:
            raise serializers.ValidationError(
                {'cooking_time': 'Cooking time must be greater than zero.'}
            )

        return super().validate(data)

    def to_internal_value(self, data):
        data['image'] = self.get_image_file(data.get('image'))
        if not (ingredients := data.get('ingredients')):
            raise ValidationError(
                {'ingredients': 'Ingredients must be non empty list'}
            )
        data['ingredients'] = self._validate_ingredients(ingredients)
        return data

    def get_image(self, obj):
        return obj.image.url

    def get_is_favorited(self, obj) -> bool:
        return obj.favorited_by_users.exists()

    def get_is_in_shopping_cart(self, obj) -> bool:
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.shopping_carts_with_recipe.filter(user=user).exists()
        )

    def get_ingredients(self, obj):
        return [
            {
                'id': ingredient.ingredient.id,
                'name': ingredient.ingredient.name,
                'measurement_unit': ingredient.ingredient.measurement_unit,
                'amount': ingredient.amount,
            }
            for ingredient in obj.ingredients_in_recipe.all()
        ]

    def _validate_ingredients(self, ingredients_data):
        ingredients = []
        validated_ingredients_ids = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            amount = ingredient_data.get('amount')

            if ingredient_id in validated_ingredients_ids:
                raise ValidationError(
                    {'ingredients': 'Ingredients must be unique'}
                )
            validated_ingredients_ids.append(ingredient_id)

            if not ingredient_id or amount is None:
                raise ValidationError(
                    {
                        'ingredients': (
                            'Each ingredient must have an id and amount.'
                        )
                    }
                )

            try:
                amount = float(amount)
            except (ValueError, TypeError):
                raise ValidationError(
                    {'ingredients': 'Amount must be a valid number'}
                )

            if amount <= 0:
                raise ValidationError(
                    {'ingredients': 'Amount must be a positive number'}
                )

            ingredient = self.get_ingredient_by_id(ingredient_id)
            ingredients.append({'ingredient': ingredient, 'amount': amount})

        return ingredients

    @classmethod
    def get_ingredient_by_id(cls, ingredient_id: int) -> Ingredient:
        try:
            return Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                {
                    'ingredients': (
                        f'Ingredient with id {ingredient_id} does not exist.'
                    )
                }
            )

    def create(self, validated_data) -> Recipe:
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])
        author = self.context['request'].user

        instance = Recipe.objects.create(author=author, **validated_data)
        instance.tags.set(tags_data)
        self._create_ingredients(instance, ingredients_data)
        return instance

    def update(self, instance: Recipe, validated_data) -> Recipe:
        if tags_data := validated_data.pop('tags', []):
            instance.tags.set(tags_data)

        if ingredients_data := validated_data.pop('ingredients', []):
            instance.ingredients.clear()
            self._create_ingredients(instance, ingredients_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def _create_ingredients(self, recipe, ingredients) -> None:
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients
            ]
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Handles serialization of shopping cart data."""

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def to_representation(self, instance: ShoppingCart):
        return {
            'id': instance.id,  # type: ignore
            'name': instance.recipe.name,
            'image': instance.recipe.image.url,
            'cooking_time': instance.recipe.cooking_time,
        }


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Handles serialization of recipes data."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscriptionsBaseSerializer(
    RecipesDataMixin, UserDataMixin, serializers.ModelSerializer
):
    """Base serializer for user subscriptions."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    def to_representation(self, instance):
        user_data = self.get_user_data(instance.subscribed_to)
        base_data = super().to_representation(instance)
        return {**user_data, **base_data}


class UserSubscribeSerializer(UserSubscriptionsBaseSerializer):
    """Handles user subscription creation."""

    class Meta:
        model = UserSubscriptions
        exclude = ('subscriber', 'subscribed_to')
        validators = (
            validators.UniqueTogetherValidator(
                queryset=UserSubscriptions.objects.all(),
                fields=('subscriber', 'subscribed_to'),
                message=_('You have already subscribed this user.'),
            ),
        )


class UserSubscriptionsSerializer(UserSubscriptionsBaseSerializer):
    """Serializes user subscription details."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscriptions
        exclude = ('subscriber', 'subscribed_to')
