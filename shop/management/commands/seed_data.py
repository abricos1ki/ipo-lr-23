import random
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Cart, CartItem, Category, Manufacturer, Product


MANUFACTURERS = [
    ("YogaDesign Lab", "США", "Производитель ковриков и аксессуаров премиум-класса."),
    ("Manduka", "США", "Один из самых известных мировых брендов товаров для йоги."),
    ("Ярослав", "Беларусь", "Локальный производитель текстиля и аксессуаров для йоги."),
    ("Bodhi", "Германия", "Экологичные коврики и пропсы из натуральных материалов."),
    ("Liforme", "Великобритания", "Премиальные коврики с разметкой для выравнивания тела."),
]

CATEGORIES = [
    ("Коврики для йоги", "Коврики различной плотности и материала для практики."),
    ("Блоки для йоги", "Опорные блоки для растяжки и выравнивания позы."),
    ("Ремни для йоги", "Ремни-стропы для углубления растяжки."),
    ("Подушки для медитации", "Подушки (болстеры, дзафу) для медитации и релаксации."),
    ("Одежда для йоги", "Удобная одежда из дышащих тканей для занятий."),
    ("Аксессуары для дома", "Свечи, диффузоры и предметы для атмосферы практики."),
    ("Сумки и чехлы", "Сумки и чехлы для переноски ковриков и инвентаря."),
    ("Полотенца для йоги", "Впитывающие полотенца для горячей йоги и пилатеса."),
    ("Массажные мячи и роллы", "Инвентарь для миофасциального релиза."),
    ("Книги и материалы", "Книги и обучающие материалы по практике йоги."),
]

PRODUCT_TEMPLATES = [
    ("Коврик для йоги \"{m}\" {n}мм", "Коврик для йоги {n} мм, нескользящее покрытие, бренд {m}."),
    ("Блок для йоги \"{m}\"", "Опорный блок для йоги из пробки/EVA, бренд {m}."),
    ("Ремень для йоги \"{m}\" {n}см", "Ремень-стропа длиной {n} см для растяжки, бренд {m}."),
    ("Болстер для медитации \"{m}\"", "Подушка-болстер для медитации и релаксации, бренд {m}."),
    ("Топ для йоги \"{m}\"", "Дышащий топ для занятий йогой, бренд {m}."),
    ("Леггинсы для йоги \"{m}\"", "Эластичные леггинсы для практики йоги, бренд {m}."),
    ("Ароматическая свеча \"{m}\"", "Соевая свеча для создания атмосферы во время практики, {m}."),
    ("Сумка для коврика \"{m}\"", "Сумка-чехол для переноски коврика для йоги, {m}."),
    ("Полотенце для йоги \"{m}\"", "Впитывающее полотенце для горячей йоги, бренд {m}."),
    ("Массажный мяч \"{m}\"", "Мяч для миофасциального релиза мышц, бренд {m}."),
]


class Command(BaseCommand):
    help = (
        "Заполняет базу данных тестовыми данными: 5 производителей, "
        "10 категорий, 34 товара, 5 пользователей (с корзинами и позициями)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Очистка существующих данных...")
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Manufacturer.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Создание производителей...")
        manufacturers = [
            Manufacturer.objects.create(name=name, country=country, description=desc)
            for name, country, desc in MANUFACTURERS
        ]

        self.stdout.write("Создание категорий...")
        categories = [
            Category.objects.create(name=name, description=desc)
            for name, desc in CATEGORIES
        ]

        self.stdout.write("Создание товаров...")
        products = []
        for i in range(34):
            template_name, template_desc = PRODUCT_TEMPLATES[i % len(PRODUCT_TEMPLATES)]
            manufacturer = random.choice(manufacturers)
            category = categories[i % len(categories)]
            size_value = random.choice([4, 5, 6, 8, 180, 200, 250])

            name = template_name.format(m=manufacturer.name, n=size_value)
            # Делаем название уникальнее, добавляя порядковый номер партии при повторах
            if i >= len(PRODUCT_TEMPLATES):
                name = f"{name} (партия {i // len(PRODUCT_TEMPLATES) + 1})"

            description = template_desc.format(m=manufacturer.name, n=size_value)
            price = Decimal(random.randrange(1500, 25000)) / 100 * 10  # 15.00 - 2500.00
            price = price.quantize(Decimal("0.01"))
            stock_quantity = random.randint(0, 50)

            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                stock_quantity=stock_quantity,
                category=category,
                manufacturer=manufacturer,
            )
            products.append(product)

        self.stdout.write("Создание пользователей и корзин...")
        usernames = ["anna", "ivan", "olga", "dmitry", "maria"]
        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            if created:
                user.set_password("password123")
                user.save()

            cart, _ = Cart.objects.get_or_create(user=user)

            # Добавляем в корзину 2 случайных товара с остатком на складе
            available_products = [p for p in products if p.stock_quantity > 0]
            chosen = random.sample(available_products, k=min(2, len(available_products)))
            for product in chosen:
                max_qty = min(3, product.stock_quantity)
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=random.randint(1, max(1, max_qty)),
                )

        self.stdout.write(self.style.SUCCESS(
            "Готово: "
            f"{len(manufacturers)} производителей, "
            f"{len(categories)} категорий, "
            f"{len(products)} товаров, "
            f"{len(usernames)} пользователей с корзинами."
        ))
        self.stdout.write("Пароль для всех тестовых пользователей: password123")
