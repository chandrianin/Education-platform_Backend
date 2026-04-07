from collections import defaultdict

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils.timezone import now

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .models import Question, Answer
from .serializers import (
    QuestionSerializer,
    AnswerBulkSerializer,
    AnswerSerializer,
    QuestionHistorySerializer,
)


class ActiveQuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        current = now()

        start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        end = current.replace(hour=23, minute=59, second=59, microsecond=999999)

        user_answers = Answer.objects.filter(
            user=self.request.user,
            question=OuterRef("pk"),
            created_at__range=(start, end)
        ).order_by("-created_at")

        return Question.objects.filter(is_active=True).annotate(
            user_answer_id=Subquery(user_answers.values("id")[:1]),
            user_value_int=Subquery(user_answers.values("value_int")[:1]),
            user_value_text=Subquery(user_answers.values("value_text")[:1]),
            user_answer_created_at=Subquery(user_answers.values("created_at")[:1]),
        )

    @extend_schema(
        summary="Список активных вопросов",
        description="Возвращает активные вопросы с текущим ответом пользователя (за сегодня, если есть).",
        tags=["Рефлексия"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример",
                        value=[
                            {
                                "id": 1,
                                "text": "Оцените день",
                                "type": "choice",
                                "user_answer": "null"
                            },
                            {
                                "id": 2,
                                "text": "Что было важным?",
                                "type": "text",
                                "is_active": True,
                                "user_answer": {
                                    "id": 10,
                                    "value_int": None,
                                    "value_text": "Сделал задачу",
                                    "created_at": "2026-03-29T10:00:00Z"
                                }
                            }
                        ]
                    )
                ]
            )
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AnswerBulkCreateView(generics.GenericAPIView):
    serializer_class = AnswerBulkSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Создать или обновить ответы (bulk)",
        description=(
                "Принимает список ответов.\n"
                "Если ответ на вопрос за сегодня уже существует — он обновляется.\n"
                "Иначе создаётся новый."
        ),
        tags=["Рефлексия"],
        request=AnswerBulkSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AnswerSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример",
                        value=[
                            {
                                "id": 1,
                                "question_id": 1,
                                "value_int": 4,
                                "value_text": None,
                                "created_at": "2026-03-29T10:00:00Z"
                            }
                        ]
                    )
                ]
            )
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            answers = serializer.save()

        return Response(
            AnswerSerializer(answers, many=True).data,
            status=status.HTTP_200_OK
        )


class AnswerHistoryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="История ответов пользователя",
        description=(
                "Возвращает список вопросов, на которые пользователь когда-либо отвечал, "
                "и список всех ответов по каждому вопросу."
        ),
        tags=["Рефлексия"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionHistorySerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример",
                        value=[
                            {
                                "id": 1,
                                "text": "Оцените день",
                                "type": "choice",
                                "answers": [
                                    {
                                        "value_int": 3,
                                        "value_text": None,
                                        "created_at": "2026-03-28T10:00:00Z"
                                    },
                                    {
                                        "value_int": 5,
                                        "value_text": None,
                                        "created_at": "2026-03-29T10:00:00Z"
                                    }
                                ]
                            }
                        ]
                    )
                ]
            )
        },
    )
    def get(self, request):
        user = request.user

        answers = (Answer.objects.filter(user=user)
                   .select_related("question")
                   .order_by("created_at"))

        questions_map = {}
        answers_map = defaultdict(list)

        for answer in answers:
            q = answer.question
            questions_map[q.id] = q
            answers_map[q.id].append(answer)

        serializer = QuestionHistorySerializer(
            list(questions_map.values()),
            many=True,
            context={"answers_map": answers_map}
        )

        return Response(serializer.data)
