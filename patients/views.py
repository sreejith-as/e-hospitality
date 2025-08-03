# patients/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from accounts.utils import role_required
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Billing, Appointment, MedicalHistory, TimeSlot
from doctors.models import DoctorAvailability, Prescription
from accounts.models import CustomUser
from .forms import AppointmentBookingForm
from django.db.models import Sum, Count
import json


# -----------------------------
# Patient Dashboard & Overview
# -----------------------------
@login_required
@role_required('patient')
def overview(request):
    user = request.user
    today = timezone.now().date()
    upcoming_appointments = Appointment.objects.filter(
        patient=user, schedule__date__gte=today, status='booked'
    ).select_related('doctor', 'schedule').order_by('schedule__date', 'schedule__start_time')
    medical_records_count = MedicalHistory.objects.filter(patient=user).count()
    active_prescriptions = Prescription.objects.filter(patient=user).order_by('-created_at')[:5]
    unpaid_bills = Billing.objects.filter(patient=user, is_paid=False).order_by('due_date')
    recent_activity = []  # Can be extended later
    context = {
        'upcoming_appointments': upcoming_appointments,
        'medical_records_count': medical_records_count,
        'active_prescriptions': active_prescriptions,
        'unpaid_bills': unpaid_bills,
        'recent_activity': recent_activity,
    }
    return render(request, 'patients/dashboard.html', context)


# -----------------------------
# Appointments
# -----------------------------
@login_required
@role_required('patient')
def appointments(request):
    user = request.user
    today = timezone.now().date()
    upcoming = Appointment.objects.filter(
        patient=user, schedule__date__gte=today, status='booked'
    ).select_related('doctor', 'schedule').order_by('schedule__date', 'schedule__start_time')
    past = Appointment.objects.filter(
        patient=user, schedule__date__lt=today
    ).select_related('doctor', 'schedule').order_by('-schedule__date', '-schedule__start_time')
    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past,
    }
    return render(request, 'patients/appointments.html', context)


# -----------------------------
# Medical Records
# -----------------------------
@login_required
@role_required('patient')
def medical_records(request):
    medical_history = MedicalHistory.objects.filter(
        patient=request.user
    ).order_by('-updated_at')
    return render(request, 'patients/medical_records.html', {'medical_history': medical_history})


# -----------------------------
# Prescriptions
# -----------------------------
@login_required
@role_required('patient')
def prescriptions(request):
    prescriptions = Prescription.objects.filter(
        patient=request.user
    ).order_by('-created_at')
    return render(request, 'patients/prescriptions.html', {'prescriptions': prescriptions})


# -----------------------------
# Billing & Payments
# -----------------------------
@login_required
@role_required('patient')
def billing(request):
    billings = Billing.objects.filter(patient=request.user).order_by('-due_date')
    return render(request, 'patients/billing.html', {'billings': billings})


@login_required
@role_required('patient')
def pay_bill(request, billing_id):
    billing = get_object_or_404(Billing, id=billing_id, patient=request.user)
    if request.method == 'POST':
        billing.is_paid = True
        billing.save()
        messages.success(request, 'Payment successful.')
        return redirect('patients:billing')
    return render(request, 'patients/pay_bill.html', {'billing': billing})


# -----------------------------
# Health Education
# -----------------------------
@login_required
@role_required('patient')
def health_education(request):
    return render(request, 'patients/health_education.html')


# -----------------------------
# AJAX: Get Doctors by Department
# -----------------------------
@require_GET
@login_required
@role_required('patient')
def get_doctors_by_department(request):
    department_id = request.GET.get('department_id')
    if not department_id:
        return JsonResponse({'doctors': []})
    try:
        # ✅ CORRECT: Use 'doctorallocation__department_id', not 'doctorallocation_set'
        doctors = CustomUser.objects.filter(
            role='doctor',
            doctorallocation__department_id=department_id
        ).distinct()
    except:
        return JsonResponse({'doctors': []})

    doctor_list = [
        {'id': doc.id, 'name': doc.get_full_name() or doc.username}
        for doc in doctors
    ]
    return JsonResponse({'doctors': doctor_list})


# -----------------------------
# AJAX: Get Available Time Slots for Doctor on Date
# -----------------------------
@require_GET
@login_required
@role_required('patient')
def get_available_time_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    if not doctor_id or not date_str:
        return JsonResponse({'available_slots': []})
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'available_slots': []})
    today = timezone.now().date()
    now_time = timezone.now().time()

    # Prevent booking in the past
    if selected_date < today:
        return JsonResponse({'available_slots': []})

    try:
        doctor = CustomUser.objects.get(id=doctor_id, role='doctor')
        day_of_week_short = selected_date.strftime('%a').lower()  # 'Monday' → 'mon'
        availability = DoctorAvailability.objects.get(doctor=doctor, day_of_week=day_of_week_short)
    except (CustomUser.DoesNotExist, DoctorAvailability.DoesNotExist):
        return JsonResponse({'available_slots': []})

    start_time = availability.start_time
    end_time = availability.end_time

    current = datetime.combine(selected_date, start_time)
    end_dt = datetime.combine(selected_date, end_time)

    # Get already booked time slots
    booked_slots = Appointment.objects.filter(
        doctor=doctor,
        schedule__date=selected_date,
        status='booked'
    ).values_list('schedule__start_time', flat=True)
    booked_times = {bt.strftime('%H:%M') for bt in booked_slots}

    available_slots = []
    while current + timedelta(minutes=30) <= end_dt:
        slot_time = current.time()
        slot_str = slot_time.strftime('%H:%M')

        # Skip past times on today
        if selected_date == today and slot_time < now_time:
            current += timedelta(minutes=30)
            continue

        if slot_str not in booked_times:
            available_slots.append(slot_str)

        current += timedelta(minutes=30)

    return JsonResponse({'available_slots': available_slots})


# -----------------------------
# Booking Form (Main View)
# -----------------------------
@login_required
@role_required('patient')
def book_appointment_form(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['date']
            time_obj = form.cleaned_data['time']
            symptoms = form.cleaned_data['symptoms']

            # Get or create the TimeSlot
            end_time_obj = (datetime.combine(date, time_obj) + timedelta(minutes=30)).time()
            time_slot, created = TimeSlot.objects.get_or_create(
                doctor=doctor,
                date=date,
                start_time=time_obj,
                defaults={'end_time': end_time_obj}
            )

            # Prevent double booking
            if Appointment.objects.filter(schedule=time_slot, status='booked').exists():
                messages.error(request, "This time slot is already booked.")
                return redirect('patients:book_appointment_form')

            # Create appointment
            Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                schedule=time_slot,
                symptoms=symptoms,
                status='booked'
            )

            messages.success(request, f'Appointment with Dr. {doctor.get_full_name()} booked successfully!')
            return redirect('patients:overview')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = AppointmentBookingForm()

    return render(request, 'patients/book_appointment_form.html', {'form': form})


# -----------------------------
# View Doctor Schedules
# -----------------------------
@login_required
@role_required('patient')
def view_doctors_schedule(request):
    doctors = CustomUser.objects.filter(role='doctor')
    schedules = TimeSlot.objects.filter(doctor__in=doctors).order_by('date', 'start_time')
    return render(request, 'patients/doctor_schedule.html', {'schedules': schedules})


# -----------------------------
# Direct Booking by Schedule ID (Optional)
# -----------------------------
@login_required
@role_required('patient')
def book_appointment(request, schedule_id):
    schedule = get_object_or_404(TimeSlot, id=schedule_id)
    if request.method == 'POST':
        if Appointment.objects.filter(patient=request.user, schedule=schedule, status='booked').exists():
            messages.error(request, 'You have already booked this appointment.')
        else:
            Appointment.objects.create(
                patient=request.user,
                doctor=schedule.doctor,
                schedule=schedule,
                status='booked'
            )
            messages.success(request, 'Appointment booked successfully.')
        return redirect('patients:appointments')
    return render(request, 'patients/book_appointment.html', {'schedule': schedule})