# patients/views.py
from email.policy import default
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from accounts.utils import role_required
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from .models import Billing, Appointment, MedicalHistory, TimeSlot
from doctors.models import DoctorAvailability, Prescription
from accounts.models import CustomUser
from .forms import AppointmentBookingForm
from django.db.models import Sum, Count
import json

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO








# ... existing code ...

@login_required
@role_required('patient')
def download_medical_history_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    user = request.user
    medical_history = MedicalHistory.objects.filter(patient=user).order_by('-updated_at')
    prescriptions = Prescription.objects.filter(patient=user).select_related('medication', 'doctor').order_by('-created_at')
    appointments = Appointment.objects.filter(patient=user).select_related('doctor', 'schedule').order_by('-schedule__date')

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Medical History Report for {user.get_full_name()}")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Email: {user.email}")
    y -= 20
    p.drawString(50, y, f"Date of Birth: {user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else 'N/A'}")
    y -= 20
    p.drawString(50, y, f"Gender: {user.gender.title() if user.gender else 'N/A'}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Medical History:")
    y -= 20
    p.setFont("Helvetica", 10)
    for record in medical_history:
        text = f"{record.updated_at.strftime('%Y-%m-%d')}: Diagnosis: {record.diagnosis}, Medications: {record.medications or 'None'}, Allergies: {record.allergies or 'None'}, Treatments: {record.treatments or 'None'}"
        p.drawString(60, y, text)
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Prescriptions:")
    y -= 20
    p.setFont("Helvetica", 10)
    for prescription in prescriptions:
        text = f"{prescription.created_at.strftime('%Y-%m-%d')}: {prescription.medication.name}, Dosage: {prescription.dosage}, Instructions: {prescription.instructions or 'None'}, Prescribed by: Dr. {prescription.doctor.get_full_name()}"
        p.drawString(60, y, text)
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Appointments:")
    y -= 20
    p.setFont("Helvetica", 10)
    for appointment in appointments:
        text = f"{appointment.schedule.date.strftime('%Y-%m-%d')}: Dr. {appointment.doctor.get_full_name()}, Time: {appointment.schedule.start_time.strftime('%H:%M')}, Status: {appointment.status.title()}"
        p.drawString(60, y, text)
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


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
    active_prescriptions = Prescription.objects.filter(
        patient=user, 
        status__in=['Active', 'Pending']
    ).order_by('-created_at')[:5]
    unpaid_bills = Billing.objects.filter(patient=user, is_paid=False).order_by('due_date')
    recent_activity = []  # Can be extended later

    # New counts for completed appointments and total prescriptions & diagnosis
    completed_appointments_count = Appointment.objects.filter(
        patient=user, status='completed'
    ).count()
    total_prescriptions_count = Prescription.objects.filter(
        patient=user
    ).count()
    
    # Completed appointments for dashboard display
    completed_appointments = Appointment.objects.filter(
        patient=user, status='completed'
    ).select_related('doctor', 'schedule').order_by('-schedule__date', '-schedule__start_time')[:10]
    
    # Active prescriptions with unpaid bills
    active_prescriptions_unpaid = []
    unpaid_bills = Billing.objects.filter(patient=user, is_paid=False).order_by('due_date')
    
    # Link prescriptions to unpaid bills
    for bill in unpaid_bills:
        # Find prescriptions related to this bill (assuming description contains medication info)
        related_prescriptions = Prescription.objects.filter(
            patient=user,
            medication__name__icontains=bill.description
        )
        
        for prescription in related_prescriptions:
            active_prescriptions_unpaid.append({
                'prescription': prescription,
                'bill': bill
            })

    context = {
        'upcoming_appointments': upcoming_appointments,
        'medical_records_count': medical_records_count,
        'active_prescriptions': active_prescriptions,
        'active_prescriptions_unpaid': active_prescriptions_unpaid,
        'unpaid_bills': unpaid_bills,
        'recent_activity': recent_activity,
        'completed_appointments_count': completed_appointments_count,
        'total_prescriptions_count': total_prescriptions_count,
        'completed_appointments': completed_appointments,
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

    # Upcoming Appointments: booked and future/present (but not completed)
    upcoming = Appointment.objects.filter(
        patient=user,
        status='booked',
        schedule__date__gte=today
    ).select_related('doctor', 'schedule').order_by('schedule__date', 'schedule__start_time')

    # Past Appointments: only those with status = 'completed'
    # (Assuming completed appointments are only for past or today's visits)
    past_appointments = Appointment.objects.filter(
        patient=user,
        status='completed'
    ).select_related('doctor', 'schedule').order_by('-schedule__date', '-schedule__start_time')

    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past_appointments,
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
    
    prescriptions = Prescription.objects.filter(
        patient=request.user
    ).select_related('medication', 'doctor').order_by('-created_at')
    
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor', 'schedule').order_by('-schedule__date')
    
    context = {
        'medical_history': medical_history,
        'prescriptions': prescriptions,
        'appointments': appointments,
    }
    return render(request, 'patients/medical_records.html', context)


# -----------------------------
# Visit Detail & PDF Download
# -----------------------------
@login_required
@role_required('patient')
def visit_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Get related medical history for this visit
    medical_history = MedicalHistory.objects.filter(
        patient=request.user
    ).order_by('-updated_at')[:5]
    
    # Get prescriptions for this visit
    prescriptions = Prescription.objects.filter(
        patient=request.user,
        doctor=appointment.doctor
    ).select_related('medication', 'doctor').order_by('-created_at')[:10]
    
    context = {
        'appointment': appointment,
        'medical_history': medical_history,
        'prescriptions': prescriptions,
    }
    return render(request, 'patients/visit_detail.html', context)


@login_required
@role_required('patient')
def download_visit_pdf(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Get related data
    medical_history = MedicalHistory.objects.filter(
        patient=request.user
    ).order_by('-updated_at')[:5]
    
    prescriptions = Prescription.objects.filter(
        patient=request.user,
        doctor=appointment.doctor
    ).select_related('medication', 'doctor').order_by('-created_at')[:10]
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 100  # Start position

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Visit Details Report")
    y -= 60

    # Patient Info
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Patient: {appointment.patient.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Email: {appointment.patient.email}")
    y -= 20
    dob = appointment.patient.date_of_birth
    p.drawString(50, y, f"Date of Birth: {dob.strftime('%Y-%m-%d') if dob else 'N/A'}")
    y -= 30

    # Visit Details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Visit Information")
    y -= 25

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Doctor: Dr. {appointment.doctor.get_full_name()}")
    y -= 15

    # ✅ Fix: Use strftime() instead of |date
    p.drawString(50, y, f"Date: {appointment.schedule.date.strftime('%b %d, %Y')}")
    y -= 15

    # ✅ Fix: Use strftime() for time
    p.drawString(50, y, f"Time: {appointment.schedule.start_time.strftime('%I:%M %p')}")
    y -= 15

    p.drawString(50, y, "Duration: 30 minutes")
    y -= 30

    # Symptoms
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Symptoms & Reason for Visit")
    y -= 25

    p.setFont("Helvetica", 11)
    symptoms = appointment.symptoms or "Not specified"
    p.drawString(50, y, f"Symptoms: {symptoms}")
    y -= 30

    # Medical History
    if medical_history:
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Medical History")
        y -= 25

        p.setFont("Helvetica", 11)
        for record in medical_history:
            diagnosis = record.diagnosis or "Unknown"
            p.drawString(50, y, f"Diagnosis: {diagnosis}")
            y -= 15

            treatment = record.treatments or "None"
            p.drawString(50, y, f"Treatment: {treatment}")
            y -= 20

            if y < 100:
                p.showPage()
                y = height - 50

    # Prescriptions
    if prescriptions:
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Prescriptions")
        y -= 25

        p.setFont("Helvetica", 11)
        for prescription in prescriptions:
            p.drawString(50, y, f"Medication: {prescription.medication.name}")
            y -= 15

            p.drawString(50, y, f"Dosage: {prescription.dosage}")
            y -= 15

            instructions = prescription.instructions or "As directed"
            p.drawString(50, y, f"Instructions: {instructions}")
            y -= 20

            if y < 100:
                p.showPage()
                y = height - 50

    # Finalize PDF
    p.save()
    buffer.seek(0)

    # Return as response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="visit_{appointment.id}_{appointment.patient.username}.pdf"'
    return response


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

def prescriptions(request):
    """Display patient's prescriptions"""
    return render(request, 'patients/prescriptions.html')


# -----------------------------
# Prescription PDF Download
# -----------------------------
@login_required
@role_required('patient')
def download_prescription_pdf(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id, patient=request.user)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Prescription Details")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Patient: {request.user.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Email: {request.user.email}")
    y -= 20
    p.drawString(50, y, f"Date of Birth: {request.user.date_of_birth.strftime('%Y-%m-%d') if request.user.date_of_birth else 'N/A'}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Prescription Information:")
    y -= 25

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Medication: {prescription.medication.name}")
    y -= 20
    p.drawString(50, y, f"Dosage: {prescription.dosage}")
    y -= 20
    p.drawString(50, y, f"Instructions: {prescription.instructions or 'As directed by physician'}")
    y -= 20
    p.drawString(50, y, f"Prescribed by: Dr. {prescription.doctor.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Date Prescribed: {prescription.created_at.strftime('%Y-%m-%d')}")
    y -= 20
    p.drawString(50, y, f"Status: {prescription.status}")

    # Add footer
    y -= 50
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "This prescription was generated from the eHospital system.")
    p.drawString(50, y-15, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}_{request.user.username}.pdf"'
    return response


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


# -----------------------------
# Cancel Appointment (Patient)
# -----------------------------
@login_required
@role_required('patient')
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    if request.method == 'POST':
        # Only allow cancellation of booked appointments
        if appointment.status == 'booked':
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully.')
        else:
            messages.error(request, 'Cannot cancel this appointment.')
        return redirect('patients:appointments')
    
    return render(request, 'patients/cancel_appointment.html', {'appointment': appointment})


# -----------------------------
# Edit Appointment (Patient)
# -----------------------------
@login_required
@role_required('patient')
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Only allow editing of booked appointments
    if appointment.status != 'booked':
        messages.error(request, 'Cannot edit this appointment.')
        return redirect('/patients/overview/#appointments')
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, instance=appointment)
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

            # Update appointment
            appointment.doctor = doctor
            appointment.schedule = time_slot
            appointment.symptoms = symptoms
            appointment.save()

            messages.success(request, f'Appointment with Dr. {doctor.get_full_name()} updated successfully!')
            return redirect('/patients/overview/#appointments')
        else:
            # Handle form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        # Pre-populate form with existing appointment data
        form = AppointmentBookingForm(initial={
            'doctor': appointment.doctor,
            'date': appointment.schedule.date,
            'time': appointment.schedule.start_time,
            'symptoms': appointment.symptoms
        })

    return render(request, 'patients/edit_appointment.html', {'form': form, 'appointment': appointment})
