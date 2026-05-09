from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render
from django.db.models import F, Sum, Count, Max
from django.utils import timezone
from datetime import timedelta

from .models import Task, Session, Screenshot
from accounts.models import User # Assuming User is in accounts.models

class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 0 # Don't show extra empty forms

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'start_time', 'end_time', 'active_time', 'idle_time')
    list_filter = ('start_time', 'user')
    search_fields = ('user__username', 'task__title')
    inlines = [ScreenshotInline]
    readonly_fields = ('active_time', 'idle_time')

@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('session', 'image', 'created_at')
    list_filter = ('created_at', 'session__user')
    search_fields = ('session__user__username',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'completed')
    list_filter = ('completed', 'user')
    search_fields = ('user__username', 'title')

# Custom Admin Site for reports
# Custom Admin Site for reports
class MyAdminSite(admin.AdminSite):
    site_header = "WorkPulse Pro Admin"
    site_title = "WorkPulse Pro Admin Portal"
    index_title = "Welcome to WorkPulse Pro Admin"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'daywise-report/',
                self.admin_view(self.daywise_report_view),
                name='daywise_report'
            ),
        ]

        return custom_urls + urls

    def index(self, request, extra_context=None):

        if extra_context is None:
            extra_context = {}

        extra_context['custom_report_link'] = {
            'name': 'Day-wise Activity Report',
            'url': reverse('myadmin:daywise_report'),
        }

        return super().index(request, extra_context)

    def daywise_report_view(self, request):

        users_data = []

        for user in User.objects.all():

            all_sessions = Session.objects.filter(
                user=user
            ).order_by('-start_time')

            daily_summaries = {}

            for session in all_sessions:

                session_date = session.start_time.date()

                if session_date not in daily_summaries:

                    daily_summaries[session_date] = {
                        'date': session_date.isoformat(),
                        'total_active_time': timedelta(0),
                        'total_idle_time': timedelta(0),
                        'sessions': []
                    }

                daily_summaries[session_date]['total_active_time'] += session.active_time

                daily_summaries[session_date]['total_idle_time'] += session.idle_time

            for date_summary in daily_summaries.values():

                date_summary['total_active_time'] = str(
                    date_summary['total_active_time']
                )

                date_summary['total_idle_time'] = str(
                    date_summary['total_idle_time']
                )

            sorted_daily_summaries = sorted(
                daily_summaries.values(),
                key=lambda x: x['date'],
                reverse=True
            )

            users_data.append({
                'id': user.id,
                'username': user.username,
                'is_staff': user.is_staff,
                'daily_summaries': sorted_daily_summaries,
                'total_tasks': Task.objects.filter(user=user).count(),
            })

        context = dict(
            self.each_context(request),
            title="Day-wise Activity Report",
            users_data=users_data,
        )

        return render(
            request,
            'admin/daywise_report.html',
            context
        )


# Instantiate the custom admin site
admin_site = MyAdminSite(name='myadmin')


# Register models with the custom admin site
admin_site.register(Task, TaskAdmin)
admin_site.register(Session, SessionAdmin)
admin_site.register(Screenshot, ScreenshotAdmin)
admin_site.register(User)
