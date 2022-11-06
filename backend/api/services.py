from string import hexdigits

from rest_framework.serializers import ValidationError

from recipes.models import AmountIngredient


def recipe_amount_ingredients_set(recipe, ingredients):
    """Записывает ингредиенты вложенные в рецепт.
    """
    ingredients_list = []
    for ingredient in ingredients:
        new_ingredient = AmountIngredient(
            recipe=recipe,
            ingredients=ingredient['ingredient'],
            amount=ingredient['amount']
        )
        ingredients_list.append(new_ingredient)
        AmountIngredient.objects.bulk_create(ingredients_list)


def check_value_validate(value, klass=None):
    """Проверяет корректность переданного значения.
    """
    if not str(value).isdecimal():
        raise ValidationError(
            f'{value} должно содержать цифру'
        )
    if klass:
        obj = klass.objects.filter(id=value)
        if not obj:
            raise ValidationError(
                f'{value} не существует'
            )
        return obj[0]


def is_hex_color(value):
    """Проверяет - может ли значение быть шестнадцатеричным цветом.
    """
    if len(value) not in (3, 6):
        raise ValidationError(
            f'{value} не правильной длины ({len(value)}).'
        )
    if not set(value).issubset(hexdigits):
        raise ValidationError(
            f'{value} не шестнадцатиричное.'
        )


# Словарь для сопостановления латинской и русской стандартных раскладок.
incorrect_layout = str.maketrans(
    'qwertyuiop[]asdfghjkl;\'zxcvbnm,./',
    'йцукенгшщзхъфывапролджэячсмитьбю.'
)
