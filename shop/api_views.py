"""
API-представления (ModelViewSet) для Django REST Framework
(лабораторная работа №20).
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Cart, CartItem, Category, Manufacturer, Order, OrderItem, Product
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    ManufacturerSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD-операции над категориями товаров: /api/categories/"""

    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class ManufacturerViewSet(viewsets.ModelViewSet):
    """CRUD-операции над производителями: /api/manufacturers/"""

    queryset = Manufacturer.objects.all().order_by("id")
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD-операции над товарами: /api/products/
    Поддерживает фильтрацию через query-параметры category и manufacturer.
    """

    queryset = Product.objects.select_related("category", "manufacturer").order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get("category")
        manufacturer_id = self.request.query_params.get("manufacturer")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if manufacturer_id:
            queryset = queryset.filter(manufacturer_id=manufacturer_id)
        return queryset


class CartViewSet(viewsets.ModelViewSet):
    """
    Операции над корзинами: /api/carts/
    Пользователь видит и может изменять только свою собственную корзину.
    """

    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Обычный пользователь видит только свою корзину;
        # суперпользователь -- все корзины (удобно для администрирования).
        if self.request.user.is_superuser:
            return Cart.objects.all().order_by("id")
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    Операции над элементами корзины: /api/cart-items/
    Пользователь видит и может изменять только элементы своей корзины.
    """

    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return CartItem.objects.select_related("cart", "product").order_by("id")
        return CartItem.objects.filter(cart__user=self.request.user).select_related(
            "cart", "product"
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    Операции над заказами: /api/orders/
    Пользователь видит и может изменять только свои собственные заказы.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Операции над позициями заказа: /api/order-items/
    Пользователь видит и может изменять только позиции своих заказов.
    """

    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return OrderItem.objects.select_related("order", "product").order_by("id")
        return OrderItem.objects.filter(order__user=self.request.user).select_related(
            "order", "product"
        )
