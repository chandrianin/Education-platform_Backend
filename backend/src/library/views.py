from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import permissions, viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import LibraryFile
from .serializers import LibraryFileSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Редактировать может только автор"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class LibraryFileViewSet(viewsets.ModelViewSet):
    queryset = LibraryFile.objects.all()
    serializer_class = LibraryFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['categories', 'file_type', 'author']
    ordering_fields = ['title', 'created_at']
    ordering = ['-created_at']  # по умолчанию новые сверху
    search_fields = ['title', 'description', 'author']
    lookup_field = 'slug'

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # def get_object(self):
    #     """Позволяет получать объект по ID и по Slug"""
    #     # lookup_field = self.kwargs.get('pk')
    #     # if lookup_field.isdigit():
    #     #     return super().get_object()
    #     self.lookup_field = 'slug'
    #     return super().get_object()

    @extend_schema(
        summary="Список файлов",
        tags=["Библиотека"],
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
                                "file": "https://methodical-space.ru/media/library/primer.pdf",
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
        tags=["Библиотека"],
        description="Возвращает данные полей БД о выбранном файле по его уникальному Slug",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл найден",
                response=LibraryFileSerializer,
                examples=[
                    OpenApiExample(
                        "Пример ответа",
                        value={
                            "slug": "primer-dokumenta",
                            "title": "Пример документа",
                            "description": "Описание документа",
                            "file_type": "document",
                            "file": "https://methodical-space.ru/media/library/primer.pdf",
                            "category_details": [{"id": 1, "name": "Чек-лист"}],
                            "author_name": "ivan",
                            "created_at": "2026-02-10T12:00:00Z"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
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
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создание нового файла",
        tags=["Библиотека"],
        description="Позволяет авторизованному пользователю загрузить новый файл",
        request=LibraryFileSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Успешная загрузка файла",
                response=LibraryFileSerializer,
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
                            "file": "https://methodical-space.ru/media/library/novyy.pdf",
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
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Пользователь не авторизован",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "detail": "Учетные данные не были предоставлены."
                    }
                )]), },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление файла",
        tags=["Библиотека"],
        description="Обновляет все поля существующего файла",
        request=LibraryFileSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл обновлён",
                response=LibraryFileSerializer,
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
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Пользователь не авторизован",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "detail": "Учетные данные не были предоставлены."
                    }
                )]),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
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
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
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
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление файла",
        tags=["Библиотека"],
        description="Обновляет только указанные поля методического материала",
        request=OpenApiResponse,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Файл обновлён",
                response=LibraryFileSerializer,
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
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Пользователь не авторизован",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "detail": "Учетные данные не были предоставлены."
                    }
                )]),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
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
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
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
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить файл библиотеки",
        tags=["Библиотека"],
        description="Удаляет выбранный файл",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Файл успешно удален",
                response=OpenApiTypes.NONE
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Пользователь не авторизован",
                response=OpenApiTypes.OBJECT,
                examples=[OpenApiExample(
                    "Пример ответа",
                    value={
                        "detail": "Учетные данные не были предоставлены."
                    }
                )]),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
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
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
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
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
