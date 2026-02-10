from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LibraryFileViewSet

router = DefaultRouter()
router.register(r'files', LibraryFileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
]
