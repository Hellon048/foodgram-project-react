from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (ModelSerializer, SerializerMethodField,
                                        ValidationError)

from recipes.models import AmountIngredient, Ingredient, Recipe, Tag
from users.models import MyUser
from users.validators import username_validation

from .services import (check_value_validate, is_hex_color,
                       recipe_amount_ingredients_set)


class ShortRecipeSerializer(ModelSerializer):
    """Сериализатор для модели Recipe.
    Определён укороченный набор полей для некоторых эндпоинтов.
    """

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = '__all__',


class UserSerializer(ModelSerializer):
    """Сериализатор для использования с моделью User.
    """
    is_subscribed = SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = 'is_subscribed',

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей.

        Определяет - подписан ли текущий пользователь
        на просматриваемого пользователя.

        Args:
            obj (User): Пользователь, на которого проверяется подписка.

        Returns:
            bool: True, если подписка есть. Во всех остальных случаях False.
        """
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return user.subscribe.filter(id=obj.id).exists()

    def create(self, validated_data):
        """ Создаёт нового пользователя с запрошенными полями.

        Args:
            validated_data (dict): Полученные проверенные данные.

        Returns:
            User: Созданный пользователь.
        """
        user = MyUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate_username(self, value):
        """Проверяет корректность имени пользователя."""
        return username_validation(value)


class UserSubscribeSerializer(UserSerializer):
    """Сериализатор вывода авторов на которых подписан текущий пользователь.
    """
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField(method_name='get_recipes_count')

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        """Проверка подписки пользователей.

        Переопределённый метод родительского класса для уменьшения нагрузки,
        так как в текущей реализации всегда вернёт `True`.

        Returns:
            bool: True
        """
        return True

    def get_recipes_count(self, obj):
        """ Показывает общее количество рецептов у каждого автора.

        Args:
            obj (User): Запрошенный пользователь.

        Returns:
            int: Количество рецептов созданных запрошенным пользователем.
        """
        return obj.recipes.count()


class TagSerializer(ModelSerializer):
    """Сериализатор для вывода тэгов.
    """

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = '__all__',

    def validate_color(self, color):
        """Проверяет и нормализует код цвета.

        Args:
            color (str): Строка описывающая код цвета.

        Returns:
            str: Проверенная строка описывающая цвет в HEX-формате (#12AB98).
        """
        color = str(color).strip(' #')
        is_hex_color(color)
        return f'#{color}'


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингридиентов.
    """

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = '__all__',


class RecipeSerializer(ModelSerializer):
    """Сериализатор для рецептов.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField(method_name='get_ingredients')
    is_favorited = SerializerMethodField(method_name='get_is_favorited')
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart')
    image = Base64ImageField()

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
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def get_ingredients(self, obj):
        """Получает список ингридиентов для рецепта.

        Args:
            obj (Recipe): Запрошенный рецепт.

        Returns:
            list: Список ингридиентов в рецепте.
        """
        obj.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )

    def get_is_favorited(self, obj):
        """Проверка - находится ли рецепт в избранном.

        Args:
            obj (Recipe): Переданный для проверки рецепт.

        Returns:
            bool: True - если рецепт в `избранном`
            у запращивающего пользователя, иначе - False.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка - находится ли рецепт в списке  покупок.

        Args:
            obj (Recipe): Переданный для проверки рецепт.

        Returns:
            bool: True - если рецепт в `списке покупок`
            у запращивающего пользователя, иначе - False.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.carts.filter(id=obj.id).exists()

    def validate(self, data):
        """Проверка вводных данных при создании/редактировании рецепта.

        Args:
            data (dict): Вводные данные.

        Raises:
            ValidationError: Тип данных несоответствует ожидаемому.

        Returns:
            dict: Проверенные данные.
        """
        name = str(self.initial_data.get('name')).strip()
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        values_as_list = (tags, ingredients)
        cooking_time = data['cooking_time']

        for value in values_as_list:
            if not isinstance(value, list):
                raise ValidationError(
                    f'"{value}" должен быть в формате "[]"'
                )

        for tag in tags:
            check_value_validate(tag, Tag)

        valid_ingredients = []
        for ing in ingredients:
            ing_id = ing.get('id')
            ingredient = check_value_validate(ing_id, Ingredient)

            amount = ing.get('amount')
            check_value_validate(amount)

            valid_ingredients.append(
                {'ingredient': ingredient, 'amount': amount}
            )

        data['name'] = name.capitalize()
        data['tags'] = tags
        data['ingredients'] = valid_ingredients
        data['author'] = self.context.get('request').user
        if int(cooking_time) <= 0:
            raise ValidationError({
                'cooking_time': 'Время приготовления должно быть больше 0!'
            })
        return data

    def create(self, validated_data):
        """Создаёт рецепт.

        Args:
            validated_data (dict): Данные для создания рецепта.

        Returns:
            Recipe: Созданый рецепт.
        """
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags)
        recipe_amount_ingredients_set(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        """Обновляет рецепт.
        """
        recipe.tags.clear()
        AmountIngredient.objects.filter(recipe=recipe).delete()
        recipe.tags(validated_data.pop('tags'), recipe)
        recipe.ingredients(validated_data.pop('ingredients'), recipe)
        return super().update(recipe, validated_data)
