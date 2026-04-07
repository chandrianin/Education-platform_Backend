from django.db.models import Q, Prefetch, OuterRef, Subquery
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from practicum.models import Answer, Case
from practicum.serializers import CaseWithAnswersSerializer, AnswerCreateSerializer, AnswerReadSerializer, \
    AnswerCheckSerializer


class OpenCasesViewSet(ReadOnlyModelViewSet):
    serializer_class = CaseWithAnswersSerializer

    def get_queryset(self):
        user = self.request.user

        last_answer_subquery = Answer.objects.filter(
            case=OuterRef('pk'),
            user=user
        ).order_by('-created_at')

        last_status = Subquery(last_answer_subquery.values('status')[:1])

        return (
            Case.objects
            .filter(is_active=True)
            .annotate(last_user_status=last_status)
            .filter(
                Q(last_user_status=Answer.StatusType.FAIL) |  # последняя попытка не принята
                Q(last_user_status__isnull=True)  # попыток нет
            )
            .distinct()
            .prefetch_related(
                Prefetch("answer_set",
                         queryset=Answer.objects.filter(user=user).order_by("-created_at"),
                         to_attr="user_answers"
                         )
            ))

    @extend_schema(
        summary="Открытые кейсы",
        description=(
                "Возвращает список доступных к ответу кейсов:\n"
                "- пользователь ещё не отвечал\n"
                "- или последняя попытка имеет статус FAIL\n\n"
                "Включает все ответы пользователя по каждому кейсу"
        ),
        tags=["Практикум"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=CaseWithAnswersSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример",
                        value=[
                            {
                                "id": 1,
                                "name": "Кейс по архитектуре",
                                "description": "Опишите архитектуру сервиса",
                                "answers": [
                                    {
                                        "id": 10,
                                        "text": "Микросервисная архитектура...",
                                        "status": "fail",
                                        "comment": "Недостаточно деталей",
                                        "attempt": 1,
                                        "created_at": "2026-04-01T10:00:00Z"
                                    }
                                ]
                            }
                        ]
                    )
                ]
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ClosedCasesViewSet(ReadOnlyModelViewSet):
    serializer_class = CaseWithAnswersSerializer

    def get_queryset(self):
        user = self.request.user

        last_answer_subquery = Answer.objects.filter(
            case=OuterRef('pk'),
            user=user
        ).order_by('-created_at')

        last_status = Subquery(last_answer_subquery.values('status')[:1])

        return (
            Case.objects
            .filter(is_active=True)
            .annotate(last_user_status=last_status)
            .filter(
                Q(last_user_status=Answer.StatusType.OK) |  # последняя попытка принята
                Q(last_user_status=Answer.StatusType.CHECKING)  # последняя попытка проверяется
            )
            .distinct()
            .prefetch_related(
                Prefetch("answer_set",
                         queryset=Answer.objects.filter(user=user).order_by("-created_at"),
                         to_attr="user_answers"
                         )
            ))

    @extend_schema(
        summary="Закрытые кейсы",
        description=(
                "Возвращает кейсы, которые недоступны к ответу:\n"
                "- уже приняты (OK)\n"
                "- или находятся на проверке (CHECKING)\n\n"
                "Включает все ответы пользователя."
        ),
        tags=["Практикум"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=CaseWithAnswersSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример",
                        value=[
                            {
                                "id": 2,
                                "name": "Алгоритмы",
                                "description": "Оптимизация поиска",
                                "answers": [
                                    {
                                        "id": 22,
                                        "text": "Использовал бинарный поиск...",
                                        "status": "ok",
                                        "comment": "Отлично",
                                        "attempt": 2,
                                        "created_at": "2026-04-02T12:00:00Z"
                                    }
                                ]
                            }
                        ]
                    )
                ]
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AnswerViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = AnswerCreateSerializer

    def get_queryset(self):
        return Answer.objects.filter(user=self.request.user).select_related("case")

    @extend_schema(
        summary="Создать ответ на кейс",
        description=(
                "Создаёт новую попытку ответа на кейс\n\n"
                "Ограничения:\n"
                "- кейс должен быть активен\n"
                "- предыдущая попытка не должна быть CHECKING или OK\n"
                "- при FAIL создаётся новая попытка\n"
        ),
        tags=["Практикум"],
        request=AnswerCreateSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=AnswerReadSerializer,
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={
                            "id": 30,
                            "text": "Решение через кэширование...",
                            "status": "check",
                            "comment": None,
                            "attempt": 3,
                            "created_at": "2026-04-07T10:00:00Z"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Ошибка валидации",
                examples=[
                    OpenApiExample(
                        "Кейс уже принят",
                        value={"non_field_errors": ["Кейс уже принят"]}
                    ),
                    OpenApiExample(
                        "Ответ на проверке",
                        value={"non_field_errors": ["Ответ уже на проверке"]}
                    ),
                    OpenApiExample(
                        "Пустой текст",
                        value={"text": ["Пустой ответ"]}
                    )
                ]
            )
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class AdminAnswerViewSet(ReadOnlyModelViewSet):
    serializer_class = AnswerReadSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Answer.objects.filter(
            status=Answer.StatusType.CHECKING
        ).select_related("user", "case")


class AdminAnswerCheckViewSet(UpdateModelMixin, GenericViewSet):
    serializer_class = AnswerCheckSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['put']

    def perform_update(self, serializer):
        serializer.save(checked_by=self.request.user)

    def get_queryset(self):
        return Answer.objects.filter(
            status=Answer.StatusType.CHECKING
        ).select_related("user", "case")
