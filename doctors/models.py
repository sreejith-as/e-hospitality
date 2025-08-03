from django.db import models
from django.conf import settings


class DiagnosisNote(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diagnosis_notes'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_diagnosis_notes'
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()} on {self.created_at.strftime('%Y-%m-%d')}"


class Treatment(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='treatments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_treatments'
    )
    treatment_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()} on {self.created_at.strftime('%Y-%m-%d')}"


class Medication(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    interactions = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Prescription(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_prescriptions'
    )
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending')  # e.g., Pending, Completed

    def __str__(self):
        return f"Prescription of {self.medication.name} for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()}"


class DoctorAvailability(models.Model):
    """
    Defines recurring weekly availability for a doctor.
    Allows different hours per day.
    """
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField(help_text="Start of working hours")
    end_time = models.TimeField(help_text="End of working hours")

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time', 'end_time')
        verbose_name = "Doctor Availability"
        verbose_name_plural = "Doctor Availabilities"
        ordering = ['day_of_week']

    def __str__(self):
        display_day = self.get_day_of_week_display()
        return f"{self.doctor.get_full_name()} available on {display_day} from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"