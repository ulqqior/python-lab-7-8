"""Моделі даних онлайн-бібліотеки для Django ORM (Завдання 1-2)."""
from django.db import models
from django.urls import reverse


class Author(models.Model):
    """Сутність Автора книги."""

    first_name = models.CharField(
        max_length=100,
        verbose_name="Ім'я",
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Прізвище",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Електронна пошта",
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата народження",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний автор",
    )

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Автор"
        verbose_name_plural = "Автори"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AuthorProfile(models.Model):
    """Профіль автора (зв'язок один-до-одного OneToOneField із Author)."""

    # Політика CASCADE: профіль не має самостійного сенсу без сутності автора
    author = models.OneToOneField(
        Author,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Автор",
    )
    biography = models.TextField(
        blank=True,
        default="",
        verbose_name="Біографія",
    )
    website = models.URLField(
        null=True,
        blank=True,
        verbose_name="Особистий вебсайт",
    )
    country = models.CharField(
        max_length=80,
        default="Україна",
        verbose_name="Країна",
    )
    awards_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Кількість літературних нагород",
    )

    class Meta:
        ordering = ["-awards_count", "author__last_name"]
        verbose_name = "Профіль автора"
        verbose_name_plural = "Профілі авторів"

    def __str__(self) -> str:
        return f"Профіль: {self.author} ({self.country})"


class Genre(models.Model):
    """Літературний жанр (використовується у зв'язку багато-до-багатьох із Book)."""

    name = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="Назва жанру",
    )
    slug = models.SlugField(
        max_length=80,
        unique=True,
        verbose_name="URL-ідентифікатор (slug)",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Опис жанру",
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендований жанр",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Жанр"
        verbose_name_plural = "Жанри"

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    """Книга в каталозі онлайн-бібліотеки."""

    STATUS_AVAILABLE = "available"
    STATUS_BORROWED = "borrowed"
    STATUS_ARCHIVED = "archived"

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "В наявності"),
        (STATUS_BORROWED, "Видана читачу"),
        (STATUS_ARCHIVED, "В архіві"),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="Назва книги",
    )
    isbn = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="Код ISBN-13",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
        verbose_name="Статус примірника",
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=250.00,
        verbose_name="Ціна (грн)",
    )
    pages = models.PositiveIntegerField(
        default=100,
        verbose_name="Кількість сторінок",
    )
    published_year = models.IntegerField(
        default=2024,
        verbose_name="Рік видання",
    )
    language = models.CharField(
        max_length=50,
        default="Українська",
        verbose_name="Мова видання",
    )
    summary = models.TextField(
        blank=True,
        default="",
        verbose_name="Короткий опис (анотація)",
    )
    # Політика PROTECT: забороняє видалення автора, поки в бібліотеці зареєстровані його книги
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="Основний автор",
    )
    # Політика SET_NULL: якщо автора-рекомендатора видалено, книга залишається без рекомендації
    recommended_by = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommended_books",
        verbose_name="Ким рекомендовано",
    )
    # Зв'язок багато-до-багатьох із Genre
    genres = models.ManyToManyField(
        Genre,
        related_name="books",
        blank=True,
        verbose_name="Жанри",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата додавання",
    )

    class Meta:
        ordering = ["-published_year", "title"]
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"

    def get_absolute_url(self) -> str:
        return reverse("catalog:book_detail", kwargs={"pk": self.pk})


class BookReview(models.Model):
    """Відгук читача на книгу (зв'язок один-до-багатьох ForeignKey із Book)."""

    # Політика CASCADE: при видаленні книги всі відгуки на неї також видаляються
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Книга",
    )
    reviewer_name = models.CharField(
        max_length=100,
        verbose_name="Ім'я рецензента",
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Оцінка (1-5)",
    )
    comment = models.TextField(
        verbose_name="Текст відгуку",
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name="Схвалено модератором",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата створення",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Відгук на книгу"
        verbose_name_plural = "Відгуки на книги"

    def __str__(self) -> str:
        return f"Відгук від {self.reviewer_name} на «{self.book.title}» ({self.rating}/5)"
