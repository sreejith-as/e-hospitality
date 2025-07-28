from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from accounts.models import CustomUser
from patients.models import MedicalHistory
from .models import DiagnosisNote, Treatment, Medication, Prescription
from accounts.utils import role_required

@login_required
@role_required('doctor')
def dashboard(request):
    return render(request, 'doctors/dashboard.html')

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
    # Placeholder for appointment schedule view
    return render(request, 'doctors/appointment_schedule.html')

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
