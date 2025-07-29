from django.db import models
from django.conf import settings

class DiagnosisNote(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diagnosis_notes')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_diagnosis_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.patient.username} by {self.doctor.username} on {self.created_at.strftime('%Y-%m-%d')}"

class Treatment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='treatments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_treatments')
    treatment_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment for {self.patient.username} by {self.doctor.username} on {self.created_at.strftime('%Y-%m-%d')}"

class Medication(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    interactions = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Prescription(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_prescriptions')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending')  # e.g., Pending, Completed

    def __str__(self):
        return f"Prescription of {self.medication.name} for {self.patient.username} by {self.doctor.username}"

class DoctorAvailability(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.doctor.username} available on {self.get_day_of_week_display()} from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"

class DoctorSchedule(models.Model):
    doctor = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedule')
    work_monday = models.BooleanField(default=False)
    work_tuesday = models.BooleanField(default=False)
    work_wednesday = models.BooleanField(default=False)
    work_thursday = models.BooleanField(default=False)
    work_friday = models.BooleanField(default=False)
    work_saturday = models.BooleanField(default=False)
    work_sunday = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        days = []
        if self.work_monday:
            days.append('Mon')
        if self.work_tuesday:
            days.append('Tue')
        if self.work_wednesday:
            days.append('Wed')
        if self.work_thursday:
            days.append('Thu')
        if self.work_friday:
            days.append('Fri')
        if self.work_saturday:
            days.append('Sat')
        if self.work_sunday:
            days.append('Sun')
        days_str = ', '.join(days)
        return f"{self.doctor.username} works on {days_str} from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
