from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Cart, CartItem, Category, Manufacturer, Product


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
        "  - /catalog/       -- каталог товаров (фильтрация, поиск, сортировка)\n"
        "  - /cart/          -- корзина пользователя (требуется вход в систему)\n"
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


def _get_or_create_cart(user):
    """Вспомогательная функция: получить (или создать) корзину пользователя."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
@require_POST
def add_to_cart(request, product_id):
    """
    Добавление товара в корзину (лабораторная работа №18).
    Доступно только аутентифицированным пользователям (@login_required).
    Если товар уже есть в корзине -- увеличивает количество,
    иначе создаёт новый CartItem.
    """
    product = get_object_or_404(Product, pk=product_id)
    cart = _get_or_create_cart(request.user)

    try:
        quantity_to_add = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity_to_add = 1
    quantity_to_add = max(1, quantity_to_add)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={"quantity": 0}
    )
    new_quantity = cart_item.quantity + quantity_to_add

    if new_quantity > product.stock_quantity:
        messages.error(
            request,
            f"Нельзя добавить {quantity_to_add} шт. товара \"{product.name}\": "
            f"на складе доступно только {product.stock_quantity} шт. "
            f"(в корзине уже {cart_item.quantity} шт.).",
        )
        if created:
            cart_item.delete()
        return redirect("shop:product_detail", pk=product_id)

    cart_item.quantity = new_quantity
    cart_item.save()
    messages.success(request, f"Товар \"{product.name}\" добавлен в корзину.")
    return redirect("shop:cart_view")


@login_required
@require_POST
def update_cart(request, item_id):
    """
    Обновление количества товара в корзине (лабораторная работа №18).
    Валидация: количество не должно превышать остаток на складе.
    """
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)

    try:
        new_quantity = int(request.POST.get("quantity"))
    except (TypeError, ValueError):
        messages.error(request, "Некорректное значение количества.")
        return redirect("shop:cart_view")

    if new_quantity < 1:
        messages.error(request, "Количество должно быть не менее 1.")
        return redirect("shop:cart_view")

    if new_quantity > cart_item.product.stock_quantity:
        messages.error(
            request,
            f"Количество не может превышать остаток на складе "
            f"({cart_item.product.stock_quantity} шт.).",
        )
        return redirect("shop:cart_view")

    cart_item.quantity = new_quantity
    cart_item.save()
    messages.success(request, f"Количество товара \"{cart_item.product.name}\" обновлено.")
    return redirect("shop:cart_view")


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """
    Удаление товара из корзины (лабораторная работа №18).
    """
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Товар \"{product_name}\" удалён из корзины.")
    return redirect("shop:cart_view")


@login_required
def cart_view(request):
    """
    Просмотр корзины пользователя (лабораторная работа №18).
    Отображает все элементы корзины с общей стоимостью.
    Доступно только аутентифицированным пользователям (@login_required).
    """
    cart = _get_or_create_cart(request.user)
    items = cart.items.select_related("product").all()

    context = {
        "cart": cart,
        "items": items,
        "total_cost": cart.total_cost(),
    }
    return render(request, "shop/cart.html", context)
