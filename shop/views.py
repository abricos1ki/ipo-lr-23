from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Cart, CartItem, Category, Manufacturer, Order, OrderItem, Product
from .receipts import build_order_receipt


def home(request):
    """
    Главная страница магазина (лабораторная работа №21).
    Hero-секция, сетка популярных товаров (6 штук) и список категорий
    со ссылками на отфильтрованный каталог.
    """
    popular_products = (
        Product.objects.select_related("category", "manufacturer")
        .order_by("-id")[:6]
    )
    categories = Category.objects.all()

    context = {
        "popular_products": popular_products,
        "categories": categories,
    }
    return render(request, "shop/index.html", context)


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
    Список товаров / каталог (лабораторная работа №17, оформление №21).

    Поддерживает через GET-параметры:
      - category     -- фильтрация по id категории
      - manufacturer -- фильтрация по id производителя
      - q            -- поиск по названию или описанию (через Q-объекты)
      - sort         -- сортировка: 'price_asc', 'price_desc', 'name'
      - page         -- номер страницы (пагинация, 9 товаров на страницу)
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

    paginator = Paginator(products, 9)
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


@login_required
def checkout(request):
    """
    Оформление заказа (лабораторная работа №19).
    Доступно только аутентифицированным пользователям (@login_required).

    GET  -- отображает форму с адресом доставки и комментарием.
    POST -- создаёт заказ на основе содержимого корзины, генерирует чек
            в формате Excel, отправляет его на email пользователя
            и очищает корзину.
    """
    cart = _get_or_create_cart(request.user)
    items = list(cart.items.select_related("product").all())

    if request.method == "POST":
        delivery_address = request.POST.get("delivery_address", "").strip()
        comment = request.POST.get("comment", "").strip()

        if not items:
            messages.error(request, "Корзина пуста -- оформить заказ невозможно.")
            return redirect("shop:cart_view")

        if not delivery_address:
            messages.error(request, "Укажите адрес доставки.")
            return render(
                request,
                "shop/checkout.html",
                {"items": items, "total_cost": cart.total_cost()},
            )

        if not request.user.email:
            messages.error(
                request,
                "У вашего аккаунта не указан email -- невозможно отправить чек. "
                "Заполните email в профиле и повторите попытку.",
            )
            return render(
                request,
                "shop/checkout.html",
                {"items": items, "total_cost": cart.total_cost()},
            )

        # Дополнительная проверка остатков перед оформлением заказа
        for item in items:
            if item.quantity > item.product.stock_quantity:
                messages.error(
                    request,
                    f"Товара \"{item.product.name}\" недостаточно на складе "
                    f"(в наличии {item.product.stock_quantity} шт., в корзине {item.quantity} шт.). "
                    "Обновите корзину перед оформлением заказа.",
                )
                return redirect("shop:cart_view")

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    delivery_address=delivery_address,
                    comment=comment,
                )
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                    )
                    # Списываем товар со склада
                    item.product.stock_quantity -= item.quantity
                    item.product.save()

                # Очищаем корзину после успешного оформления заказа
                cart.items.all().delete()

            # Генерация чека в формате Excel
            receipt_buffer = build_order_receipt(order)

            # Отправка чека по электронной почте
            email = EmailMessage(
                subject=f"Чек по заказу №{order.pk} -- Интернет-магазин товаров для йоги",
                body=(
                    f"Здравствуйте, {request.user.username}!\n\n"
                    f"Спасибо за заказ №{order.pk} в интернет-магазине товаров для йоги.\n"
                    f"Адрес доставки: {order.delivery_address}\n"
                    f"Итоговая сумма: {order.total_cost()} BYN\n\n"
                    "Чек по заказу во вложении."
                ),
                to=[request.user.email],
            )
            email.attach(
                f"receipt_order_{order.pk}.xlsx",
                receipt_buffer.read(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            email.send(fail_silently=False)

            messages.success(
                request,
                f"Заказ №{order.pk} успешно оформлен! Чек отправлен на {request.user.email}.",
            )
            return redirect("shop:home")

        except Exception as exc:
            messages.error(
                request,
                f"Не удалось завершить оформление заказа: {exc}",
            )
            return redirect("shop:cart_view")

    # GET-запрос: показываем форму оформления заказа
    context = {
        "items": items,
        "total_cost": cart.total_cost(),
    }
    return render(request, "shop/checkout.html", context)
