from django.urls import path
from .views import (
    ModuleListView,
    ModuleDetailView,
    UserCompletedModulesView,
    ToggleModuleCompletionView
)

urlpatterns = [
    path('modules/', ModuleListView.as_view(), name='module-list'),
    path('modules/<int:pk>/', ModuleDetailView.as_view(), name='module-detail'),
    path('modules/completed/', UserCompletedModulesView.as_view(), name='user-completed-modules'),
    path('modules/<int:module_id>/completion/', ToggleModuleCompletionView.as_view(), name='toggle-module-completion'),
]
