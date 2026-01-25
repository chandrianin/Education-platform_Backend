from django.urls import path
from .views import MyProfileView, RegisterView
from rest_framework.authtoken import views as auth_views

urlpatterns = [
    path('me/', MyProfileView.as_view(), name='my_profile'),
    path('login/', auth_views.obtain_auth_token, name='auth_login'),
    path('register/', RegisterView.as_view(), name='auth_register'),

]
