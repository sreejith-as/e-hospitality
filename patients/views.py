from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from .models import Billing, DoctorSchedule, Appointment, MedicalHistory
from doctors.models import DoctorAvailability, Prescription
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from accounts.utils import role_required

from django.utils import timezone
from datetime import timedelta
from .forms import AppointmentBookingForm

@login_required
@role_required('patient')
def overview(request):
    user = request.user
    today = timezone.now().date()
    upcoming_appointments = Appointment.objects.filter(patient=user, schedule__date__gte=today, status='booked').order_by('schedule__date', 'schedule__start_time')
    medical_records_count = MedicalHistory.objects.filter(patient=user).count()
    active_prescriptions = Prescription.objects.filter(patient=user).order_by('-created_at')[:5]
    unpaid_bills = Billing.objects.filter(patient=user, is_paid=False).order_by('due_date')
    recent_activity = []  # Placeholder for recent activity, can be extended later

    context = {
        'upcoming_appointments': upcoming_appointments,
        'medical_records_count': medical_records_count,
        'active_prescriptions': active_prescriptions,
        'unpaid_bills': unpaid_bills,
        'recent_activity': recent_activity,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
@role_required('patient')
def appointments(request):
    user = request.user
    today = timezone.now().date()
    upcoming_appointments = Appointment.objects.filter(patient=user, schedule__date__gte=today, status='booked').order_by('schedule__date', 'schedule__start_time')
    past_appointments = Appointment.objects.filter(patient=user, schedule__date__lt=today).order_by('-schedule__date', '-schedule__start_time')
    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    return render(request, 'patients/appointments.html', context)

@login_required
@role_required('patient')
def medical_records(request):
    medical_history = MedicalHistory.objects.filter(patient=request.user).order_by('-updated_at')
    return render(request, 'patients/medical_records.html', {'medical_history': medical_history})

@login_required
@role_required('patient')
def prescriptions(request):
    prescriptions = Prescription.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'patients/prescriptions.html', {'prescriptions': prescriptions})

@login_required
@role_required('patient')
def billing(request):
    billings = Billing.objects.filter(patient=request.user).order_by('-due_date')
    return render(request, 'patients/billing.html', {'billings': billings})

@login_required
@role_required('patient')
def health_education(request):
    return render(request, 'patients/health_education.html')

# Retain existing views for booking appointments etc.

@login_required
@role_required('patient')
def book_appointment_form(request):
    from datetime import datetime
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']
            symptoms = form.cleaned_data['symptoms']
            day_of_week = date.strftime('%a').lower()[:3]  # e.g., 'mon', 'tue'
            availability = DoctorAvailability.objects.filter(doctor=doctor, day_of_week=day_of_week, start_time__lte=time, end_time__gte=time).first()
            if not availability:
                messages.error(request, f"Dr. {doctor.username} is not available on {date} at {time}. Please choose another time.")
                return redirect('patients:book_appointment_form')
            # Find or create DoctorSchedule for this date and time
            schedule, created = DoctorSchedule.objects.get_or_create(
                doctor=doctor,
                date=date,
                start_time=time,
                end_time=time  # Assuming appointment duration is fixed or handled elsewhere
            )
            existing_appointment = Appointment.objects.filter(patient=request.user, schedule=schedule, status='booked').first()
            if existing_appointment:
                messages.error(request, 'You have already booked this appointment.')
                return redirect('patients:overview')
            Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                schedule=schedule,
                symptoms=symptoms,
                status='booked'
            )
            messages.success(request, 'Appointment booked successfully.')
            return redirect('patients:overview')
    else:
        form = AppointmentBookingForm()
    return render(request, 'patients/book_appointment_form.html', {'form': form})

@login_required
@role_required('patient')
def view_doctors_schedule(request):
    doctors = CustomUser.objects.filter(role='doctor')
    schedules = DoctorSchedule.objects.filter(doctor__in=doctors).order_by('date', 'start_time')
    return render(request, 'patients/doctor_schedule.html', {'schedules': schedules})

@login_required
@role_required('patient')
def book_appointment(request, schedule_id):
    schedule = get_object_or_404(DoctorSchedule, id=schedule_id)
    if request.method == 'POST':
        existing_appointment = Appointment.objects.filter(patient=request.user, schedule=schedule, status='booked').first()
        if existing_appointment:
            messages.error(request, 'You have already booked this appointment.')
            return redirect('patients:appointments')
        Appointment.objects.create(
            patient=request.user,
            doctor=schedule.doctor,
            schedule=schedule,
            status='booked'
        )
        messages.success(request, 'Appointment booked successfully.')
        return redirect('patients:appointments')
    return render(request, 'patients/book_appointment.html', {'schedule': schedule})

@login_required
@role_required('patient')
def book_appointment_form(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['date']
            symptoms = form.cleaned_data['symptoms']
            schedule = DoctorSchedule.objects.filter(doctor=doctor, date=date).first()
            if not schedule:
                messages.error(request, f"No available schedule for Dr. {doctor.username} on {date}.")
                return redirect('patients:book_appointment_form')
            existing_appointment = Appointment.objects.filter(patient=request.user, schedule=schedule, status='booked').first()
            if existing_appointment:
                messages.error(request, 'You have already booked this appointment.')
                return redirect('patients:overview')
            Appointment.objects.create(
                patient=request.user,
                doctor=doctor,
                schedule=schedule,
                symptoms=symptoms,
                status='booked'
            )
            messages.success(request, 'Appointment booked successfully.')
            return redirect('patients:overview')
    else:
        form = AppointmentBookingForm()
    return render(request, 'patients/book_appointment_form.html', {'form': form})

@login_required
@role_required('patient')
def view_doctors_schedule(request):
    doctors = CustomUser.objects.filter(role='doctor')
    schedules = DoctorSchedule.objects.filter(doctor__in=doctors).order_by('date', 'start_time')
    return render(request, 'patients/doctor_schedule.html', {'schedules': schedules})

@login_required
@role_required('patient')
def book_appointment(request, schedule_id):
    schedule = get_object_or_404(DoctorSchedule, id=schedule_id)
    if request.method == 'POST':
        existing_appointment = Appointment.objects.filter(patient=request.user, schedule=schedule, status='booked').first()
        if existing_appointment:
            messages.error(request, 'You have already booked this appointment.')
            return redirect('patients:appointments')
        Appointment.objects.create(
            patient=request.user,
            doctor=schedule.doctor,
            schedule=schedule,
            status='booked'
        )
        messages.success(request, 'Appointment booked successfully.')
        return redirect('patients:appointments')
    return render(request, 'patients/book_appointment.html', {'schedule': schedule})

@login_required
@role_required('patient')
def medical_records(request):
    medical_history = MedicalHistory.objects.filter(patient=request.user).order_by('-updated_at')
    return render(request, 'patients/medical_records.html', {'medical_history': medical_history})

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

@login_required
@role_required('patient')
def health_education(request):
    return render(request, 'patients/health_education.html')
