from django.db import models
from django.conf import settings
from datetime import timedelta

class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Session(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    active_time = models.DurationField(default=timedelta(0))
    idle_time = models.DurationField(default=timedelta(0))
    last_ping_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Session {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class Screenshot(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='screenshots/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Screenshot for Session {self.session.id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    

class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name    
    

class Team(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='teams'
    )

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name