from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (CASCADE, CharField, CheckConstraint,
                              DateTimeField, ForeignKey, ImageField,
                              ManyToManyField, Model,
                              PositiveSmallIntegerField, Q, TextField,
                              UniqueConstraint)
from django.db.models.functions import Length

from api.conf import MAX_LEN_RECIPES_CHARFIELD, MAX_LEN_RECIPES_TEXTFIELD
from users.models import MyUser

CharField.register_lookup(Length)


class Tag(Model):
    BLUE = '#0000FF'
    ORANGE = '#FFA500'
    GREEN = '#008000'
    PURPLE = '#800080'
    YELLOW = '#FFFF00'

    COLOR_CHOICES = [
        (BLUE, 'Синий'),
        (ORANGE, 'Оранжевый'),
        (GREEN, 'Зеленый'),
        (PURPLE, 'Фиолетовый'),
        (YELLOW, 'Желтый'),
    ]
    name = CharField(
        verbose_name='Тэг',
        max_length=MAX_LEN_RECIPES_CHARFIELD,
        unique=True,
    )
    color = CharField(max_length=7,
                      unique=True,
                      choices=COLOR_CHOICES,
                      verbose_name='Цвет в HEX')
    slug = CharField(
        verbose_name='Слаг тэга',
        max_length=MAX_LEN_RECIPES_CHARFIELD,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)
        constraints = (
            CheckConstraint(
                check=Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
            CheckConstraint(
                check=Q(color__length__gt=0),
                name='\n%(app_label)s_%(class)s_color is empty\n',
            ),
            CheckConstraint(
                check=Q(slug__length__gt=0),
                name='\n%(app_label)s_%(class)s_slug is empty\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.name} (цвет: {self.color})'


class Ingredient(Model):
    name = CharField(
        verbose_name='Ингридиент',
        max_length=MAX_LEN_RECIPES_CHARFIELD,
    )
    measurement_unit = CharField(
        verbose_name='Единицы измерения',
        max_length=MAX_LEN_RECIPES_CHARFIELD,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)
        constraints = (
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_for_ingredient'
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
            CheckConstraint(
                check=Q(measurement_unit__length__gt=0),
                name='\n%(app_label)s_%(class)s_measurement_unit is empty\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.name} {self.measurement_unit}'


class Recipe(Model):
    name = CharField(
        verbose_name='Название блюда',
        max_length=MAX_LEN_RECIPES_CHARFIELD,
    )
    author = ForeignKey(
        verbose_name='Автор рецепта',
        to=MyUser,
        on_delete=CASCADE,
        related_name='recipes',
    )
    tags = ManyToManyField(
        verbose_name='Тег',
        related_name='recipes',
        to='Tag',
    )
    ingredients = ManyToManyField(
        verbose_name='Ингредиенты блюда',
        related_name='recipes',
        to=Ingredient,
        through='recipes.AmountIngredient',
    )
    pub_date = DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    image = ImageField(
        verbose_name='Изображение блюда',
        upload_to='recipe_images/',
    )
    text = TextField(
        verbose_name='Описание блюда',
        max_length=MAX_LEN_RECIPES_TEXTFIELD,
    )
    cooking_time = PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        default=1,
        validators=(
            MinValueValidator(
                1,
                'Ваше блюдо уже готово!'
            ),
            MaxValueValidator(
                600,
                'Очень долго ждать...'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = (
            UniqueConstraint(
                fields=('name', 'author'),
                name='unique_for_author'
            ),
            CheckConstraint(
                check=Q(name__length__gt=0),
                name='\n%(app_label)s_%(class)s_name is empty\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.name}. Автор: {self.author.username}'


class AmountIngredient(Model):
    recipe = ForeignKey(
        verbose_name='В каких рецептах',
        to=Recipe,
        on_delete=CASCADE,
    )
    ingredients = ForeignKey(
        verbose_name='Связанные ингредиенты',
        to=Ingredient,
        on_delete=CASCADE,
    )
    amount = PositiveSmallIntegerField(
        verbose_name='Количество',
        default=1,
        validators=(
            MinValueValidator(
                1, 'Нужно хоть какое-то количество.'
            ),
            MaxValueValidator(
                10000, 'Слишком много!'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('recipe',)
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'ingredients'),
                name='\n%(app_label)s_%(class)s ingredient alredy added\n',
            ),
        )

    def __str__(self) -> str:
        return f'{self.amount} {self.ingredients}'


class Favorite(Model):
    """ Модель добавление в избраное. """
    user = ForeignKey(
        MyUser,
        on_delete=CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favorite_unique'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(Model):
    """ Модель списка покупок. """
    user = ForeignKey(
        MyUser,
        on_delete=CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_list',
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_list',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_shoppinglist_unique'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
