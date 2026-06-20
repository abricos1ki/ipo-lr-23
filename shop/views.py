from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Category, Manufacturer, Product


def home(request):
    """
    Главная страница магазина.
    Содержит ссылки на страницу "Об авторе" и страницу "О магазине".
    """
    text = (
        "Интернет-магазин товаров для йоги\n"
        "==================================\n\n"
        "Добро пожаловать в учебный интернет-магазин товаров для практики йоги!\n\n"
        "Доступные страницы:\n"
        "  - /about-author/  -- информация об авторе лабораторной работы\n"
        "  - /about-shop/    -- информация о магазине\n"
        "  - /products/      -- список товаров (фильтрация, поиск, сортировка)\n"
    )
    return HttpResponse(text, content_type="text/plain; charset=utf-8")


def about_author(request):
    """
    Страница "Об авторе".
    Содержит информацию о том, кто выполнил лабораторную работу.
    """
    text = (
        "Об авторе\n"
        "=========\n\n"
        "Автор: Саплицкий Родион Александрович\n\n"
        "Лабораторная работа №16\n"
        "Тема: Создание и базовая настройка приложений Django\n"
        "Вариант: 22\n\n"
        "Работа выполнена в рамках изучения дисциплины,\n"
        "связанной с веб-разработкой на фреймворке Django.\n"
        "Цель работы -- освоить базовую настройку проекта Django\n"
        "и приложения для дальнейшей разработки интернет-магазина.\n"
    )
    return HttpResponse(text, content_type="text/plain; charset=utf-8")


def about_shop(request):
    """
    Страница "О магазине".
    Содержит информацию о теме лабораторной работы (вариант 22).
    """
    text = (
        "О магазине\n"
        "==========\n\n"
        "Тема (вариант 22): интернет-магазин товаров для йоги.\n\n"
        "Магазин предлагает товары для практики йоги:\n"
        "  - коврики для йоги;\n"
        "  - аксессуары (ремни, блоки, подушки для медитации);\n"
        "  - одежда для занятий йогой;\n"
        "  - товары для дома и атмосферы (свечи, ароматические диффузоры).\n\n"
        "В рамках данной лабораторной работы реализована только базовая\n"
        "структура Django-проекта и приложения (без моделей и базы данных\n"
        "товаров -- это будет добавлено в следующих лабораторных работах).\n"
    )
    return HttpResponse(text, content_type="text/plain; charset=utf-8")


def product_list(request):
    """
    Список товаров (лабораторная работа №17).

    Поддерживает через GET-параметры:
      - category     -- фильтрация по id категории
      - manufacturer -- фильтрация по id производителя
      - q            -- поиск по названию или описанию (через Q-объекты)
      - sort         -- сортировка: 'price_asc', 'price_desc', 'name'
      - page         -- номер страницы (пагинация, 10 товаров на страницу)
    """
    products = Product.objects.select_related("category", "manufacturer").all()

    category_id = request.GET.get("category")
    if category_id:
        products = products.filter(category_id=category_id)

    manufacturer_id = request.GET.get("manufacturer")
    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)

    query = request.GET.get("q")
    if query:
        # Поиск по названию ИЛИ по описанию товара с помощью объекта Q
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    sort = request.GET.get("sort")
    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "name":
        products = products.order_by("name")
    else:
        products = products.order_by("id")

    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "manufacturers": Manufacturer.objects.all(),
        "current_category": category_id,
        "current_manufacturer": manufacturer_id,
        "query": query or "",
        "sort": sort or "",
    }
    return render(request, "shop/product_list.html", context)


def product_detail(request, pk):
    """
    Страница детализации товара (лабораторная работа №17).
    Получение объекта по id с обработкой ошибки 404, если товар не найден.
    """
    product = get_object_or_404(
        Product.objects.select_related("category", "manufacturer"), pk=pk
    )
    return render(request, "shop/product_detail.html", {"product": product})
