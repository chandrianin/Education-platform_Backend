from django.urls import path
from .views import MyProfileView, RegisterView, LogoutView, CustomObtainAuthToken

# TODO добавить сброс пароля и обновление профиля
urlpatterns = [
    path('me/', MyProfileView.as_view(), name='my_profile'),
    path('login/', CustomObtainAuthToken.as_view(), name='auth_login'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
