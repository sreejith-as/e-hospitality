# doctors/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import date
from accounts.utils import role_required
from accounts.models import CustomUser
from patients.models import Appointment, MedicalHistory
from .models import DiagnosisNote, Treatment, Medication, Prescription, DoctorAvailability
from .forms import DoctorAvailabilityForm, DoctorProfileUpdateForm
from admins.models import DoctorAllocation, Department


# -----------------------------
# Doctor Dashboard
# -----------------------------
@login_required
@role_required('doctor')
def doctor_dashboard(request):
    today = timezone.now().date()
    doctor = request.user

    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    try:
        availability = DoctorAvailability.objects.filter(doctor=doctor)
    except DoctorAvailability.DoesNotExist:
        availability = None

    # Appointments
    appointments = Appointment.objects.filter(doctor=doctor).order_by('schedule__date', 'schedule__start_time')
    todays_appointments = Appointment.objects.filter(doctor=doctor, schedule__date=today).order_by('schedule__start_time')
    upcoming_appointments = Appointment.objects.filter(doctor=doctor, schedule__date__gt=today).order_by('schedule__date', 'schedule__start_time')
    
    todays_count = todays_appointments.count()
    upcoming_count = upcoming_appointments.count()
    appointments_count = appointments.count()

    # Patients
    patient_ids = appointments.values_list('patient_id', flat=True).distinct()
    patients = CustomUser.objects.filter(id__in=patient_ids)

    context = {
        'appointments': appointments,
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'todays_count': todays_count,
        'upcoming_count': upcoming_count,
        'appointments_count': appointments_count,
        'patients': patients,
        'doctor': doctor,
        'doctor_allocation': doctor_allocation,
        'availability': availability,
    }
    return render(request, 'doctors/doctor_dashboard.html', context)


# -----------------------------
# Today's Appointments
# -----------------------------
@login_required
@role_required('doctor')
def todays_appointments(request):
    doctor = request.user
    today = date.today()
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset
    appointments = Appointment.objects.filter(
        doctor=doctor,
        schedule__date=today
    ).order_by('schedule__start_time')
    
    # Apply search filters
    if search_query:
        appointments = appointments.filter(
            patient__first_name__icontains=search_query
        ) | appointments.filter(
            patient__last_name__icontains=search_query
        )
    
    context = {
        'appointments': appointments,
        'search_query': search_query,
    }
    return render(request, 'doctors/todays_appointments.html', context)


# -----------------------------
# Upcoming Appointments
# -----------------------------
@login_required
@role_required('doctor')
def upcoming_appointments(request):
    doctor = request.user
    today = date.today()
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset
    appointments = Appointment.objects.filter(
        doctor=doctor,
        schedule__date__gt=today
    ).order_by('schedule__date', 'schedule__start_time')
    
    # Apply search filters
    if search_query:
        appointments = appointments.filter(
            patient__first_name__icontains=search_query
        ) | appointments.filter(
            patient__last_name__icontains=search_query
        ) | appointments.filter(
            schedule__date__icontains=search_query
        )
    
    context = {
        'appointments': appointments,
        'search_query': search_query,
    }
    return render(request, 'doctors/upcoming_appointments.html', context)


# -----------------------------
# Manage Availability (Replaces DoctorSchedule)
# -----------------------------
@login_required
@role_required('doctor')
def doctor_schedule_manage(request):
    doctor = request.user
    availabilities = DoctorAvailability.objects.filter(doctor=doctor)

    if request.method == 'POST':
        # Handle form submission (you may want to use a formset)
        # For now, we'll assume a multi-form or manual handling
        pass  # Implement formset logic if needed
    else:
        # Prepare initial data for form (or formset)
        pass

    return render(request, 'doctors/doctor_schedule_form.html', {'availabilities': availabilities})


# -----------------------------
# Patient List
# -----------------------------
@login_required
@role_required('doctor')
def patient_list(request):
    doctor = request.user
    patient_ids = Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True).distinct()
    patients = CustomUser.objects.filter(id__in=patient_ids)
    return render(request, 'doctors/patient_list.html', {'patients': patients})


# -----------------------------
# Patient Detail
# -----------------------------
@login_required
@role_required('doctor')
def patient_detail(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    diagnosis_notes = DiagnosisNote.objects.filter(patient=patient)
    treatments = Treatment.objects.filter(patient=patient)
    medical_history = MedicalHistory.objects.filter(patient=patient)
    prescriptions = Prescription.objects.filter(patient=patient)
    appointments = Appointment.objects.filter(patient=patient).order_by('-schedule__date')

    # Calculate age if date_of_birth is available
    age = None
    if patient.date_of_birth:
        today = date.today()
        age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))

    context = {
        'patient': patient,
        'diagnosis_notes': diagnosis_notes,
        'treatments': treatments,
        'medical_history': medical_history,
        'prescriptions': prescriptions,
        'appointments': appointments,
        'age': age,
    }
    return render(request, 'doctors/patient_detail.html', context)


# -----------------------------
# Add Diagnosis Note
# -----------------------------
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


# -----------------------------
# Add Treatment
# -----------------------------
@login_required
@role_required('doctor')
def add_treatment(request, patient_id):
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


# -----------------------------
# Add Prescription
# -----------------------------
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
    return render(request, 'doctors/add_prescription.html', {
        'patient': patient,
        'medications': medications,
    })


# -----------------------------
# Medication List
# -----------------------------
@login_required
@role_required('doctor')
def medication_list(request):
    medications = Medication.objects.all()
    return render(request, 'doctors/medication_list.html', {'medications': medications})


# -----------------------------
# Appointment Schedule
# -----------------------------
@login_required
@role_required('doctor')
def appointment_schedule(request):
    doctor = request.user
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset
    appointments = Appointment.objects.filter(doctor=doctor).order_by('schedule__date', 'schedule__start_time')
    
    # Apply search filters
    if search_query:
        appointments = appointments.filter(
            patient__first_name__icontains=search_query
        ) | appointments.filter(
            patient__last_name__icontains=search_query
        ) | appointments.filter(
            schedule__date__icontains=search_query
        )
    
    context = {
        'appointments': appointments,
        'search_query': search_query,
    }
    return render(request, 'doctors/appointment_schedule.html', context)


# -----------------------------
# Doctor Profile
# -----------------------------
@login_required
@role_required('doctor')
def profile(request):
    doctor = request.user
    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    try:
        availability = DoctorAvailability.objects.filter(doctor=doctor)
    except DoctorAvailability.DoesNotExist:
        availability = None

    context = {
        'doctor': doctor,
        'doctor_allocation': doctor_allocation,
        'availability': availability,
    }
    return render(request, 'doctors/profile.html', context)


# -----------------------------
# Update Doctor Profile
# -----------------------------
@login_required
@role_required('doctor')
def profile_update(request):
    from .forms import DoctorProfileUpdateForm, DoctorAvailabilitySimpleForm

    doctor = request.user
    try:
        doctor_allocation = DoctorAllocation.objects.get(doctor=doctor)
    except DoctorAllocation.DoesNotExist:
        doctor_allocation = None

    if request.method == 'POST':
        form = DoctorProfileUpdateForm(request.POST)
        availability_form = DoctorAvailabilitySimpleForm(request.POST)
        if form.is_valid() and availability_form.is_valid():
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

            # Update DoctorAvailability records
            working_days = availability_form.cleaned_data['working_days']
            start_time = availability_form.cleaned_data['start_time']
            end_time = availability_form.cleaned_data['end_time']

            # Delete existing availability records not in working_days
            DoctorAvailability.objects.filter(doctor=doctor).exclude(day_of_week__in=working_days).delete()

            # Create or update availability for selected days
            for day in working_days:
                obj, created = DoctorAvailability.objects.update_or_create(
                    doctor=doctor,
                    day_of_week=day,
                    defaults={'start_time': start_time, 'end_time': end_time}
                )

            messages.success(request, 'Profile and availability updated successfully.')
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

        # Prepare initial data for availability form
        existing_days = DoctorAvailability.objects.filter(doctor=doctor).values_list('day_of_week', flat=True)
        if existing_days:
            first_availability = DoctorAvailability.objects.filter(doctor=doctor).first()
            initial_availability = {
                'working_days': list(existing_days),
                'start_time': first_availability.start_time,
                'end_time': first_availability.end_time,
            }
        else:
            initial_availability = {}

        availability_form = DoctorAvailabilitySimpleForm(initial=initial_availability)

    context = {
        'form': form,
        'availability_form': availability_form,
        'doctor': doctor,
    }
    return render(request, 'doctors/profile_update.html', context)

@login_required
@role_required('doctor')
def appointment_details(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    # Get diagnosis notes and prescriptions for this appointment
    diagnosis_notes = DiagnosisNote.objects.filter(patient=appointment.patient, doctor=request.user)
    prescriptions = Prescription.objects.filter(patient=appointment.patient, doctor=request.user)
    
    context = {
        'appointment': appointment,
        'diagnosis_notes': diagnosis_notes,
        'prescriptions': prescriptions,
    }
    return render(request, 'doctors/appointment_details_readonly.html', context)
 
@login_required
@role_required('doctor')
def appointment_details_update(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    # Check if appointment is scheduled for today
    today = date.today()
    appointment_date = appointment.schedule.date
    
    if appointment_date != today:
        messages.error(request, 'You can only add diagnosis and prescription for appointments scheduled for today.')
        return redirect('doctors:appointment_details', appointment_id=appointment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_diagnosis_and_prescription':
            diagnosis_note = request.POST.get('diagnosis_note')
            medicine_name = request.POST.get('medicine_name')
            dosage = request.POST.get('dosage')
            instructions = request.POST.get('instructions')
            
            # Both diagnosis and prescription are required
            if diagnosis_note and medicine_name and dosage:
                # Create diagnosis note
                diagnosis = DiagnosisNote.objects.create(
                    patient=appointment.patient,
                    doctor=request.user,
                    note=diagnosis_note
                )
                
                # Create prescription
                medication, created = Medication.objects.get_or_create(name=medicine_name)
                prescription = Prescription.objects.create(
                    patient=appointment.patient,
                    doctor=request.user,
                    medication=medication,
                    dosage=dosage,
                    instructions=instructions or ''
                )
                
                # Mark appointment as completed
                appointment.status = 'completed'
                appointment.save()
                
                messages.success(request, 'Diagnosis and prescription added successfully. Appointment marked as completed.')
                # Redirect to the updated appointment details page
                return redirect('doctors:appointment_updated', appointment_id=appointment_id)
            else:
                messages.error(request, 'Both diagnosis note and prescription details are required.')
         
    return render(request, 'doctors/appointment_details.html', {'appointment': appointment})

@login_required
@role_required('doctor')
def appointment_updated(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    # Get the latest diagnosis note and prescription for this appointment
    diagnosis_note = DiagnosisNote.objects.filter(
        patient=appointment.patient, 
        doctor=request.user
    ).order_by('-created_at').first()
    
    prescription = Prescription.objects.filter(
        patient=appointment.patient, 
        doctor=request.user
    ).order_by('-created_at').first()
    
    context = {
        'appointment': appointment,
        'diagnosis_note': diagnosis_note,
        'prescription': prescription,
    }
    return render(request, 'doctors/appointment_updated.html', context)
