from django.contrib.auth import logout
from django.contrib.auth.models import User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import generics, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer, RegisterSerializer


@extend_schema(
    summary="Вход в систему",
    tags=["Аутентификация"],
    auth=[],
    request=ObtainAuthToken.serializer_class,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Авторизация успешна",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    "Пример",
                    value={"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"},
                    response_only=True
                )],

        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Данные не прошли валидацию",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    "Недостаточно данных",
                    value={
                        "username": [
                            "Обязательное поле."
                        ],
                        "password": [
                            "Обязательное поле."
                        ]
                    },
                    response_only=True
                ),
                OpenApiExample(
                    "Некорректные учетные данные",
                    value={
                        "non_field_errors": [
                            "Невозможно войти с предоставленными учетными данными."
                        ]
                    }
                )
            ]
        )
    }
)
class CustomObtainAuthToken(ObtainAuthToken):
    pass


@extend_schema(
    summary="Получение данных авторизованного профиля",
    tags=["Профиль"],
    responses={
        status.HTTP_200_OK: UserSerializer,
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Пользователь не авторизован",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    "Пример",
                    value={"detail": "Учетные данные не были предоставлены."},
                    response_only=True
                )
            ]
        )
    }
)
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


@extend_schema(
    summary="Регистрация нового пользователя",
    tags=["Аутентификация"],
    auth=[],
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            description="Учетная запись зарегистрирована",
            response=RegisterSerializer,
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Данные не прошли валидацию",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    "Пример",
                    value={
                        "username": [
                            "Это поле не может быть пустым."
                        ],
                        "password": [
                            "Это поле не может быть пустым."
                        ],
                        "email": [
                            "Это поле не может быть пустым."
                        ],
                        "full_name": [
                            "Это поле не может быть пустым."
                        ]
                    },
                    response_only=True
                )
            ]
        )
    }
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход из системы",
        tags=["Аутентификация"],
        description="Удаляет токен авторизации и закрывает сессию",
        responses={
            status.HTTP_200_OK: OpenApiResponse(description="Успешный выход"),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Пользователь не авторизован",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "Пример",
                        value={"detail": "Учетные данные не были предоставлены."},
                        response_only=True
                    )
                ]
            )},
    )
    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()

        logout(request)
        return Response(status=status.HTTP_200_OK)
