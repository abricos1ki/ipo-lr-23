from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('about-author/', views.about_author, name='about_author'),
    path('about-shop/', views.about_shop, name='about_shop'),

    # Каталог товаров (лабораторная работа №17/№18)
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('catalog/', views.product_list, name='catalog'),
    path('catalog/<int:pk>/', views.product_detail, name='catalog_detail'),

    # Корзина (лабораторная работа №18)
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Оформление заказа (лабораторная работа №19)
    path('checkout/', views.checkout, name='checkout'),
]
