"""
URL-маршруты REST API (лабораторная работа №20).
Используется DefaultRouter из DRF, который автоматически генерирует
маршруты list/create/retrieve/update/partial_update/destroy для каждого ViewSet.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import (
    CartItemViewSet,
    CartViewSet,
    CategoryViewSet,
    ManufacturerViewSet,
    MeView,
    OrderItemViewSet,
    OrderViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"manufacturers", ManufacturerViewSet, basename="manufacturer")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"carts", CartViewSet, basename="cart")
router.register(r"cart-items", CartItemViewSet, basename="cartitem")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")

urlpatterns = [
    path("me/", MeView.as_view(), name="api-me"),
] + router.urls
