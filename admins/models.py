from django.db import models
from django.conf import settings

from accounts.models import CustomUser

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('department', 'room_number')

    def __str__(self):
        return f"{self.department.name} - Room {self.room_number}"

class Resource(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class DoctorAllocation(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'doctor'})
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    allocated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'department', 'room')

    def __str__(self):
        return f"{self.doctor.username} allocated to {self.department.name} {self.room}"

class HealthArticle(models.Model):
    """
    A health education article created by an admin.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='authored_articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Order by newest first
        ordering = ['-created_at']
        verbose_name = 'Health Article'
        verbose_name_plural = 'Health Articles'

    def __str__(self):
        return self.title

