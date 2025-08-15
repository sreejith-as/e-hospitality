from django.db import models
from django.contrib.auth.models import AbstractUser
import os

def profile_picture_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.username}_profile.{ext}"
    return os.path.join('profile_pics', filename)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female'), ('O', 'Other')), blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to=profile_picture_upload_path, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"