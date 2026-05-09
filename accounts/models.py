from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)

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


class User(AbstractUser):

    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('company_admin', 'Company Admin'),
        ('team_leader', 'Team Leader'),
        ('employee', 'Employee'),
    )

    # Existing fields
    username = models.CharField(max_length=150, unique=True)

    email = models.EmailField(blank=True, null=True)

    first_name = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # NEW FIELDS
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )

    def __str__(self):
        return self.username