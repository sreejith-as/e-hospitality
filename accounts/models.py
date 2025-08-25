from django.db import models
from django.contrib.auth.models import AbstractUser
import os
import uuid
from django.utils import timezone

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
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_created_at = models.DateTimeField(blank=True, null=True)
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def generate_verification_token(self):
        """Generate a unique verification token"""
        self.verification_token = str(uuid.uuid4())
        self.verification_token_created_at = timezone.now()
        self.save()
        return self.verification_token

    def generate_password_reset_token(self):
        """Generate a unique password reset token"""
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_token_created_at = timezone.now()
        self.save()
        return self.password_reset_token

    def is_verification_token_valid(self, token):
        """Check if verification token is valid (24 hours expiry)"""
        if (self.verification_token == token and 
            self.verification_token_created_at and
            (timezone.now() - self.verification_token_created_at).total_seconds() < 86400):  # 24 hours
            return True
        return False

    def is_password_reset_token_valid(self, token):
        """Check if password reset token is valid (1 hour expiry)"""
        if (self.password_reset_token == token and 
            self.password_reset_token_created_at and
            (timezone.now() - self.password_reset_token_created_at).total_seconds() < 3600):  # 1 hour
            return True
        return False
