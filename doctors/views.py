from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from accounts.models import CustomUser
from patients.models import MedicalHistory
from .models import DiagnosisNote, Treatment, Medication, Prescription
from patients.models import Appointment
from accounts.utils import role_required

@login_required
@role_required('doctor')
def dashboard(request):
    # Render dashboard with cards for navigation
    return render(request, 'doctors/dashboard.html')

@login_required
@role_required('doctor')
def todays_appointments(request):
    from django.utils import timezone
    from datetime import date

    doctor = request.user
    today = date.today()
    appointments = Appointment.objects.filter(
        doctor=doctor,
        schedule__date=today
    ).order_by('schedule__start_time')
    context = {
        'appointments': appointments,
    }
    return render(request, 'doctors/todays_appointments.html', context)

@login_required
@role_required('doctor')
def patient_list(request):
    doctor = request.user
    # Get patients who have consulted this doctor at least once
    patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True).distinct()
    patients = CustomUser.objects.filter(id__in=patient_ids)
    return render(request, 'doctors/patient_list.html', {'patients': patients})

@login_required
@role_required('doctor')
def profile(request):
    doctor = request.user
    return render(request, 'doctors/profile.html', {'doctor': doctor})

@login_required
@role_required('doctor')
def profile_update(request):
    doctor = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        gender = request.POST.get('gender')
        if first_name and last_name and email and phone_number and gender:
            doctor.first_name = first_name
            doctor.last_name = last_name
            doctor.email = email
            doctor.phone_number = phone_number
            doctor.gender = gender
            doctor.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('doctors:profile')
        else:
            messages.error(request, 'All fields are required.')
    return render(request, 'doctors/profile_update.html', {'doctor': doctor})

@login_required
@role_required('doctor')
def patient_list(request):
    patients = CustomUser.objects.filter(role='patient')
    return render(request, 'doctors/patient_list.html', {'patients': patients})

@login_required
@role_required('doctor')
def patient_detail(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    diagnosis_notes = DiagnosisNote.objects.filter(patient=patient)
    treatments = Treatment.objects.filter(patient=patient)
    medical_history = MedicalHistory.objects.filter(patient=patient)
    prescriptions = Prescription.objects.filter(patient=patient)
    context = {
        'patient': patient,
        'diagnosis_notes': diagnosis_notes,
        'treatments': treatments,
        'medical_history': medical_history,
        'prescriptions': prescriptions,
    }
    return render(request, 'doctors/patient_detail.html', context)

@login_required
@role_required('doctor')
def add_diagnosis_note(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    if request.method == 'POST':
        note = request.POST.get('note')
        if note:
            DiagnosisNote.objects.create(patient=patient, doctor=request.user, note=note)
            messages.success(request, 'Diagnosis note added successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
        else:
            messages.error(request, 'Note cannot be empty.')
    return render(request, 'doctors/add_diagnosis_note.html', {'patient': patient})

@login_required
@role_required('doctor')
def add_treatment(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    if request.method == 'POST':
        treatment_details = request.POST.get('treatment_details')
        if treatment_details:
            Treatment.objects.create(patient=patient, doctor=request.user, treatment_details=treatment_details)
            messages.success(request, 'Treatment added successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
        else:
            messages.error(request, 'Treatment details cannot be empty.')
    return render(request, 'doctors/add_treatment.html', {'patient': patient})

@login_required
@role_required('doctor')
def appointment_schedule(request):
    # Fetch appointments for the logged-in doctor
    appointments = Appointment.objects.filter(doctor=request.user).order_by('time')
    return render(request, 'doctors/appointment_schedule.html', {'appointments': appointments})

@login_required
@role_required('doctor')
def medication_list(request):
    medications = Medication.objects.all()
    return render(request, 'doctors/medication_list.html', {'medications': medications})

@login_required
@role_required('doctor')
def add_prescription(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    medications = Medication.objects.all()
    if request.method == 'POST':
        medication_id = request.POST.get('medication')
        dosage = request.POST.get('dosage')
        instructions = request.POST.get('instructions')
        if medication_id and dosage:
            medication = get_object_or_404(Medication, id=medication_id)
            Prescription.objects.create(
                patient=patient,
                doctor=request.user,
                medication=medication,
                dosage=dosage,
                instructions=instructions or ''
            )
            messages.success(request, 'Prescription added successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
        else:
            messages.error(request, 'Medication and dosage are required.')
    return render(request, 'doctors/add_prescription.html', {'patient': patient, 'medications': medications})
