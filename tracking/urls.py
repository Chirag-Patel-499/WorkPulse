from django.urls import path
from .views import (
    LoginView, StartSessionView, StopSessionView,
    ActivityPingView, UploadScreenshotView, DashboardView,
    TaskView, AdminReportView, AdminTaskCreateView
)

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('start-session', StartSessionView.as_view(), name='start_session'),
    path('stop-session', StopSessionView.as_view(), name='stop_session'),
    path('activity-ping', ActivityPingView.as_view(), name='activity_ping'),
    path('upload-screenshot', UploadScreenshotView.as_view(), name='upload_screenshot'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('tasks', TaskView.as_view(), name='tasks'),
    path('tasks/<int:pk>', TaskView.as_view(), name='task_detail'),
    path('admin-report', AdminReportView.as_view(), name='admin_report'),
    path('admin-tasks/create', AdminTaskCreateView.as_view(), name='admin_task_create'), # New URL
]
