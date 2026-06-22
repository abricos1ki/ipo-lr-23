from django.contrib import admin

from .models import Cart, CartItem, Category, Manufacturer, Order, OrderItem, Product, Profile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country")
    search_fields = ("name", "country")
    list_filter = ("country",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "manufacturer",
        "price",
        "stock_quantity",
    )
    list_filter = ("category", "manufacturer")
    search_fields = ("name", "description")
    ordering = ("name",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity")
    list_filter = ("cart",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "delivery_address", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "delivery_address")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price")
    list_filter = ("order",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "phone", "experience_level", "is_admin_role")
    list_filter = ("experience_level",)
    search_fields = ("user__username", "full_name", "phone")

    @admin.display(boolean=True, description="Администратор")
    def is_admin_role(self, obj):
        return obj.is_admin_role
