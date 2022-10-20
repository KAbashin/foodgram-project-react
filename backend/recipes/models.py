from django.contrib.auth import get_user_model
from django.core.validators import (MinValueValidator, MaxValueValidator,
                                    RegexValidator)
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        help_text='Введите название продуктов',
#        db_index=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
        help_text='Введите единицы измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=50,
#        db_index=True,
    )
    color = models.CharField(
        verbose_name='Цветовой HEX-код',
        unique=True,
        max_length=7,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='Введенное значение не является цветом в формате HEX!'
            )
        ],
        default='#006400',
        help_text='Введите цвет тега. Например, #006400',
    )
    slug = models.SlugField(
        verbose_name='Текстовый идентификатор тега',
        unique=True,
        max_length=50,
        help_text='Введите текстовый идентификатор тега'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipe',
        on_delete=models.CASCADE,
        help_text='Выберите автора рецепта',
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200,
        help_text='Введите название рецепта',
#        db_index=True,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='static/recipe/',
        blank=True,
        null=True,
        help_text='Выберите изображение рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите описания рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        help_text='Выберите продукты рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег рецепта',
        related_name='recipes',
        help_text='Выберите тег рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(1, message='Минимальное значение 1!'),
            MaxValueValidator(600, message='Максимальное значение 600!')
        ],
        help_text='Введите время приготовления'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        help_text='Дата публикации',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.author.email}, {self.name}'


class RecipeIngredient(models.Model):
    """Модель количества ингридиентов в отдельных рецептах"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт',
        help_text='Выберите рецепт',
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient',
        help_text='Добавить продукты рецепта в корзину',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        default=1,
        validators=[
            MinValueValidator(1, message='Минимальное количество 1!'),
            MaxValueValidator(10000, message='Максимальное значение 10000!')
        ],
        help_text='Введите количество продукта',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиентов в рецепте'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique ingredient')]


class Subscribe(models.Model):
    """Модель подписки на авторов"""
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        help_text='Выберите пользователя, который подписывается',
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Автор',
        on_delete=models.CASCADE,
        help_text='Выберите автора, на которого подписываются',
    )
    created = models.DateTimeField(
        verbose_name='Дата подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription')]

    def __str__(self):
        return f'Пользователь {self.user} -> автор {self.author}'


class FavoriteRecipe(models.Model):
    """Модель избранного рецепта"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Пользователь',
        related_name='favorite_recipe',
        help_text='Выберите пользователя',
    )
    recipe = models.ManyToManyField(
        Recipe,
        verbose_name='Избранный рецепт',
        related_name='favorite_recipe',
        help_text='Выберите рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'Пользователь {self.user} добавил "{self.recipe}" в Избранное'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(
            sender, instance, created, **kwargs):
        if created:
            return FavoriteRecipe.objects.create(user=instance)


class ShoppingCart(models.Model):
    """Модель списка покупок"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
        null=True,
        help_text='Выберите пользователя',
    )
    recipe = models.ManyToManyField(
        Recipe,
        verbose_name='Рецепт в списке',
        related_name='shopping_cart',
        help_text='Выберите рецепты для добавления в список покупок',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['-id']

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в список покупок'

    @receiver(post_save, sender=User)
    def create_shopping_cart(
            sender, instance, created, **kwargs):
        if created:
            return ShoppingCart.objects.create(user=instance)
