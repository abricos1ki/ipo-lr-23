"""
API-представления (ModelViewSet) для Django REST Framework
(лабораторная работа №20, права доступа по ролям -- лабораторная работа №22).
"""

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Category, Manufacturer, Order, OrderItem, Product, Profile
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    ManufacturerSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductSerializer,
    ProfileSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Категории товаров: /api/categories/
    Чтение -- всем аутентифицированным; изменение -- только администратору.
    """

    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ManufacturerViewSet(viewsets.ModelViewSet):
    """
    Производители: /api/manufacturers/
    Чтение -- всем аутентифицированным; изменение -- только администратору.
    """

    queryset = Manufacturer.objects.all().order_by("id")
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """
    Товары: /api/products/
    Чтение (GET) -- всем аутентифицированным пользователям.
    Создание/изменение/удаление (POST/PUT/PATCH/DELETE) -- только
    пользователям с ролью администратора (is_staff=True).
    Поддерживает фильтрацию через query-параметры category и manufacturer.
    """

    queryset = Product.objects.select_related("category", "manufacturer").order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

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
    Покупатель видит и может изменять только свою собственную корзину.
    Администратор (is_staff=True) видит все корзины.
    """

    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Cart.objects.all().order_by("id")
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    Операции над элементами корзины: /api/cart-items/
    Покупатель видит и может изменять только элементы своей корзины.
    Администратор (is_staff=True) видит все элементы.
    """

    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CartItem.objects.select_related("cart", "product").order_by("id")
        return CartItem.objects.filter(cart__user=self.request.user).select_related(
            "cart", "product"
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    Операции над заказами: /api/orders/
    Покупатель видит и может изменять только свои собственные заказы.
    Администратор (is_staff=True) видит все заказы (требование лр22).
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Операции над позициями заказа: /api/order-items/
    Покупатель видит и может изменять только позиции своих заказов.
    Администратор (is_staff=True) видит все позиции.
    """

    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderItem.objects.select_related("order", "product").order_by("id")
        return OrderItem.objects.filter(order__user=self.request.user).select_related(
            "order", "product"
        )


class MeView(APIView):
    """
    Эндпоинт текущего пользователя (лабораторная работа №22):
      GET   /api/me/  -- возвращает профиль текущего пользователя.
      PATCH /api/me/  -- частично обновляет профиль текущего пользователя.

    Доступно только аутентифицированным пользователям. Пользователь
    всегда работает только со своим собственным профилем -- объект
    profile берётся из request.user, а не из URL, поэтому подменить
    чужой профиль через этот эндпоинт невозможно.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
