from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Make username unique and required
    username = models.CharField(max_length=150, unique=True)

    # Add any other fields if needed, but for now, keep it minimal
    # For simplicity, email and first_name, last_name are not required for login
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return self.username