from django.contrib.auth import logout
from django.contrib.auth.models import User
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, extend_schema_view
from rest_framework import generics, status, mixins
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer, RegisterSerializer

UNAUTHORIZED_RESPONSE = OpenApiResponse(
    description="Пользователь не авторизован",
    response=OpenApiTypes.OBJECT,
    examples=[OpenApiExample(
        "Пример ответа",
        value={
            "detail": "Учетные данные не были предоставлены."
        }
    )]
)


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


@extend_schema_view(
    get=extend_schema(
        summary="Получение данных авторизованного профиля",
        tags=["Профиль"],
        responses={
            status.HTTP_200_OK: UserSerializer,
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
        }
    ),
    patch=extend_schema(
        summary="Обновление данных авторизованного профиля",
        tags=["Профиль"],
        request=UserSerializer,
        responses={
            status.HTTP_200_OK: UserSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Некорректные данные",
                response=OpenApiTypes.OBJECT
            ),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
        }
    ),
)
class MyProfileView(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request):
        return self.retrieve(request)

    def patch(self, request):
        return self.partial_update(request)


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


@extend_schema_view(
    post=extend_schema(
        summary="Выход из системы",
        tags=["Аутентификация"],
        description="Удаляет токен авторизации и закрывает сессию",
        responses={
            status.HTTP_200_OK: OpenApiResponse(description="Успешный выход"),
            status.HTTP_401_UNAUTHORIZED: UNAUTHORIZED_RESPONSE
        },
    )
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()

        logout(request)
        return Response(status=status.HTTP_200_OK)
