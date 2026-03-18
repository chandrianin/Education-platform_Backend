from django.db import models
from rest_framework.authtoken.admin import User


class Module(models.Model):
    MODULE_TYPES = [
        ("theory", "Теория"),
        ("practice", "Практика"),
        ("reflection", "Рефлексия"),
    ]

    title = models.CharField(max_length=255)

    type = models.CharField(
        max_length=20,
        choices=MODULE_TYPES
    )

    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class ModuleItem(models.Model):
    ITEM_TYPES = [
        ("text", "Текст"),
        ("file", "Файл"),
    ]

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="items"
    )

    type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES
    )

    text = models.TextField(blank=True, null=True)

    library_file = models.ForeignKey(
        "library.LibraryFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.module.title} - {self.type}"


class ModuleCompletion(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE
    )

    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "module")
