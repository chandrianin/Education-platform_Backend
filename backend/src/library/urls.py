from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LibraryFileViewSet, LibraryCategoriesView

router = DefaultRouter()
router.register(r'files', LibraryFileViewSet, basename='file')

urlpatterns = [
    path('files/categories/', LibraryCategoriesView.as_view()),
    path('', include(router.urls)),
]
