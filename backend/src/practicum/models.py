from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Case(models.Model):
    """
        Учебный кейс для раздела "Практикум"

        Поля:
            - name (str): Название кейса
            - is_active (bool): Активен ли кейс
            - description (str): Подробное описание кейса
            - created_at (datetime): Дата и время создания кейса

        Примечания:
            - Кейс доступен для ответов только, если активен
        """
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Answer(models.Model):
    """
        Ответ пользователя на кейс из раздела "Практикум"

        Поля:
            - user (FK): Пользователь, давший ответ
            - case (FK): Кейс, на который дан ответ
            - text (str): Текст ответа
            - attempt (int): Номер попытки пользователя для данного кейса
            - status (str): Статус ответа (check / ok / fail)
            - checked_by (FK | null): Администратор\, проверивший ответ
            - checked_at (datetime | null): Дата проверки
            - comment (str | null): Комментарий проверяющего
            - created_at (datetime): Дата и время создания ответа

        Статусы:
            - CHECKING ("check"): Ответ в процессе проверки
            - OK ("ok"): Ответ принят
            - FAIL ("fail"): Ответ с ошибками, пользователь может отправить новую попытку

        Индексы:
            - По пользователю и дате создания (для истории)
            - По пользователю и кейсу (для быстрого поиска последних попыток)
            - По статусу (для фильтрации открытых кейсов)

        Примечания:
            - Набор user, case, attempt должен быть уникален для предотвращения дубликатов попыток
            - Новую попытку можно создать только после нового статуса FAIL
            - CHECKING и OK блокируют создание новой попытки
        """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="practicum_answers")
    case = models.ForeignKey(Case, on_delete=models.CASCADE)

    text = models.TextField()
    attempt = models.PositiveIntegerField()  # Номер попытки ответа на выбранный кейс

    class StatusType(models.TextChoices):
        CHECKING = "check", "Answer is being verified"  # Нельзя редактировать
        OK = "ok", "Answer is accepted"  # Нельзя редактировать
        FAIL = "fail", "Errors found"  # Создается новая попытка ответа через attempt

    checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_answers"
    )
    checked_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=5, choices=StatusType.choices, default=StatusType.CHECKING)
    comment = models.CharField(max_length=750, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "case"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "case", "attempt"],
                name="unique_user_case_attempt"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.case_id}"
