from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    """Модель "Категория товара"."""

    name = models.CharField("название", max_length=100)
    description = models.TextField("описание", blank=True)

    class Meta:
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товаров"

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Модель "Производитель"."""

    name = models.CharField("название", max_length=100)
    country = models.CharField("страна", max_length=100)
    description = models.TextField("описание", blank=True)

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель "Товар"."""

    name = models.CharField("название", max_length=200)
    description = models.TextField("описание")
    photo = models.ImageField(
        "фото товара", upload_to="products/", blank=True, null=True
    )
    price = models.DecimalField(
        "цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock_quantity = models.IntegerField(
        "количество на складе",
        validators=[MinValueValidator(0)],
    )
    category = models.ForeignKey(
        Category,
        verbose_name="категория",
        on_delete=models.CASCADE,
        related_name="products",
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name="производитель",
        on_delete=models.CASCADE,
        related_name="products",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

    def clean(self):
        # Дополнительная проверка на уровне модели (на случай создания
        # объекта без формы, где валидаторы поля могут не вызываться напрямую).
        errors = {}
        if self.price is not None and self.price < 0:
            errors["price"] = "Цена не может быть отрицательной."
        if self.stock_quantity is not None and self.stock_quantity < 0:
            errors["stock_quantity"] = "Количество на складе не может быть отрицательным."
        if errors:
            raise ValidationError(errors)


class Cart(models.Model):
    """Модель "Корзина", связанная один-к-одному с пользователем."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    def total_cost(self):
        """Считает суммарную стоимость всех элементов корзины."""
        return sum(item.item_cost() for item in self.items.all())

    # Псевдоним на русском языке, как указано в задании
    общая_стоимость = total_cost


class CartItem(models.Model):
    """Модель "Элемент корзины"."""

    cart = models.ForeignKey(
        Cart,
        verbose_name="корзина",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        verbose_name="товар",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField("количество")

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"

    def item_cost(self):
        """Возвращает стоимость данного элемента корзины (цена * количество)."""
        return self.product.price * self.quantity

    # Псевдоним на русском языке, как указано в задании
    стоимость_элемента = item_cost

    def clean(self):
        # Количество не должно превышать остаток на складе.
        if self.product_id and self.quantity is not None:
            if self.quantity > self.product.stock_quantity:
                raise ValidationError(
                    {
                        "quantity": (
                            "Количество в корзине не может превышать "
                            "количество товара на складе "
                            f"({self.product.stock_quantity} шт.)."
                        )
                    }
                )


class Order(models.Model):
    """
    Модель "Заказ" (лабораторная работа №19).
    Создаётся на основе содержимого корзины при оформлении заказа.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    delivery_address = models.CharField("адрес доставки", max_length=255)
    comment = models.TextField("комментарий к заказу", blank=True)
    created_at = models.DateTimeField("дата оформления", auto_now_add=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ №{self.pk} ({self.user.username})"

    def total_cost(self):
        """Считает суммарную стоимость всех позиций заказа."""
        return sum(item.item_cost() for item in self.items.all())


class OrderItem(models.Model):
    """
    Модель "Позиция заказа".
    Хранит снимок цены товара на момент оформления заказа,
    чтобы итоговая сумма не менялась при последующем изменении цены товара.
    """

    order = models.ForeignKey(
        Order,
        verbose_name="заказ",
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        verbose_name="товар",
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField("количество")
    price = models.DecimalField(
        "цена на момент заказа", max_digits=10, decimal_places=2
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"

    def item_cost(self):
        """Возвращает стоимость позиции заказа (цена на момент заказа * количество)."""
        return self.price * self.quantity


class Profile(models.Model):
    """
    Профиль пользователя (лабораторная работа №22).
    Связан с User один-к-одному, создаётся автоматически при регистрации
    (см. сигнал post_save ниже).
    """

    EXPERIENCE_BEGINNER = "beginner"
    EXPERIENCE_PRACTITIONER = "practitioner"
    EXPERIENCE_INSTRUCTOR = "instructor"
    EXPERIENCE_CHOICES = [
        (EXPERIENCE_BEGINNER, "Новичок"),
        (EXPERIENCE_PRACTITIONER, "Практикующий"),
        (EXPERIENCE_INSTRUCTOR, "Инструктор"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField("полное имя", max_length=150, blank=True)
    phone = models.CharField("телефон", max_length=30, blank=True)
    address = models.CharField("адрес доставки по умолчанию", max_length=255, blank=True)

    # Поля, специфичные для тематики магазина (вариант 22 -- товары для йоги)
    favorite_category = models.ForeignKey(
        Category,
        verbose_name="любимая категория товаров",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    experience_level = models.CharField(
        "уровень практики",
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default=EXPERIENCE_BEGINNER,
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль пользователя {self.user.username}"

    @property
    def is_admin_role(self):
        """
        Роль пользователя для отображения в личном кабинете (лр22).
        В проекте роль администратора/менеджера определяется через
        стандартный флаг Django `is_staff` (вариант 1 из задания).
        """
        return self.user.is_staff

