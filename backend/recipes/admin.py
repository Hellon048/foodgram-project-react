from django.contrib.admin import ModelAdmin, TabularInline, register, site
from django.utils.safestring import mark_safe

from .models import AmountIngredient, Ingredient, Recipe, Tag, Favorite

site.site_header = 'Администрирование Foodgram'
EMPTY_VALUE_DISPLAY = 'Значение не указано'


class IngredientInline(TabularInline):
    model = AmountIngredient
    extra = 2


@register(AmountIngredient)
class LinksAdmin(ModelAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = (
        'name', 'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'name',
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'name', 'author', 'get_image', 'get_ingredients',
    )
    fields = (
        ('name', 'cooking_time',),
        ('author', 'tags',),
        ('text',),
        ('image',),
    )
    raw_id_fields = ('author', )
    search_fields = (
        'name', 'author',
    )
    list_filter = (
        'name', 'author__username',
    )

    inlines = (IngredientInline,)
    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30"')

    get_image.short_description = 'Изображение'

    def get_ingredients(self, obj):
        return ', '.join(
            [str(ingredients) for ingredients in obj.ingredients.all()]
        )
    get_ingredients.short_description = 'Ингредиенты'

    def favorites(self, obj):
        if Favorite.objects.filter(recipe=obj).exists():
            return Favorite.objects.filter(recipe=obj).count()
        return 0


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = (
        'name', 'color', 'slug',
    )
    search_fields = (
        'name', 'color'
    )

    save_on_top = True
    empty_value_display = EMPTY_VALUE_DISPLAY
