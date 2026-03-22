import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import permissions, viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from .models import LibraryFile, Category
from .serializers import LibraryFileSerializer, CategorySerializer

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
NOT_FOUND_RESPONSE = OpenApiResponse(
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

logger = logging.getLogger("library")


def truncate_dict(data, limit=100):
    """
    Обрезает строки в словаре до `limit` символов.
    Работает рекурсивно для вложенных словарей и списков.
    """
    if isinstance(data, dict):
        return {k: truncate_dict(v, limit) for k, v in data.items()}
    elif isinstance(data, list):
        return [truncate_dict(v, limit) for v in data]
    elif isinstance(data, str):
        return data[:limit]
    else:
        return data


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Редактировать может только автор"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


@extend_schema(
    summary="Список категорий библиотеки",
    description="Возвращает список всех категорий методических материалов",
    tags=["Библиотека"],
    responses={
        status.HTTP_200_OK: CategorySerializer(many=True)
    },
    examples=[
        OpenApiExample(
            "Пример ответа",
            value=[
                {"id": 1, "name": "Методические материалы"},
                {"id": 2, "name": "Видео"},
                {"id": 3, "name": "Изображения"}
            ],
            response_only=True
        )
    ]
)
class LibraryCategoriesView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@extend_schema(tags=["Библиотека"])
class LibraryFileViewSet(viewsets.ModelViewSet):
    queryset = LibraryFile.objects.all()
    serializer_class = LibraryFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['categories', 'file_type', 'author']
    ordering_fields = ['title', 'created_at']
    ordering = ['-created_at']  # по умолчанию новые сверху
    search_fields = ['title', 'description', 'author__profile__full_name', 'author__username']
    lookup_field = 'slug'

    def get_queryset(self):
        return super().get_queryset().select_related('author__profile')

    @extend_schema(
        summary="Список избранных файлов пользователя",
        description="Возвращает список файлов, которые пользователь отметил как избранные",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Список избранных файлов",
                response=LibraryFileSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value=[
                            {
                                "slug": "primer-dokumenta",
                                "title": "Пример документа",
                                "description": "Описание документа",
                                "file_type": "document",
                                "file": "https://methodical-space.ru/media/library/2026/02/primer.pdf",
                                "category_details": [{"id": 1, "name": "Чек-лист"}],
                                "author_name": "ivan",
                                "created_at": "2026-02-10T12:00:00Z"
                            }
                        ]
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
        },
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def favorites(self, request):
        profile = request.user.profile
        favorite_files = profile.favorites.all()
        serializer = self.get_serializer(favorite_files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Добавление файла в избранное авторизованного пользователя",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Файл добавлен в избранное",
                response=OpenApiTypes.OBJECT
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
        },
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, slug=None):
        file = self.get_object()
        profile = request.user.profile
        profile.favorites.add(file)
        return Response({"detail": "Добавлено в избранное"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление файла из избранного",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Файл удалён из избранного"
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
        },
    )
    @favorite.mapping.delete
    def unfavorite(self, request, slug=None):
        file = self.get_object()
        profile = request.user.profile
        profile.favorites.remove(file)
        return Response({"detail": "Удалено из избранного"}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(
        summary="Список файлов",
        description="Возвращает список всех файлов с возможностью фильтрации, поиска и сортировки",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Успешный ответ",
                response=LibraryFileSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value=[
                            {
                                "slug": "primer-dokumenta",
                                "title": "Пример документа",
                                "description": "Описание документа",
                                "file_type": "document",
                                "file": "https://methodical-space.ru/media/library/2026/02/primer.pdf",
                                "category_details": [{"id": 1, "name": "Чек-лист"}],
                                "author_name": "ivan",
                                "created_at": "2026-02-10T12:00:00Z"
                            }
                        ]
                    )
                ]

            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получение информации о файле по Slug",
        description="Возвращает данные полей БД о выбранном файле по его уникальному Slug",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл найден",
                response=LibraryFileSerializer(),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "slug": "primer-dokumenta",
                            "title": "Пример документа",
                            "description": "Описание документа",
                            "file_type": "document",
                            "file": "https://methodical-space.ru/media/library/2026/02/primer.pdf",
                            "category_details": [{"id": 1, "name": "Чек-лист"}],
                            "author_name": "ivan",
                            "created_at": "2026-02-10T12:00:00Z"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создание нового файла",
        description="Позволяет авторизованному пользователю загрузить новый файл",
        request=LibraryFileSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Успешная загрузка файла",
                response=LibraryFileSerializer(),
                examples=[
                    OpenApiExample(
                        "Пример запроса",
                        value={
                            "title": "Новый документ",
                            "description": "Описание нового документа",
                            "file_type": "document",
                            "file": "file.docx",
                            "categories": [1, 2]
                        }
                    ),
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "slug": "novyy-dokument",
                            "title": "Новый документ",
                            "description": "Описание нового документа",
                            "file_type": "document",
                            "file": "https://methodical-space.ru/media/library/2026/02/novyy.pdf",
                            "category_details": [{"id": 1, "name": "Чек-лист"}, {"id": 2, "name": "Тест"}],
                            "author_name": "ivan",
                            "created_at": "2026-02-10T12:10:00Z"
                        })]),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Некорректные данные",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "Без названия",
                        value={
                            "title": [
                                "Это поле не может быть пустым."
                            ]
                        }),
                    OpenApiExample(
                        "Неправильный тип файла",
                        value={
                            "file_type": [
                                "Значения нет среди допустимых вариантов."
                            ]
                        }),
                    OpenApiExample(
                        "Тип файла не соответствует ожидаемому",
                        value={
                            "file": [
                                "Загруженный файл не является корректным файлом."
                            ]
                        }),
                    OpenApiExample(
                        "Нет файла",
                        value={
                            "file": [
                                "Ни одного файла не было отправлено."
                            ]
                        })

                ]),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
        },
    )
    def create(self, request, *args, **kwargs):
        truncated_data = truncate_dict(request.data)
        logger.debug("JSON пользователя: %s", truncated_data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.debug("Ошибка сериализатора: %s", serializer.errors)

        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление файла",
        description="Обновляет все поля существующего файла",
        request=LibraryFileSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл обновлён",
                response=LibraryFileSerializer(),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "slug": "string",
                            "title": "qqwert",
                            "description": "",
                            "file_type": "document",
                            "file": "null",
                            "category_details": [],
                            "author_name": "Ananas",
                            "created_at": "2026-02-10T19:24:41.451141+02:00"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Некорректные данные",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "title": [
                            "Это поле не может быть пустым."
                        ],
                        "file_type": [
                            "Значения нет среди допустимых вариантов."
                        ]
                    }
                )]
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
            status.HTTP_403_FORBIDDEN: FORBIDDEN_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление файла",
        description="Обновляет только указанные поля методического материала",
        request=LibraryFileSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл обновлён",
                response=LibraryFileSerializer(),
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "slug": "string",
                            "title": "qqwert",
                            "description": "newDescription",
                            "file_type": "document",
                            "file": "null",
                            "category_details": [],
                            "author_name": "Ananas",
                            "created_at": "2026-02-10T19:24:41.451141+02:00"
                        }
                    ),
                    OpenApiExample(
                        "Пример запроса",
                        value={
                            "description": "newDescription"
                        }
                    )

                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Некорректные данные",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "title": [
                            "Это поле не может быть пустым."
                        ],
                        "file_type": [
                            "Значения нет среди допустимых вариантов."
                        ]
                    }
                )]
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
            status.HTTP_403_FORBIDDEN: FORBIDDEN_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить файл библиотеки",
        description="Удаляет выбранный файл",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Файл успешно удален",
                response=OpenApiTypes.NONE
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE,
            status.HTTP_403_FORBIDDEN: FORBIDDEN_RESPONSE,
            status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
