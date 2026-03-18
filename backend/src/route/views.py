from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Module, ModuleCompletion
from .serializers import ModuleSerializer, ModuleCompletionSerializer

UNAUTHORIZED_RESPONSE = OpenApiResponse(
    description="Пользователь не авторизован",
    response=OpenApiTypes.OBJECT,
    examples=[OpenApiExample(
        "Пример ответа",
        value={
            "detail": "Учетные данные не были предоставлены."
        }
    )])

FORBIDDEN_RESPONSE = OpenApiResponse(
    description="Нет прав на редактирование",
    response=OpenApiTypes.OBJECT,
    examples=[
        OpenApiExample(
            "Пример ответа",
            value={
                "detail": "У вас недостаточно прав для выполнения данного действия."
            }
        )
    ]
)
NOT_FOUND_MODULE_RESPONSE = OpenApiResponse(
    description="Файл не найден",
    response=OpenApiTypes.OBJECT,
    examples=[
        OpenApiExample(
            "Пример ответа",
            value={
                "detail": "No LibraryFile matches the given query."
            }
        )
    ]
)
NOT_FOUND_COMPLETION_RESPONSE = OpenApiResponse(
    description="Отметка выполнения не найдена",
    response=OpenApiTypes.OBJECT,
    examples=[
        OpenApiExample(
            "Пример ответа",
            value={"detail": "ModuleCompletion not found"}
        )
    ]
)


@extend_schema(
    summary="Список модулей",
    description="Возвращает список всех модулей со вложенными элементами",
    tags=["Мой маршрут"],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Успешный ответ",
            response=ModuleSerializer(many=True),
            examples=[
                OpenApiExample(
                    "Пример ответа",
                    value=[
                        {
                            "id": 1,
                            "title": "Введение",
                            "type": "theory",
                            "order": 1,
                            "items": [
                                {
                                    "id": 10,
                                    "type": "text",
                                    "text": "Описание модуля",
                                    "library_file": None,
                                    "order": 1
                                }
                            ]
                        }
                    ]
                )
            ]
        ),
        status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
    }
)
class ModuleListView(generics.ListAPIView):
    queryset = Module.objects.all().order_by('order')
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary="Получение конкретного модуля",
    description="Возвращает детальную информацию о модуле по его id",
    tags=["Мой маршрут"],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Успешный ответ",
            response=ModuleSerializer,
            examples=[
                OpenApiExample(
                    "Пример ответа",
                    value={
                        "id": 1,
                        "title": "Введение",
                        "type": "theory",
                        "order": 1,
                        "items": [
                            {
                                "id": 10,
                                "type": "file",
                                "text": None,
                                "library_file": {
                                    "slug": "primer-dokumenta",
                                    "title": "Пример документа",
                                    "file": "https://example.com/file.pdf"
                                },
                                "order": 1
                            }
                        ]
                    }
                )
            ]
        ),
        status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
        status.HTTP_404_NOT_FOUND: NOT_FOUND_MODULE_RESPONSE
    }
)
class ModuleDetailView(generics.RetrieveAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary="Список выполненных модулей",
    description="Возвращает список модулей, которые пользователь отметил как выполненные",
    tags=["Мой маршрут"],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Успешный ответ",
            response=ModuleCompletionSerializer(many=True),
            examples=[
                OpenApiExample(
                    "Пример ответа",
                    value=[
                        {
                            "module": 3,
                            "completed": True
                        }
                    ]
                )
            ]
        ),
        status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
    }
)
class UserCompletedModulesView(generics.ListAPIView):
    serializer_class = ModuleCompletionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ModuleCompletion.objects.filter(user=self.request.user, completed=True)


class ToggleModuleCompletionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Отметить модуль как выполненный",
        description="Добавляет отметку о выполнении модуля",
        tags=["Мой маршрут"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Модуль отмечен как выполненный",
                response=ModuleCompletionSerializer,
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "module": 3,
                            "completed": True
                        }
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_MODULE_RESPONSE
        }
    )
    def post(self, request, module_id):
        user = request.user
        module = get_object_or_404(Module, pk=module_id)
        obj, created = ModuleCompletion.objects.get_or_create(user=user, module=module)
        obj.completed = True
        obj.save()
        serializer = ModuleCompletionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Снять отметку выполнения модуля",
        description="Отмечает модуль как невыполненный",
        tags=["Мой маршрут"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Модуль отмечен как невыполненный",
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "detail": "Module uncompleted"
                        }
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_COMPLETION_RESPONSE
        }
    )
    def delete(self, request, module_id):
        user = request.user
        module = get_object_or_404(Module, pk=module_id)
        obj = ModuleCompletion.objects.filter(user=user, module=module).first()
        if obj:
            obj.completed = False
            obj.save()
            return Response({"detail": "Module uncompleted"}, status=status.HTTP_200_OK)
        return Response({"detail": "ModuleCompletion not found"}, status=status.HTTP_404_NOT_FOUND)
