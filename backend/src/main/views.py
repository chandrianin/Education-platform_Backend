from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
import random
from .models import WeeklyGoal, Quote
from .serilizers import WeeklyGoalSerializer


@extend_schema(
    tags=["Главная страница"]
)
class WeeklyGoalViewSet(viewsets.GenericViewSet):
    serializer_class = WeeklyGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WeeklyGoal.objects.filter(user=self.request.user)

    def get_object(self):
        return WeeklyGoal.objects.filter(
            user=self.request.user
        ).first()

    @extend_schema(
        summary="Получить текущую цель недели",
        responses={
            status.HTTP_200_OK: WeeklyGoalSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Цель не создана")
        }
    )
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        obj = self.get_object()
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(obj).data)

    @extend_schema(
        summary="Создать или редактировать цель недели",
        responses={
            status.HTTP_200_OK: WeeklyGoalSerializer,
            status.HTTP_201_CREATED: WeeklyGoalSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse()
        }
    )
    @current.mapping.post
    def create_or_update(self, request):
        obj = self.get_object()

        serializer = self.get_serializer(obj, data=request.data)

        if serializer.is_valid():
            instance = serializer.save(
                user=request.user
            )

            status_code = (
                status.HTTP_200_OK if obj else status.HTTP_201_CREATED
            )

            return Response(self.get_serializer(instance).data, status=status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Удалить текущую цель",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(description="Удалено"),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Цель не найдена")
        }
    )
    @current.mapping.delete
    def delete_current(self, request):
        obj = self.get_object()

        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RandomQuoteView(APIView):

    @extend_schema(
        tags=["Главная страница"],
        summary="Получить случайную цитату",
        description="Возвращает случайную цитату для placeholder",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=dict,
                description="Успешный ответ"
            )
        },
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={"quote": "Consistency beats intensity."},
                response_only=True
            )
        ]
    )
    def get(self, request):
        count = Quote.objects.count()
        random_index = random.randint(0, count - 1)
        quote = Quote.objects.all()[random_index]

        return Response({"quote": quote.text})
