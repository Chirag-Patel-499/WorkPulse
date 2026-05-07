from rest_framework import serializers
from accounts.models import User
from .models import Task, Session, Screenshot

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'completed']

class SessionSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True) # Nested serializer for task details
    task_id = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all(), source='task', write_only=True, required=False)

    class Meta:
        model = Session
        fields = ['id', 'user', 'task', 'task_id', 'start_time', 'end_time', 'active_time', 'idle_time']
        read_only_fields = ['user']

class ScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screenshot
        fields = ['id', 'session', 'image', 'created_at']
        read_only_fields = ['session']
