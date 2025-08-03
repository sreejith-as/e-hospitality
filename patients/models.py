from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeSlot(models.Model):
    """
    Represents a specific time slot on a given date for a doctor.
    Used for appointment booking.
    """
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='time_slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.date} {self.start_time}–{self.end_time}"


class Appointment(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'}
    )
    schedule = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    symptoms = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Appointment: {self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {self.schedule.date} at {self.schedule.start_time}"


class MedicalHistory(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    diagnosis = models.TextField()
    medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    treatments = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical History for {self.patient.get_full_name()} (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"


class Billing(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_paid = models.BooleanField(default=False)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"Billing for {self.patient.get_full_name()} - {status} - Amount: ${self.amount}"