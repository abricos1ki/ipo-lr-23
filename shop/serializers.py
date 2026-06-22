"""
Сериализаторы Django REST Framework (лабораторная работа №20).
Определяют, как объекты моделей преобразуются в JSON и обратно для API.
"""

from rest_framework import serializers

from .models import Cart, CartItem, Category, Manufacturer, Order, OrderItem, Product, Profile


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор модели "Категория товара"."""

    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class ManufacturerSerializer(serializers.ModelSerializer):
    """Сериализатор модели "Производитель"."""

    class Meta:
        model = Manufacturer
        fields = ["id", "name", "country", "description"]


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели "Товар".

    Поля category_name и manufacturer_name -- удобные для чтения
    дополнительные поля (read-only), не заменяющие основные FK-поля
    category/manufacturer, которые используются для записи (создание/обновление).
    """

    category_name = serializers.CharField(source="category.name", read_only=True)
    manufacturer_name = serializers.CharField(source="manufacturer.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "photo",
            "price",
            "stock_quantity",
            "category",
            "category_name",
            "manufacturer",
            "manufacturer_name",
        ]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Количество на складе не может быть отрицательным."
            )
        return value


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор модели "Элемент корзины"."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    item_cost = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "cart", "product", "product_name", "quantity", "item_cost"]

    def get_item_cost(self, obj):
        return obj.item_cost()

    def validate(self, data):
        product = data.get("product") or getattr(self.instance, "product", None)
        quantity = data.get("quantity") or getattr(self.instance, "quantity", None)
        if product and quantity and quantity > product.stock_quantity:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        "Количество в корзине не может превышать остаток "
                        f"на складе ({product.stock_quantity} шт.)."
                    )
                }
            )
        return data


class CartSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели "Корзина".
    Включает вложенный список элементов корзины (только для чтения)
    и общую стоимость корзины.
    """

    items = CartItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "created_at", "items", "total_cost"]
        read_only_fields = ["user", "created_at"]

    def get_total_cost(self, obj):
        return obj.total_cost()


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор модели "Элемент заказа" (позиция заказа)."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    item_cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "product_name", "quantity", "price", "item_cost"]

    def get_item_cost(self, obj):
        return obj.item_cost()


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели "Заказ".
    Включает вложенный список позиций заказа (только для чтения)
    и итоговую стоимость заказа.
    """

    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "delivery_address",
            "comment",
            "created_at",
            "items",
            "total_cost",
        ]
        read_only_fields = ["user", "created_at"]

    def get_total_cost(self, obj):
        return obj.total_cost()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор профиля пользователя (лабораторная работа №22).
    Используется для эндпоинта GET/PATCH /api/me/.
    Поля username/email/is_staff -- только для чтения (отображение роли
    и логина); редактируются full_name, phone, address,
    favorite_category, experience_level.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_staff = serializers.BooleanField(source="user.is_staff", read_only=True)
    favorite_category_name = serializers.CharField(
        source="favorite_category.name", read_only=True, default=None
    )
    experience_level_display = serializers.CharField(
        source="get_experience_level_display", read_only=True
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "is_staff",
            "full_name",
            "phone",
            "address",
            "favorite_category",
            "favorite_category_name",
            "experience_level",
            "experience_level_display",
        ]
