from django.db import models
from rest_framework.authtoken.admin import User


class Question(models.Model):
    class QuestionType(models.TextChoices):
        CHOICE = "choice", "Choice (1-5)"
        TEXT = "text", "Text"

    text = models.TextField()
    type = models.CharField(max_length=10, choices=QuestionType.choices)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reflection_answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    value_int = models.IntegerField(null=True, blank=True)
    value_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "question"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.question_id}"
