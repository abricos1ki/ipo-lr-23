"""
Кастомные классы прав доступа DRF (лабораторная работа №22).

Роль администратора/менеджера в проекте определяется стандартным
флагом Django `is_staff` (вариант 1 из задания лр22): это совместимо
с уже существующей админ-панелью Django и не требует дополнительной
модели ролей.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Чтение (GET/HEAD/OPTIONS) каталога доступно всем аутентифицированным
    пользователям; изменение (POST/PUT/PATCH/DELETE) -- только пользователям
    с правами администратора/менеджера (is_staff=True).
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Доступ к объекту разрешён только его владельцу (obj.user) или
    администратору (is_staff=True). Используется для заказов и корзин,
    где queryset уже отфильтрован в get_queryset(), но дополнительная
    object-level проверка защищает от прямого обращения по id.
    """

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        return bool(
            request.user.is_staff or (owner is not None and owner == request.user)
        )
