import os

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from pytils.translit import slugify


class Category(models.Model):
    """Набор категорий для методических материалов в разделе \"Библиотека\""""
    name = models.CharField("Название категории", max_length=100)

    class Meta:
        verbose_name = "Категория методических материалов"
        verbose_name_plural = "Категории методических материалов"

    def __str__(self):
        return self.name


def library_file_path(instance, filename):
    """Формирование пути сохранения файла методических материалов"""
    ext = filename.split('.')[-1]
    name = slugify(instance.title[:200])
    return os.path.join("library", now().strftime('%Y/%m'), f"{name}-{get_random_string(5)}.{ext}")



# TODO нужны ли просмотры
class LibraryFile(models.Model):
    """Модель методических материалов (документы, видео, изображения)"""

    FILE_TYPES = [
        ('document', 'Документ'),
        ('video', 'Видеоролик'),
        ('image', 'Изображение'),
    ]

    slug = models.SlugField("URL", max_length=255, unique=True, db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        verbose_name="Автор"
    )

    categories = models.ManyToManyField(Category, related_name='files')
    title = models.CharField("Название файла", max_length=255,
                             validators=[MinLengthValidator(5, message="Минимальная длина названия - 5 символов")])
    description = models.TextField("Описание файла", blank=True)
    file_type = models.CharField("Тип файла", max_length=10, choices=FILE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField("Файл", upload_to=library_file_path)

    def save(self, *args, **kwargs):
        if not self.id and not self.slug:
            base_slug = slugify(self.title)[:200]
            curr_slug = base_slug
            counter = 1
            while LibraryFile.objects.filter(slug=curr_slug).exists():
                curr_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = curr_slug

        old_file_name = None
        if self.id:
            try:
                old_file_name = LibraryFile.objects.get(pk=self.id).file.name
            except LibraryFile.DoesNotExist:
                pass
        super().save(*args, **kwargs)

        if old_file_name and old_file_name != (self.file.name if self.file else None):
            storage = self.file.storage if self.file else None
            if storage and storage.exists(old_file_name):
                storage.delete(old_file_name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            storage = self.file.storage
            if storage.exists(self.file.name):
                storage.delete(self.file.name)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Методический материал"
        verbose_name_plural = "Методические материалы"
