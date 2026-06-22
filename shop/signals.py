"""
Сигналы Django (лабораторная работа №22).
Автоматически создают/обновляют профиль пользователя при создании User
(в том числе для пользователей, созданных через /admin/ или Python shell,
не только через форму регистрации).
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # На случай, если пользователь существовал до подключения профилей
        # (например, тестовые данные из ранних лабораторных).
        Profile.objects.get_or_create(user=instance)
