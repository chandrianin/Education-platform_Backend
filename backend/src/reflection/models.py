from django.db import models
from rest_framework.authtoken.admin import User


class Question(models.Model):
    """
        Вопрос в разделе "Рефлексия"

        Поля:
            - text (TextField): Текст вопроса
            - type (CharField): Тип вопроса, один из "choice" (оценка 1–5) или "text" (текстовый ответ)
            - is_active (BooleanField): Активен ли вопрос
            - created_at (DateTimeField): Дата и время создания вопроса
        """

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
    """
        Ответ пользователя на вопрос из раздела "Рефлексия"

        Поля:
            - user (ForeignKey): Пользователь, давший ответ
            - question (ForeignKey): Вопрос, на который дан ответ
            - value_int (IntegerField): Числовой ответ (1–5 для choice), nullable для текстовых вопросов
            - value_text (TextField): Текстовый ответ, nullable для choice вопросов
            - created_at (DateTimeField): Дата и время создания ответа

        Индексы:
            - По пользователю и дате создания (для выборки истории)
            - По пользователю и вопросу (для быстрого поиска существующих ответов)

        Примечания:
            - Ответы на один вопрос ежедневно создаются новые
            - Поля value_int и value_text взаимно исключающие в зависимости от типа вопроса
        """
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
