from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tracking.models import Session

class Command(BaseCommand):
    help = 'Ends sessions that have been inactive for a specified duration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=15,  # Default to 15 minutes
            help='Inactivity threshold in minutes after which a session is ended.',
        )

    def handle(self, *args, **options):
        threshold_minutes = options['threshold']
        inactivity_threshold = timedelta(minutes=threshold_minutes)
        now = timezone.now()

        # Find sessions that are still active (end_time is null)
        # and whose last_ping_time is older than the inactivity threshold
        inactive_sessions = Session.objects.filter(
            end_time__isnull=True,
            last_ping_time__lt=now - inactivity_threshold
        )

        ended_count = 0
        for session in inactive_sessions:
            # Set end_time to the last_ping_time plus the threshold
            # This provides a more accurate representation of when activity ceased
            session.end_time = session.last_ping_time + inactivity_threshold
            session.save()
            ended_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully ended {ended_count} inactive sessions.'
        ))