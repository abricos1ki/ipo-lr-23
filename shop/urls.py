from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('about-author/', views.about_author, name='about_author'),
    path('about-shop/', views.about_shop, name='about_shop'),
]
