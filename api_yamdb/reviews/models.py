from api.utilities import get_confirmation_code
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

ROLE_CHOICES = [('user', 'user'),
                ('moderator', 'moderator'),
                ('admin', 'admin')]


class User(AbstractUser):
    username = models.CharField('Логин пользователя', max_length=150,
                                unique=True,
                                blank=False, null=False,)
    email = models.EmailField('Электронная почта', max_length=254,
                              unique=True, blank=False, null=False,)
    bio = models.TextField('Биография', blank=True,)
    first_name = models.CharField('Имя', max_length=150, blank=True,)
    last_name = models.CharField('Фамилия', max_length=150, blank=True,)
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=20,
        help_text='Используется для получения токена через API',)
    role = models.CharField(
        'Роль',
        max_length=20,
        choices=ROLE_CHOICES,
        default='user', help_text='Пользователь, модератор, администратор',
    )

    @property
    def is_admin(self):
        return (self.is_staff or self.role == ROLE_CHOICES[2][1]
                or self.is_superuser)

    @property
    def is_moderator(self):
        return (self.role == ROLE_CHOICES[1][1] or self.is_superuser)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        if self.confirmation_code == '':
            self.confirmation_code = get_confirmation_code()
        super().save(*args, **kwargs)


class Categorie(models.Model):
    name = models.CharField('Название категории', max_length=256,)
    slug = models.SlugField(
        'Короткий ярлычок', max_length=50, unique=True,
        help_text='Только английские буквы, цифры, подчеркивания или дефисы',)

    class Meta:
        ordering = ['id']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField('Название жанра', max_length=256,)
    slug = models.SlugField(
        'Короткий ярлычок', max_length=50, unique=True,
        help_text='Только английские буквы, цифры, подчеркивания или дефисы',)

    class Meta:
        ordering = ['id']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField('Название произведения', max_length=70,)
    year = models.PositiveIntegerField('Год издания',)
    description = models.TextField('Описание', blank=True,)
    genre = models.ManyToManyField(
        'Genre',
        related_name='titles', verbose_name='Жанры',
    )
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.SET_NULL,
        related_name='titles',
        null=True, verbose_name='Категория',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class Review(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Автор',)
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True,)
    score = models.PositiveSmallIntegerField(
        'Оценка',
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ],
        blank=False,
        null=False,
    )
    text = models.CharField('Текст отзыва', max_length=256,)
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Произведение',)

    class Meta:
        ordering = ['id']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        db_table = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'], name='unique_author_for_title'
            )
        ]

    def __str__(self):
        return self.text


class Comment(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Автор',)
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Отзыв',)
    text = models.TextField('Текст комментария',)
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True,)
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Произведение',)

    class Meta:
        ordering = ['id']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
