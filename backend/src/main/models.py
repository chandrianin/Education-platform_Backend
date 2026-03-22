from django.db import models
from rest_framework.authtoken.admin import User


class WeeklyGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.text}"


class Quote(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
