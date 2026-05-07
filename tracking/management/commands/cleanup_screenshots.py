import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from tracking.models import Screenshot

class Command(BaseCommand):
    help = 'Deletes screenshots and their records older than 3 days.'

    def handle(self, *args, **options):
        three_days_ago = timezone.now() - timedelta(days=3)
        old_screenshots = Screenshot.objects.filter(created_at__lt=three_days_ago)

        self.stdout.write(f"Found {old_screenshots.count()} screenshots older than 3 days.")

        for screenshot in old_screenshots:
            # Delete image file from disk
            if screenshot.image:
                image_path = os.path.join(settings.MEDIA_ROOT, screenshot.image.name)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    self.stdout.write(self.style.SUCCESS(f"Deleted image file: {image_path}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Image file not found, skipping: {image_path}"))
            
            # Delete DB record
            screenshot.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted DB record for screenshot ID: {screenshot.id}"))

        self.stdout.write(self.style.SUCCESS('Screenshot cleanup completed.'))
