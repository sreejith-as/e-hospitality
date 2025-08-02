from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import date

from accounts.utils import role_required
from accounts.models import CustomUser
from patients.models import Appointment, MedicalHistory
from .models import DiagnosisNote, Treatment, Medication, Prescription, DoctorSchedule
from .forms import DoctorScheduleForm


@login_required
@role_required('doctor')
def doctor_dashboard(request):
    """Display doctor's dashboard with appointments, stats, and patients."""
    today = timezone.now().date()
    doctor = request.user

    from admins.models import DoctorAllocation
    from .models import DoctorSchedule

    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor)
    except DoctorSchedule.DoesNotExist:
        schedule = None

    # Appointments
    appointments = Appointment.objects.filter(doctor=doctor).order_by(
        'schedule__date', 'schedule__start_time'
    )
    scheduled_count = appointments.filter(status='booked').count()
    completed_today_count = appointments.filter(status='completed', schedule__date=today).count()

    # Patients who have had appointments with this doctor
    patient_ids = appointments.values_list('patient_id', flat=True).distinct()
    patients = CustomUser.objects.filter(id__in=patient_ids)

    context = {
        'appointments': appointments,
        'scheduled_count': scheduled_count,
        'completed_today_count': completed_today_count,
        'patients': patients,
        'doctor': doctor,
        'doctor_allocation': doctor_allocation,
        'schedule': schedule,
    }
    return render(request, 'doctors/doctor_dashboard.html', context)


@login_required
@role_required('doctor')
def todays_appointments(request):
    """List today's appointments only."""
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
def doctor_schedule_manage(request):
    """Manage doctor's availability schedule."""
    doctor = request.user
    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor)
    except DoctorSchedule.DoesNotExist:
        schedule = None

    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()
            messages.success(request, 'Schedule saved successfully.')
            return redirect('doctors:doctor_schedule_manage')
    else:
        form = DoctorScheduleForm(instance=schedule)

    return render(request, 'doctors/doctor_schedule_form.html', {'form': form})


@login_required
@role_required('doctor')
def patient_list(request):
    """List all patients who have had an appointment with the doctor."""
    doctor = request.user
    patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True).distinct()
    patients = CustomUser.objects.filter(id__in=patient_ids)
    return render(request, 'doctors/patient_list.html', {'patients': patients})


@login_required
@role_required('doctor')
def patient_detail(request, patient_id):
    """View detailed medical history of a specific patient."""
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
    """Add a diagnosis note for a patient."""
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
    """Add a treatment record for a patient."""
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    if request.method == 'POST':
        treatment_details = request.POST.get('treatment_details')
        if treatment_details:
            Treatment.objects.create(
                patient=patient,
                doctor=request.user,
                treatment_details=treatment_details
            )
            messages.success(request, 'Treatment added successfully.')
            return redirect('doctors:patient_detail', patient_id=patient.id)
        else:
            messages.error(request, 'Treatment details cannot be empty.')
    return render(request, 'doctors/add_treatment.html', {'patient': patient})


@login_required
@role_required('doctor')
def add_prescription(request, patient_id):
    """Prescribe medication to a patient."""
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

    return render(request, 'doctors/add_prescription.html', {
        'patient': patient,
        'medications': medications,
    })


@login_required
@role_required('doctor')
def medication_list(request):
    """List all available medications."""
    medications = Medication.objects.all()
    return render(request, 'doctors/medication_list.html', {'medications': medications})


@login_required
@role_required('doctor')
def appointment_schedule(request):
    """List all appointments for the logged-in doctor."""
    appointments = Appointment.objects.filter(doctor=request.user).order_by('schedule__date', 'schedule__start_time')
    return render(request, 'doctors/appointment_schedule.html', {'appointments': appointments})


@login_required
@role_required('doctor')
def profile(request):
    """View doctor's profile."""
    doctor = request.user
    from admins.models import DoctorAllocation
    from .models import DoctorSchedule

    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor)
    except DoctorSchedule.DoesNotExist:
        schedule = None

    context = {
        'doctor': doctor,
        'doctor_allocation': doctor_allocation,
        'schedule': schedule,
    }
    return render(request, 'doctors/profile.html', context)


from .forms import DoctorScheduleForm, DoctorProfileUpdateForm
from admins.models import DoctorAllocation, Department

@login_required
@role_required('doctor')
def profile_update(request):
    """Update doctor's profile information including department and working hours."""
    doctor = request.user

    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor)
    except DoctorSchedule.DoesNotExist:
        schedule = None

    if request.method == 'POST':
        form = DoctorProfileUpdateForm(request.POST)
        schedule_form = DoctorScheduleForm(request.POST, instance=schedule)
        if form.is_valid() and schedule_form.is_valid():
            # Update user info
            doctor.first_name = form.cleaned_data['first_name']
            doctor.last_name = form.cleaned_data['last_name']
            doctor.email = form.cleaned_data['email']
            doctor.phone_number = form.cleaned_data['phone_number']
            doctor.gender = form.cleaned_data['gender']
            doctor.save()

            # Update or create DoctorAllocation
            department = form.cleaned_data['department']
            if doctor_allocation:
                doctor_allocation.department = department
                doctor_allocation.save()
            else:
                DoctorAllocation.objects.create(doctor=doctor, department=department)

            # Update DoctorSchedule
            schedule = schedule_form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()

            messages.success(request, 'Profile updated successfully.')
            url = reverse('doctors:dashboard') + '#profile'
            return redirect(url)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {
            'first_name': doctor.first_name,
            'last_name': doctor.last_name,
            'email': doctor.email,
            'phone_number': doctor.phone_number,
            'gender': doctor.gender,
            'department': doctor_allocation.department if doctor_allocation else None,
        }
        form = DoctorProfileUpdateForm(initial=initial_data)
        schedule_form = DoctorScheduleForm(instance=schedule)

    context = {
        'form': form,
        'schedule_form': schedule_form,
        'doctor': doctor,
    }
    return render(request, 'doctors/profile_update.html', context)
