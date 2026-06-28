from datetime import date
from collections import defaultdict

from django.db import transaction
from django.db.models import ExpressionWrapper, F, FloatField, Avg
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Indicator, IndicatorValue, MonthlyEnvironmentIndex
from .serializers import (
    CurrentIndicatorSerializer,
    HistoryPeriodSerializer, IndicatorUpdateItemSerializer
)


def calculate_monthly_index(period):
    values = IndicatorValue.objects.filter(period=period)

    if not values.exists():
        return None

    annotated = values.annotate(
        pi=ExpressionWrapper(
            F('score') * F('indicator__modality_coefficient'),
            output_field=FloatField()
        )
    )

    result = annotated.aggregate(index=Avg('pi'))

    MonthlyEnvironmentIndex.objects.update_or_create(
        period=period,
        defaults={
            "index_value": result['index'] or 0
        }
    )

    return result['index']


def get_current_period():
    today = date.today()
    return date(today.year, today.month, 1)


class CurrentIndicatorsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Текущие индикаторы пользователя",
        description=(
                "Возвращает список всех активных индикаторов за текущий месяц.\n\n"
                "- Если пользователь ещё не заполнял показатель → value = null\n"
                "- comment также может быть null\n"
        ),
        tags=["Мониторинг"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=CurrentIndicatorSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value=[
                            {
                                "id": 1,
                                "name": "Комфорт среды",
                                "value": 4,
                                "comment": "Нормально"
                            },
                            {
                                "id": 2,
                                "name": "Безопасность",
                                "value": None,
                                "comment": None
                            }
                        ]
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        period = get_current_period()

        indicators = Indicator.objects.filter(is_active=True)

        values = IndicatorValue.objects.filter(
            user=user,
            period=period
        ).select_related('indicator')

        values_map = {v.indicator_id: v for v in values}

        result = []

        for indicator in indicators:
            v = values_map.get(indicator.id)

            result.append({
                "id": indicator.id,
                "name": indicator.name,
                "value": v.score if v else None,
                "comment": v.comment if v else None
            })

        serializer = CurrentIndicatorSerializer(result, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Отправка значений индикаторов",
        description=(
                "Позволяет пользователю частично или полностью обновить значения индикаторов "
                "за текущий месяц.\n\n"
                "Особенности:\n"
                "- Принимает список объектов\n"
                "- Каждый объект содержит id индикатора\n"
                "- Значение должно быть от 1 до 5\n"
                "- comment необязателен\n"
                "- Обновляет существующие записи или создаёт новые\n"
        ),
        tags=["Мониторинг"],
        request=IndicatorUpdateItemSerializer(many=True),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Успешное обновление",
                examples=[
                    OpenApiExample(
                        "Пример запроса",
                        value=[
                            {
                                "id": 1,
                                "value": 5,
                                "comment": "Отлично"
                            },
                            {
                                "id": 2,
                                "value": 3
                            }
                        ],
                        request_only=True
                    ),
                    OpenApiExample(
                        "Пример ответа",
                        value={"status": "ok"},
                        response_only=True
                    )
                ]
            )
        }
    )
    def patch(self, request):
        user = request.user
        period = get_current_period()
        print(request.data)
        if not isinstance(request.data, list):
            raise ValidationError("Expected a list of objects")

        serializer = IndicatorUpdateItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data:
            return Response(
                {"detail": "empty"},
                status=400
            )

        indicators = Indicator.objects.filter(is_active=True)
        indicators_map = {i.id: i for i in indicators}

        updated = 0
        skipped = []

        with transaction.atomic():
            for item in data:
                indicator_id = item['id']

                if indicator_id not in indicators_map:
                    skipped.append({
                        "id": indicator_id,
                        "reason": "inactive or not found"
                    })
                    continue

                IndicatorValue.objects.update_or_create(
                    user=user,
                    indicator_id=indicator_id,
                    period=period,
                    defaults={
                        "score": item['value'],
                        "comment": item.get('comment', "")
                    }
                )
                updated += 1

        if updated == 0:
            return Response(
                {
                    "status": "nothing_saved",
                    "skipped": skipped
                },
                status=400
            )

        return Response(
            {
                "status": "ok",
                "updated": updated,
                "skipped": skipped
            }
        )


class IndicatorsHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="История ответов пользователя",
        description=(
                "Возвращает историю заполненных индикаторов по периодам.\n\n"
                "Особенности:\n"
                "- Группировка по месяцам (period)\n"
                "- Включаются только заполненные значения\n"
                "- Если comment отсутствует → null\n"
        ),
        tags=["Мониторинг"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=HistoryPeriodSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value=[
                            {
                                "period": "2026-04-01",
                                "indicators": [
                                    {
                                        "id": 1,
                                        "name": "Комфорт среды",
                                        "value": 4,
                                        "comment": "Ок"
                                    }
                                ]
                            },
                            {
                                "period": "2026-03-01",
                                "indicators": [
                                    {
                                        "id": 2,
                                        "name": "Безопасность",
                                        "value": 5,
                                        "comment": None
                                    }
                                ]
                            }
                        ]
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user

        values = IndicatorValue.objects.filter(
            user=user
        ).select_related('indicator').order_by('-period')

        grouped = defaultdict(list)

        for v in values:
            grouped[v.period].append({
                "id": v.indicator.id,
                "name": v.indicator.name,
                "value": v.score,
                "comment": v.comment
            })

        result = [
            {
                "period": period,
                "indicators": indicators
            }
            for period, indicators in grouped.items()
        ]

        serializer = HistoryPeriodSerializer(result, many=True)
        return Response(serializer.data)
