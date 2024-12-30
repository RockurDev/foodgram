from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag
from users.models import UserSubscriptions

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Handles serialization of recipes data."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserAvatarSerializer(serializers.ModelSerializer):
    """Handles serialization of user avatars, supporting base64 decoding."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data representation.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

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
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_is_subscribed(self, user) -> bool:
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and UserSubscriptions.objects.filter(
                subscriber=request.user, subscribed_to=user
            ).exists()
        )

    def get_avatar(self, user):
        return user.avatar.url if user.avatar else None


class UserSubscriptionsSerializer(UserSerializer):
    """Serializes user subscription details."""

    recipes_count = serializers.IntegerField(default=0, read_only=True)
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')

    def get_recipes(self, user: Recipe):
        request = self.context.get('request')

        if recipes_limit := (
            request.query_params.get('recipes_limit') if request else None
        ):
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None

        queryset = user.authored_recipes.all()  # type: ignore
        recipes = queryset[:recipes_limit] if recipes_limit else queryset
        return ShortRecipeSerializer(recipes, many=True).data

    def to_representation(self, instance):
        return super().to_representation(instance.subscribed_to)


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Handles user subscription creation."""

    class Meta:
        model = UserSubscriptions
        fields = ('subscriber', 'subscribed_to')
        validators = (
            validators.UniqueTogetherValidator(
                queryset=UserSubscriptions.objects.all(),
                fields=('subscriber', 'subscribed_to'),
                message=_('You have already subscribed this user.'),
            ),
        )

    def validate(self, attrs):
        if attrs['subscriber'] == attrs['subscribed_to']:
            raise serializers.ValidationError(
                {'detail': "You can't subscribe to yourself."}
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        return UserSubscriptionsSerializer(instance, context=self.context).data


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

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit')


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(
        many=True, source='ingredients_in_recipe'
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        exclude = ('short_link', 'publication_date')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializes recipes, including their tags, ingredients, and other details.
    """

    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=True, queryset=Tag.objects.all()
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True, required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        exclude = ('short_link', 'author')

    def validate(self, data):
        self._validate_tags(data.get('tags'))
        self._validate_ingredients(data.get('ingredients'))
        return super().validate(data)

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError('Image is required')
        return image

    def _validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'At least one tag is required.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({'tags': 'Tags must be unique.'})

    def _validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'Ingredients must be a non-empty list.'}
            )

        validated_ingredients_ids = set()
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')

            if ingredient_id in validated_ingredients_ids:
                raise serializers.ValidationError(
                    {'ingredients': 'Ingredients must be unique.'}
                )
            validated_ingredients_ids += ingredient_id

    @atomic
    def create(self, validated_data) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user

        instance = Recipe.objects.create(author=author, **validated_data)
        instance.tags.set(tags_data)
        RecipeSerializer._create_ingredients(instance, ingredients_data)
        return instance

    @atomic
    def update(self, instance: Recipe, validated_data) -> Recipe:
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)

        ingredients_data = validated_data.pop('ingredients', [])
        instance.ingredients.clear()
        RecipeSerializer._create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    @staticmethod
    def _create_ingredients(recipe, ingredients) -> None:
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=item['id'],
                    amount=item['amount'],
                )
                for item in ingredients
            ]
        )

    def to_representation(self, instance):
        return RecipeListSerializer(instance).data
