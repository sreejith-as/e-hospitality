from django.db import models
from django.conf import settings
from accounts.models import CustomUser

from patients.models import Appointment


class DiagnosisNote(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='diagnosis_notes'
    )
    appointment = models.ForeignKey(
        'patients.Appointment',
        on_delete=models.CASCADE,
        null=True,
        blank=True  
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.patient.get_full_name()} on {self.created_at.strftime('%Y-%m-%d')}"


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
    safety_warnings = models.TextField(
    blank=True,
    help_text="e.g., 'Avoid alcohol', 'Do not combine with Warfarin', 'May cause drowsiness'"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Price per unit (e.g., per tablet, per ml)"
    )
    unit = models.CharField(
        max_length=50,
        default='tablet',
        help_text="Unit of sale: tablet, ml, vial, etc."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to deactivate without deleting"
    )

    def __str__(self):
        return f"{self.name} (${self.price} per {self.unit})"


class Prescription(models.Model):
    appointment = models.ForeignKey(
        'patients.Appointment',
        on_delete=models.CASCADE, 
        null=True, blank=True
    )
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
    frequency = models.CharField(max_length=100, blank=True)
    duration_days = models.PositiveIntegerField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending')
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Rx: {self.medication.name} for {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
    # Map common frequency strings to numbers
        FREQUENCY_MAP = {
            'once': 1,
            'daily': 1,
            'every day': 1,
            'twice': 2,
            'two times': 2,
            'thrice': 3,
            'three times': 3,
            'four': 4,
            'four times': 4,
            'morning and evening': 2,
            'am and pm': 2,
        }

        # Only recalculate if quantity is missing or 1
        if self.frequency and self.duration_days and (not self.quantity or self.quantity == 1):
            freq = self.frequency.lower()
            freq_num = 1  # default
            for key, value in FREQUENCY_MAP.items():
                if key in freq:
                    freq_num = value
                    break
            self.quantity = freq_num * self.duration_days

        # Recalculate line_total if medication has price
        if self.medication.price:
            self.line_total = self.medication.price * self.quantity

        super().save(*args, **kwargs)

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
    
class MedicineInventory(models.Model):
    medicine = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0, help_text="Number of units in stock")
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    received_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.quantity} units (Batch: {self.batch_number or 'N/A'})"