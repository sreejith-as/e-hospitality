from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from .models import Billing, DoctorSchedule, Appointment, MedicalHistory
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from accounts.utils import role_required

@login_required
@role_required('patient')
def dashboard(request):
    return render(request, 'patients/dashboard.html')

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
            return redirect('patients:view_doctors_schedule')
        Appointment.objects.create(
            patient=request.user,
            doctor=schedule.doctor,
            schedule=schedule,
            status='booked'
        )
        messages.success(request, 'Appointment booked successfully.')
        return redirect('patients:dashboard')
    return render(request, 'patients/book_appointment.html', {'schedule': schedule})

@login_required
@role_required('patient')
def view_medical_history(request):
    medical_history = MedicalHistory.objects.filter(patient=request.user).order_by('-updated_at')
    return render(request, 'patients/medical_history.html', {'medical_history': medical_history})

@login_required
@role_required('patient')
def view_billing(request):
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
        return redirect('patients:view_billing')
    return render(request, 'patients/pay_bill.html', {'billing': billing})

@login_required
@role_required('patient')
def health_education(request):
    return render(request, 'patients/health_education.html')
