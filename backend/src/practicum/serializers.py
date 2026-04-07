from django.db.models import Max, Q
from rest_framework import serializers

from practicum.models import Answer, Case


class AnswerReadSerializer(serializers.ModelSerializer):
    """
        Сериализатор для отображения ответа пользователя
    """

    class Meta:
        model = Answer
        fields = [
            "id",
            "text",
            "status",
            "comment",
            "attempt",
            "created_at",
        ]


class CaseWithAnswersSerializer(serializers.ModelSerializer):
    """
        Сериализатор кейса с ответами текущего пользователя
    """

    answers = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ["id", "name", "description", "answers"]

    def get_answers(self, obj):
        qs = getattr(obj, "user_answers", [])
        return AnswerReadSerializer(qs, many=True).data


class AnswerCreateSerializer(serializers.ModelSerializer):
    """
        Сериализатор для создания нового ответа на кейс

        Проверки:
            - text не пустой.
            - кейс активен и доступен для пользователя.
            - предыдущая попытка не CHECKING или OK.
    """

    class Meta:
        model = Answer
        fields = ["case", "text"]

    def validate_text(self, text):
        if not text.strip():
            raise serializers.ValidationError("Пустой ответ")
        return text

    def validate_case(self, case):
        user = self.context["request"].user

        base_qs = Case.objects.filter(id=case.id, is_active=True)

        allowed = base_qs.filter(
            Q(answer__isnull=True) |
            Q(answer__user=user, answer__status=Answer.StatusType.FAIL)
        ).exists()

        if not allowed:
            raise serializers.ValidationError("Кейс недоступен")

        return case

    def validate(self, data):
        user = self.context["request"].user
        case = data["case"]

        last = Answer.objects.filter(user=user, case=case).order_by("-created_at").first()

        if last and last.status == Answer.StatusType.CHECKING:
            raise serializers.ValidationError("Ответ уже на проверке")

        if last and last.status == Answer.StatusType.OK:
            raise serializers.ValidationError("Кейс уже принят")

        return data

    def create(self, validated_data):
        user = self.context["request"].user

        last_attempt = Answer.objects.filter(
            user=user,
            case=validated_data["case"]
        ).aggregate(Max("attempt"))["attempt__max"] or 0

        return Answer.objects.create(
            user=user,
            attempt=last_attempt + 1,
            status=Answer.StatusType.CHECKING,
            **validated_data
        )


class AnswerCheckSerializer(serializers.ModelSerializer):
    """
        Сериализатор для создания администратором проверки ответа
    """
    class Meta:
        model = Answer
        fields = ["status", "comment"]

    def validate_status(self, value):
        if value not in [Answer.StatusType.OK, Answer.StatusType.FAIL]:
            raise serializers.ValidationError("Недопустимый статус")
        return value

    def validate(self, data):
        if self.instance.status != Answer.StatusType.CHECKING:
            raise serializers.ValidationError("Ответ уже проверен")
        return data
