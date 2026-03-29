from django.urls import path
from .views import (
    ActiveQuestionListView, AnswerBulkCreateView, AnswerHistoryView,
)

urlpatterns = [
    path("questions/", ActiveQuestionListView.as_view(), name="active-questions"),
    path("answer/", AnswerBulkCreateView.as_view(), name="create-answer"),
    path("answers-history/", AnswerHistoryView.as_view(), name="user-answers"),
]
