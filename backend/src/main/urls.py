from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RandomQuoteView, WeeklyGoalViewSet

router = DefaultRouter()
router.register(r"", WeeklyGoalViewSet, basename="weekly-goals")

urlpatterns = [
    path("", include(router.urls)),
    path("random-quote/", RandomQuoteView.as_view(), name="random-quote"),
]
