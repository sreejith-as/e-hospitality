from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from accounts.utils import role_required
from accounts.models import CustomUser 
from .models import DiagnosisNote, Treatment, Medication, Prescription, DoctorAvailability
from .forms import DoctorAvailabilityForm, DoctorProfileUpdateForm
from admins.models import DoctorAllocation, Department
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from .models import  Medication, Prescription
from patients.models import Appointment, Billing, MedicalVisit
from django.db.models import Q, Case, When, Value, IntegerField
import logging

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
    # Get today's date (timezone-aware safe)
    today = timezone.localdate()

    # Fetch all today's appointments
    appointments_list = Appointment.objects.filter(
        doctor=request.user,
        schedule__date=today
    ).select_related('patient', 'schedule')

    # Define doctor's working hours end (e.g., 6:00 PM) in timezone-aware form
    doctor_end_time = timezone.make_aware(
        timezone.datetime.combine(today, time(18, 0)),
        timezone.get_current_timezone()
    )

    now = timezone.now()

    # Auto-cancel no-shows
    for appt in appointments_list:
        if appt.status == 'booked':
            has_prescription = Prescription.objects.filter(appointment=appt).exists()
            is_after_shift = now > doctor_end_time
            # Compare full datetimes instead of time-only to avoid naive/aware mix
            appointment_start_dt = timezone.make_aware(
                timezone.datetime.combine(today, appt.schedule.start_time),
                timezone.get_current_timezone()
            )
            is_time_passed = now > appointment_start_dt

            if is_after_shift and is_time_passed and not has_prescription:
                appt.status = 'cancelled'
                appt.save()

    # ✅ Sort in Python (safe after auto-cancel)
    sorted_appointments = sorted(
        appointments_list,
        key=lambda x: {'booked': 1, 'completed': 2, 'cancelled': 3}.get(x.status, 4)
    )

    # Pagination
    paginator = Paginator(sorted_appointments, 10)
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)

    all_medicines = Medication.objects.filter(is_active=True)

    return render(request, 'doctors/todays_appointments.html', {
        'appointments': appointments,
        'search_query': request.GET.get('search', ''),
        'all_medicines': all_medicines,
        'CONSULTATION_FEE': getattr(settings, 'CONSULTATION_FEE', 500),  # Default ₹500
    })

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
# Patient Detail
# -----------------------------
@login_required
@role_required('doctor')
def patient_detail(request, patient_id):
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    diagnosis_notes = DiagnosisNote.objects.filter(patient=patient)
    treatments = Treatment.objects.filter(patient=patient)
    medical_history = MedicalVisit.objects.filter(patient=patient)
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
    """
    View to display appointment details, diagnosis, and prescriptions in read-only mode.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    # ✅ Fetch notes and prescriptions for this specific appointment
    diagnosis_notes = DiagnosisNote.objects.filter(
        patient=appointment.patient,
        doctor=request.user,
        appointment=appointment
    ).order_by('-created_at')

    prescriptions = Prescription.objects.filter(
        patient=appointment.patient,
        doctor=request.user,
        appointment=appointment
    ).order_by('-created_at')

    # --- Determine if the doctor can prescribe ---
    today = date.today()
    can_prescribe = (
        appointment.status == 'booked' and
        appointment.schedule.date == today
    )

    context = {
        'appointment': appointment,
        'diagnosis_notes': diagnosis_notes,
        'prescriptions': prescriptions,
        'can_prescribe': can_prescribe,
        'today': today,
    }

    return render(request, 'doctors/appointment_details_readonly.html', context)

logger = logging.getLogger(__name__)

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
            
            if diagnosis_note:
                try:
                    # ✅ Create diagnosis note linked to the appointment
                    diagnosis = DiagnosisNote.objects.create(
                        patient=appointment.patient,
                        doctor=request.user,
                        appointment=appointment,
                        note=diagnosis_note
                    )
                    
                    # ✅ Process multiple prescriptions
                    prescription_count = 0
                    for key in request.POST.keys():
                        if key.startswith('medicine_') and key.endswith('_id'):
                            # Extract the row index from the field name
                            row_index = key.split('_')[1]
                            
                            medicine_id = request.POST.get(f'medicine_{row_index}_id')
                            dosage = request.POST.get(f'medicine_{row_index}_dosage')
                            frequency = request.POST.get(f'medicine_{row_index}_frequency')
                            duration_days = request.POST.get(f'medicine_{row_index}_duration_days')
                            instructions = request.POST.get(f'medicine_{row_index}_instructions')
                            
                            if medicine_id and dosage:
                                try:
                                    medication = Medication.objects.get(id=medicine_id)
                                    prescription = Prescription.objects.create(
                                        patient=appointment.patient,
                                        doctor=request.user,
                                        medication=medication,
                                        dosage=dosage,
                                        frequency=frequency or '',
                                        duration_days=int(duration_days) if duration_days and duration_days.isdigit() else None,
                                        instructions=instructions or '',
                                        appointment=appointment
                                    )
                                    prescription_count += 1
                                except Medication.DoesNotExist:
                                    logger.warning(f"Medication with ID {medicine_id} not found")
                                except Exception as e:
                                    logger.error(f"Error creating prescription: {e}")
                    
                    if prescription_count == 0:
                        messages.warning(request, 'Diagnosis saved, but no valid prescriptions were provided.')

                    # ✅ Create a bill automatically if it doesn't exist
                    if not Billing.objects.filter(appointment=appointment).exists():
                        # Get all prescriptions linked to this appointment
                        prescriptions = Prescription.objects.filter(appointment=appointment)
                        
                        # Sum up line totals
                        total_medicine_cost = sum(p.line_total for p in prescriptions)

                        # Get consultation fee from settings
                        consultation_fee = getattr(settings, 'CONSULTATION_FEE', 300)  # Default ₹300

                        # Total amount
                        total_amount = total_medicine_cost + consultation_fee

                        # Create the bill
                        Billing.objects.create(
                            patient=appointment.patient,
                            appointment=appointment,
                            amount=total_amount,
                            description=f"Consultation + Medicines for {appointment.patient.get_full_name()}",
                            due_date=today + timedelta(days=7),
                            status='pending',
                            is_paid=False
                        )

                        # Optional: Log for debugging
                        print(f"Billing created: ₹{total_amount} = ₹{total_medicine_cost} (meds) + ₹{consultation_fee} (consultation)")

                    # Mark appointment as completed
                    appointment.status = 'completed'
                    appointment.save()
                    
                    messages.success(request, 'Diagnosis, prescription, and billing added successfully. Appointment marked as completed.')
                    return redirect('doctors:appointment_updated', appointment_id=appointment_id)
                except Exception as e:
                    # Log the error
                    logger.error(f"Error in appointment_details_update: {e}", exc_info=True)
                    messages.error(request, 'An error occurred while saving. Please try again.')
                    # Re-render the form
                    return render(request, 'doctors/appointment_details_update.html', {'appointment': appointment})
            else:
                messages.error(request, 'Both diagnosis note and prescription details are required.')
        
    # For GET request, render the form
    return render(request, 'doctors/appointment_details_update.html', {'appointment': appointment})


@login_required
@role_required('doctor')
def search_medicine(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    medicines = Medication.objects.filter(
        name__icontains=query,
        is_active=True
    ).order_by('name')[:10]

    results = [
        {
            'id': med.id,
            'name': med.name,
            'unit': med.unit,
            'price': float(med.price),
        }
        for med in medicines
    ]
    return JsonResponse({'results': results})