from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver



class Profile(models.Model):
    # TODO переделать на заранее определенный список должностей
    # TODO переделать на заранее определенный список организаций
    # TODO какие-то Бейджи (ачивки?)

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)

    full_name = models.CharField("ФИО", max_length=255, blank=True)

    position = models.CharField("Должность", max_length=200, blank=True)

    organization = models.CharField("Образовательная организация", max_length=255, blank=True)

    photo = models.ImageField("Фото профиля", upload_to='profiles/', null=True, blank=True)


    favorites = models.ManyToManyField(
        'library.LibraryFile',
        related_name='favorited',
        blank=True
    )

    def __str__(self):
        return f"{self.full_name}"


# Сигналы, связывающие Profile с User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
