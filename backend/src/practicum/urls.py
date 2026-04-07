from django.urls import path, include
from rest_framework.routers import DefaultRouter
from practicum.views import (
    OpenCasesViewSet,
    AnswerViewSet,
    AdminAnswerViewSet,
    AdminAnswerCheckViewSet,
    ClosedCasesViewSet
)

router = DefaultRouter()

# 1) Получение списка доступных кейсов с попытками пользователя
router.register(r'open-cases', OpenCasesViewSet, basename='open-cases')

# 2) Отправка ответа пользователя на выбранный кейс
router.register(r'answer', AnswerViewSet, basename='answer')

# 5) Получение истории ответов пользователя (OK или CHECKING)
router.register(r'closed-cases', ClosedCasesViewSet, basename='close-cases')

# 3) Админ: список решений кейсов для проверки
router.register(r'admin/answers', AdminAnswerViewSet, basename='admin-answer')

# 4) Админ: проверка и обновление статуса/комментария ответа
router.register(r'admin/check', AdminAnswerCheckViewSet, basename='admin-check')


urlpatterns = [
    path('', include(router.urls)),
]
