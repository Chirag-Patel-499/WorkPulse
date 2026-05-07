from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser # Import IsAdminUser
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.db.models import F, Sum, Count, Max # Import Sum, Count, Max
from PIL import Image
import io
import os
import random
from datetime import timedelta

from accounts.models import User
from .models import Task, Session, Screenshot
from .serializers import UserSerializer, TaskSerializer, SessionSerializer, ScreenshotSerializer

def index(request):
    return render(request, 'index.html')

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(username=username)
        # For simplicity, we're not using Django's built-in authentication system fully.
        # A real application would involve session management or token-based authentication.
        # Here, we just return the user info. The frontend will manage "login state" based on this.
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

class StartSessionView(APIView):
    # For simplicity, we'll assume the user is "logged in" if their ID is provided.
    # In a real app, this would be protected by IsAuthenticated.
    def post(self, request):
        user_id = request.data.get('user_id')
        task_id = request.data.get('task_id')

        user = get_object_or_404(User, id=user_id)
        task = get_object_or_404(Task, id=task_id, user=user) if task_id else None

        # End any existing active sessions for this user
        Session.objects.filter(user=user, end_time__isnull=True).update(end_time=timezone.now())

        session = Session.objects.create(user=user, task=task)
        return Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

class StopSessionView(APIView):
    def post(self, request):
        session_id = request.data.get('session_id')
        notes = request.data.get('notes', '') # Frontend sends notes

        session = get_object_or_404(Session, id=session_id, end_time__isnull=True)
        session.end_time = timezone.now()
        # Calculate active_time and idle_time if not already updated by activity pings
        # For now, we assume activity pings handle this. If not, a more complex calculation is needed here.
        session.save()
        return Response(SessionSerializer(session).data, status=status.HTTP_200_OK)

class ActivityPingView(APIView):
    def post(self, request):
        session_id = request.data.get('session_id')
        is_active = request.data.get('is_active', False)
        duration = request.data.get('duration', 10) # Duration in seconds since last ping

        session = get_object_or_404(Session, id=session_id, end_time__isnull=True)
        now = timezone.now()

        # Server-side enforcement: If a ping comes for a session from a previous day,
        # automatically end it and instruct the client to start a new one.
        if session.start_time.date() < now.date():
            session.end_time = now
            session.save()
            return Response(
                {'error': 'Session expired. Please start a new session.', 'session_ended': True},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Client-side responsibility: The 'is_active' flag is determined by the client.
        # For accurate tracking, the client application needs robust logic to detect
        # keyboard input, mouse movement, and application focus (e.g., VSCode active).
        # Consider implementing thresholds for idle time (e.g., 30-60 seconds of no input).
        if is_active:
            session.active_time = F('active_time') + timedelta(seconds=duration)
        else:
            session.idle_time = F('idle_time') + timedelta(seconds=duration)
        session.last_ping_time = now # Update last ping time
        session.save()
        session.refresh_from_db() # To get updated F() values
        return Response(SessionSerializer(session).data, status=status.HTTP_200_OK)

class UploadScreenshotView(APIView):
    def post(self, request):
        session_id = request.data.get('session_id')
        image_file = request.FILES.get('image')

        if not image_file:
            print("UploadScreenshotView: No image file provided.")
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = get_object_or_404(Session, id=session_id)
            print(f"UploadScreenshotView: Session {session_id} found.")
        except Exception as e:
            print(f"UploadScreenshotView: Error finding session {session_id}: {e}")
            return Response({'error': f'Session not found: {e}'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Process image
            img = Image.open(image_file)
            print(f"UploadScreenshotView: Image opened. Original size: {img.size}")
            
            # Resize image to max width 1280px, maintaining aspect ratio
            max_width = 1280
            if img.width > max_width:
                width_percent = (max_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(width_percent)))
                img = img.resize((max_width, h_size), Image.LANCZOS) # Use LANCZOS for high quality downsampling
                print(f"UploadScreenshotView: Image resized to {img.size}")

            # Convert to JPEG (quality ~60%)
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="jpeg", quality=60)
            output_buffer.seek(0)
            print("UploadScreenshotView: Image converted to JPEG and buffered.")

            # Save the processed image
            screenshot = Screenshot(session=session)
            filename = f'screenshot_{session.id}_{timezone.now().timestamp()}.jpeg'
            screenshot.image.save(filename, output_buffer)
            screenshot.save()
            print(f"UploadScreenshotView: Screenshot saved to DB and filesystem: {filename}")

            return Response(ScreenshotSerializer(screenshot).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"UploadScreenshotView: Error during image processing or saving: {e}")
            return Response({'error': f'Error processing or saving image: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)

        # Get current active session
        current_session = Session.objects.filter(user=user, end_time__isnull=True).order_by('-start_time').first()
        current_session_data = SessionSerializer(current_session).data if current_session else None

        # Get all tasks for the user
        tasks = Task.objects.filter(user=user)
        tasks_data = TaskSerializer(tasks, many=True).data

        # Get last screenshot for the current session
        last_screenshot = None
        if current_session:
            last_screenshot = Screenshot.objects.filter(session=current_session).order_by('-created_at').first()
        last_screenshot_data = ScreenshotSerializer(last_screenshot).data if last_screenshot else None

        # --- Day-wise session data ---
        # Fetch all sessions for the user, ordered by start_time descending
        all_sessions = Session.objects.filter(user=user).order_by('-start_time')

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
            daily_summaries[session_date]['sessions'].append(SessionSerializer(session).data)
        
        # Convert timedelta objects to string for JSON serialization
        for date_summary in daily_summaries.values():
            date_summary['total_active_time'] = str(date_summary['total_active_time'])
            date_summary['total_idle_time'] = str(date_summary['total_idle_time'])

        # Sort daily summaries by date descending
        sorted_daily_summaries = sorted(daily_summaries.values(), key=lambda x: x['date'], reverse=True)

        return Response({
            'user': UserSerializer(user).data,
            'current_session': current_session_data,
            'tasks': tasks_data,
            'last_screenshot': last_screenshot_data,
            'daily_summaries': sorted_daily_summaries, # New field
        }, status=status.HTTP_200_OK)

class TaskView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        title = request.data.get('title')

        user = get_object_or_404(User, id=user_id)
        task = Task.objects.create(user=user, title=title)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        completed = request.data.get('completed')
        if completed is not None:
            task.completed = completed
            task.save()
            return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AdminReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users_data = []
        for user in User.objects.all():
            # Get all sessions for the user, ordered by start_time descending
            all_sessions = Session.objects.filter(user=user).order_by('-start_time')

            daily_summaries = {}
            for session in all_sessions:
                session_date = session.start_time.date()
                if session_date not in daily_summaries:
                    daily_summaries[session_date] = {
                        'date': session_date.isoformat(),
                        'total_active_time': timedelta(0),
                        'total_idle_time': timedelta(0),
                        'sessions': [] # Optionally include individual sessions
                    }
                
                daily_summaries[session_date]['total_active_time'] += session.active_time
                daily_summaries[session_date]['total_idle_time'] += session.idle_time
                # Optionally, append serialized session data if detailed session info is needed per day
                # daily_summaries[session_date]['sessions'].append(SessionSerializer(session).data)
            
            # Convert timedelta objects to string for JSON serialization
            for date_summary in daily_summaries.values():
                date_summary['total_active_time'] = str(date_summary['total_active_time'])
                date_summary['total_idle_time'] = str(date_summary['total_idle_time'])

            # Sort daily summaries by date descending
            sorted_daily_summaries = sorted(daily_summaries.values(), key=lambda x: x['date'], reverse=True)

            users_data.append({
                'id': user.id,
                'username': user.username,
                'is_staff': user.is_staff,
                'daily_summaries': sorted_daily_summaries, # New field for day-wise data
                'total_tasks': Task.objects.filter(user=user).count(), # Keep total tasks
            })
        return Response(users_data, status=status.HTTP_200_OK)

class AdminTaskCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        completed = request.data.get('completed', False) # Admin can set initial completion status

        if not user_id or not title:
            return Response({'error': 'User ID and title are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)
        task = Task.objects.create(user=user, title=title, completed=completed)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
