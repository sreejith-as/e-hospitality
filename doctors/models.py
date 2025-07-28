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
