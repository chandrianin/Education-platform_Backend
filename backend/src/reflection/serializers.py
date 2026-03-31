from django.utils.timezone import now
from rest_framework import serializers
from .models import Question, Answer


class QuestionSerializer(serializers.ModelSerializer):
    user_answer = serializers.SerializerMethodField()

    can_answer = serializers.SerializerMethodField()

    def get_can_answer(self, obj):
        if not obj.user_answer_id:
            return True

        return obj.user_value_int is None and obj.user_value_text is None

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "type",
            "can_answer",
            "user_answer",
        ]

    def get_user_answer(self, obj):
        if not obj.user_answer_id:
            return None

        return {
            "id": obj.user_answer_id,
            "value_int": obj.user_value_int,
            "value_text": obj.user_value_text,
            "created_at": obj.user_answer_created_at,
        }


class AnswerWriteSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    value_int = serializers.IntegerField(required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        question = attrs["question"]

        if not question.is_active:
            raise serializers.ValidationError("Вопрос неактивен")

        value_int = attrs.get("value_int")
        value_text = attrs.get("value_text")

        if value_text is not None:
            value_text = value_text.strip()
            value_text = value_text or None
            attrs["value_text"] = value_text

        if value_int is None and value_text is None:
            return attrs

        if question.type == Question.QuestionType.CHOICE:
            if value_int is None:
                raise serializers.ValidationError("Требуется value_int")

            if not (1 <= value_int <= 5):
                raise serializers.ValidationError("value_int должен быть от 1 до 5")

            attrs["value_text"] = None

        elif question.type == Question.QuestionType.TEXT:
            if value_text is None:
                raise serializers.ValidationError("Требуется value_text")

            attrs["value_int"] = None

        return attrs


class AnswerBulkSerializer(serializers.Serializer):
    answers = AnswerWriteSerializer(many=True)
    value_int = serializers.IntegerField(required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def create(self, validated_data):
        user = self.context["request"].user
        today = now().date()

        result = []

        for item in validated_data["answers"]:
            question = item["question"]

            existing = Answer.objects.filter(
                user=user,
                question=question,
                created_at__date=today
            ).first()

            if existing:
                # update
                existing.value_int = item.get("value_int")
                existing.value_text = item.get("value_text")
                existing.save()
                result.append(existing)
            else:
                # create
                obj = Answer.objects.create(
                    user=user,
                    question=question,
                    value_int=item.get("value_int"),
                    value_text=item.get("value_text"),
                )
                result.append(obj)

        return result

    def validate(self, attrs):
        questions = [item["question"].id for item in attrs["answers"]]

        if len(questions) != len(set(questions)):
            raise serializers.ValidationError("Дубликаты вопросов в запросе")

        return attrs


class AnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source="question.id")

    class Meta:
        model = Answer
        fields = [
            "id",
            "question_id",
            "value_int",
            "value_text",
            "created_at",
        ]


class AnswerHistoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [
            "value_int",
            "value_text",
            "created_at",
        ]


class QuestionHistorySerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "type",
            "answers",
        ]

    def get_answers(self, obj):
        answers_map = self.context["answers_map"]
        answers = answers_map.get(obj.id, [])
        return AnswerHistoryItemSerializer(answers, many=True).data
