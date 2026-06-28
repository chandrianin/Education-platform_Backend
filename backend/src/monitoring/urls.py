from django.urls import path
from .views import CurrentIndicatorsView, IndicatorsHistoryView

urlpatterns = [
    path('indicators/current/', CurrentIndicatorsView.as_view()),
    path('indicators/history/', IndicatorsHistoryView.as_view()),
]