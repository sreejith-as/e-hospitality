# patients/views.py
from email.policy import default
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from accounts.utils import role_required
from django.utils import timezone
from datetime import date, datetime, time, timedelta

from admins.models import DoctorAllocation, Department
from .models import Billing, Appointment, MedicalVisit, TimeSlot
from doctors.models import DoctorAvailability, Prescription, DiagnosisNote
from accounts.models import CustomUser
from .forms import AppointmentBookingForm
from django.db.models import Sum, Count
import json
from django.core.paginator import Paginator
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


# -----------------------------
# Patient Dashboard & Overview
# -----------------------------
@login_required
@role_required('patient')
def overview(request):
    user = request.user
    today = timezone.now().date()

    # Upcoming Appointments
    upcoming_appointments = Appointment.objects.filter(
        patient=user,
        schedule__date__gte=today,
        status='booked'
    ).select_related('doctor', 'schedule').order_by('schedule__date', 'schedule__start_time')

    # Completed Appointments for Medical Records
    completed_appointments = Appointment.objects.filter(
        patient=user,
        status='completed'
    ).select_related('doctor', 'schedule').order_by('-schedule__date')

    medical_records = []
    for appointment in completed_appointments:
        # Get diagnosis notes
        diagnosis_notes = DiagnosisNote.objects.filter(
            appointment=appointment,
            patient=user
        ).values_list('note', flat=True)
        diagnosis_text = "; ".join(diagnosis_notes) if diagnosis_notes else "No diagnosis recorded"

        # Get prescriptions (only medicine names)
        prescriptions = Prescription.objects.filter(
            appointment=appointment,
            patient=user
        ).select_related('medication')
        medicines = [p.medication.name for p in prescriptions]
        medicines_text = ", ".join(medicines) if medicines else "No medicines prescribed"

        # Get department via DoctorAllocation
        try:
            allocation = DoctorAllocation.objects.get(doctor=appointment.doctor)
            department_name = allocation.department.name
        except DoctorAllocation.DoesNotExist:
            department_name = "General Practice"
        except Exception:
            department_name = "General Practice"

        medical_records.append({
            'appointment': appointment,
            'date': appointment.schedule.date,
            'doctor_name': f"Dr. {appointment.doctor.get_full_name()}",
            'department': department_name,
            'diagnosis': diagnosis_text,
            'medicines': medicines_text,
            'detail_url': reverse('patients:visit_detail', args=[appointment.id])
        })

    # Paginate medical records
    medical_records_paginator = Paginator(medical_records, 5)
    medical_records_page_number = request.GET.get('page_medical_records')
    medical_records_page = medical_records_paginator.get_page(medical_records_page_number)

    # Unpaid Bills
    unpaid_bills = Billing.objects.filter(patient=user, is_paid=False)
    bills_paginator = Paginator(unpaid_bills, 8)
    bills_page_number = request.GET.get('page_bills')
    bills_page = bills_paginator.get_page(bills_page_number)

    # Summary counts
    medical_records_count = medical_records_paginator.count
    active_prescriptions_count = prescriptions.count() if 'prescriptions' in locals() else 0
    unpaid_bills_count = bills_paginator.count

    context = {
        'upcoming_appointments': upcoming_appointments,
        'medical_records_count': medical_records_count,
        'active_prescriptions_count': active_prescriptions_count,
        'unpaid_bills_count': unpaid_bills_count,
        'medical_records_page': medical_records_page,
        'bills_page': bills_page,
        'recent_activity': [],
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

    # Upcoming Appointments (not cancelled)
    upcoming_appointments = Appointment.objects.filter(
        patient=user,
        schedule__date__gte=today,
        status='booked'
    ).select_related('doctor', 'schedule').order_by('schedule__date', 'schedule__start_time')

    # Past Appointments (completed or cancelled, in the past)
    past_appointments = Appointment.objects.filter(
        patient=user,
        schedule__date__lt=today
    ).select_related('doctor', 'schedule').order_by('-schedule__date', '-schedule__start_time')

    # Paginate Upcoming (10 per page)
    paginator_upcoming = Paginator(upcoming_appointments, 6)
    page_upcoming = request.GET.get('page_upcoming')
    upcoming_page = paginator_upcoming.get_page(page_upcoming)

    # Paginate Past (10 per page)
    paginator_past = Paginator(past_appointments, 6)
    page_past = request.GET.get('page_past')
    past_page = paginator_past.get_page(page_past)

    # Summary counts
    completed_count = past_appointments.filter(status='completed').count()
    total_appointments_count = upcoming_page.paginator.count + past_page.paginator.count

    context = {
        'upcoming_page': upcoming_page,
        'past_page': past_page,
        'completed_count': completed_count,
        'total_appointments_count': total_appointments_count,
    }

    return render(request, 'patients/appointments.html', context)


# -----------------------------
# Medical Records
# ----------------------------
# -----------------------------
# Visit Detail & PDF Download
# -----------------------------
@login_required
@role_required('patient')
def visit_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    
    # Get related medical history for this visit
    medical_history = MedicalVisit.objects.filter(
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
    medical_history = MedicalVisit.objects.filter(
        patient=request.user
    ).order_by('-created_at')[:5]  # Use created_at, not updated_at

    prescriptions = Prescription.objects.filter(
        patient=request.user,
        doctor=appointment.doctor
    ).select_related('medication', 'doctor').order_by('-created_at')[:10]

    # Try to get the bill for this appointment
    try:
        bill = Billing.objects.get(appointment=appointment)
        total_amount = bill.amount
        is_paid = bill.is_paid
        due_date = bill.due_date
    except Billing.DoesNotExist:
        total_amount = 0
        is_paid = False
        due_date = None

    # Calculate medicine cost (if prescriptions exist)
    total_medicine_cost = sum(p.line_total for p in prescriptions)
    consultation_fee = settings.CONSULTATION_FEE
    expected_total = total_medicine_cost + consultation_fee

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

    # Date and Time
    p.drawString(50, y, f"Date: {appointment.schedule.date.strftime('%b %d, %Y')}")
    y -= 15
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
            p.drawString(50, y, f"Frequency: {prescription.frequency}")
            y -= 15
            p.drawString(50, y, f"Duration: {prescription.duration_days} days")
            y -= 15
            instructions = prescription.instructions or "As directed"
            p.drawString(50, y, f"Instructions: {instructions}")
            y -= 20

            if y < 100:
                p.showPage()
                y = height - 50

    # Billing Summary
    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Billing Summary")
    y -= 25

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Medicine Cost: ₹{total_medicine_cost:.2f}")
    y -= 20
    p.drawString(50, y, f"Consultation Fee: ₹{consultation_fee:.2f}")
    y -= 20
    p.drawString(50, y, f"Expected Total: ₹{expected_total:.2f}")
    y -= 20

    if total_amount > 0:
        p.drawString(50, y, f"Billed Amount: ₹{total_amount:.2f}")
        y -= 20
        status = "Paid" if is_paid else "Unpaid"
        p.drawString(50, y, f"Status: {status}")
        y -= 20
        if due_date:
            p.drawString(50, y, f"Due Date: {due_date.strftime('%b %d, %Y')}")
            y -= 20
    else:
        p.drawString(50, y, "No bill generated for this visit.")
        y -= 20

    if y < 100:
        p.showPage()
        y = height - 50

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "This visit report was generated from the eHospital system.")
    y -= 15
    p.drawString(50, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 15

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Return as response
    filename = f"visit_{appointment.id}_{appointment.patient.username}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# -----------------------------
# Billing & Payments
# -----------------------------

@login_required
@role_required('patient')
def pay_bill(request, billing_id):
    billing = get_object_or_404(Billing, id=billing_id, patient=request.user)

    if request.method == 'POST':
        try:
            # Create Stripe Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': f"Medical Bill #{billing.id}",
                            'description': billing.description,
                        },
                        'unit_amount': int(billing.amount * 100),  # in paise
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    reverse('patients:payment_success')
                ) + f'?session_id={{CHECKOUT_SESSION_ID}}&billing_id={billing.id}',
                cancel_url=request.build_absolute_uri(
                    reverse('patients:dashboard')
                ),
            )
            return redirect(session.url, code=303)
        except Exception as e:
            messages.error(request, f"Error creating payment session: {str(e)}")
            return redirect('patients:dashboard')

    return render(request, 'patients/pay_bill.html', {'billing': billing})

def payment_success(request):
    session_id = request.GET.get('session_id')
    billing_id = request.GET.get('billing_id')

    if not session_id or not billing_id:
        messages.error(request, "Missing payment details.")
        return redirect('patients:dashboard')

    try:
        billing = get_object_or_404(Billing, id=billing_id, patient=request.user)
        if not billing.is_paid:
            billing.is_paid = True
            billing.save()
            messages.success(request, "Payment successful! Thank you.")
        else:
            messages.info(request, "This bill is already paid.")
    except Exception as e:
        messages.error(request, f"Error updating bill: {str(e)}")

    return redirect('patients:dashboard')

# -----------------------------
# Health Education
# -----------------------------
@login_required
@role_required('patient')
def health_education(request):
    return render(request, 'patients/health_education.html')

# -----------------------------
# Prescription PDF Download
# -----------------------------
@login_required
@role_required('patient')
def download_prescription_pdf(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id, patient=request.user)

    # Get all prescriptions for this appointment (if any)
    prescriptions = Prescription.objects.filter(
        appointment=prescription.appointment,
        patient=request.user
    ).select_related('medication', 'doctor')

    # Calculate totals
    total_medicine_cost = sum(p.line_total for p in prescriptions)
    consultation_fee = settings.CONSULTATION_FEE
    grand_total = total_medicine_cost + consultation_fee

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Prescription")
    y -= 30

    # Patient Info
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Patient: {request.user.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Email: {request.user.email}")
    y -= 20
    dob = request.user.date_of_birth
    p.drawString(50, y, f"Date of Birth: {dob.strftime('%Y-%m-%d') if dob else 'N/A'}")
    y -= 30

    # Doctor & Date
    p.drawString(50, y, f"Prescribed by: Dr. {prescription.doctor.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Date: {prescription.created_at.strftime('%b %d, %Y')}")
    y -= 30

    # Medications Table Header
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Medications:")
    y -= 20
    p.drawString(50, y, "Name")
    p.drawString(200, y, "Dosage")
    p.drawString(300, y, "Frequency")
    p.drawString(400, y, "Duration")
    p.drawString(500, y, "Instructions")
    y -= 15
    p.line(50, y, 580, y)
    y -= 15

    # Medications
    p.setFont("Helvetica", 11)
    for p_item in prescriptions:
        if y < 100:
            p.showPage()
            y = height - 50
        p.drawString(50, y, p_item.medication.name)
        p.drawString(200, y, p_item.dosage)
        p.drawString(300, y, p_item.frequency)
        p.drawString(400, y, f"{p_item.duration_days} days")
        p.drawString(500, y, p_item.instructions or "As directed")
        y -= 20

    y -= 20
    p.line(50, y, 580, y)
    y -= 20

    # Billing Summary
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Billing Summary")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Medicine Cost: ₹{total_medicine_cost:.2f}")
    y -= 20
    p.drawString(50, y, f"Consultation Fee: ₹{consultation_fee:.2f}")
    y -= 20
    p.drawString(50, y, f"Total Amount: ₹{grand_total:.2f}")
    y -= 30

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "This prescription was generated from the eHospital system.")
    y -= 15
    p.drawString(50, y, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 15

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription_id}.pdf"'
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
            date = form.cleaned_data['date']         # ✅ Selected date
            time_obj = form.cleaned_data['time']     # ✅ Selected time
            symptoms = form.cleaned_data['symptoms']

            # Calculate end time
            end_time_obj = (datetime.combine(date, time_obj) + timedelta(minutes=30)).time()

            # ✅ Get or create TimeSlot with correct date
            time_slot, created = TimeSlot.objects.get_or_create(
                doctor=doctor,
                date=date,              # ✅ Not timezone.now().date()
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
            return redirect('patients:appointments')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
            return redirect('/patients/appointments')
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


@login_required
@role_required('patient')
def download_medical_history_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    user = request.user

    # Fetch data
    medical_visits = MedicalVisit.objects.filter(patient=user).order_by('-created_at')
    prescriptions = Prescription.objects.filter(patient=user).select_related('medication', 'doctor').order_by('-created_at')
    appointments = Appointment.objects.filter(patient=user).select_related('doctor', 'schedule').order_by('-schedule__date')
    bills = Billing.objects.filter(patient=user).order_by('-created_at')

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Medical History Report for {user.get_full_name()}")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Email: {user.email}")
    y -= 20
    dob = user.date_of_birth
    p.drawString(50, y, f"Date of Birth: {dob.strftime('%Y-%m-%d') if dob else 'N/A'}")
    y -= 20
    p.drawString(50, y, f"Gender: {user.gender.title() if user.gender else 'N/A'}")
    y -= 30

    # Section: Medical History
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Medical History")
    y -= 25

    p.setFont("Helvetica", 10)
    if medical_visits.exists():
        for visit in medical_visits:
            diagnosis = visit.diagnosis or "Unknown"
            symptoms = visit.symptoms or "Not specified"
            notes = visit.notes or "No additional notes"

            text = f"{visit.created_at.strftime('%Y-%m-%d')}: Diagnosis: {diagnosis}"
            p.drawString(60, y, text)
            y -= 15

            p.drawString(70, y, f"Symptoms: {symptoms}")
            y -= 15

            p.drawString(70, y, f"Doctor: Dr. {visit.doctor.get_full_name()}")
            y -= 15

            p.drawString(70, y, f"Notes: {notes}")
            y -= 20

            if y < 100:
                p.showPage()
                y = height - 50
    else:
        p.drawString(60, y, "No medical history recorded.")
        y -= 20

    y -= 20
    if y < 100:
        p.showPage()
        y = height - 50

    # Section: Prescriptions
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Prescriptions")
    y -= 25

    p.setFont("Helvetica", 10)
    if prescriptions.exists():
        for prescription in prescriptions:
            text = (
                f"{prescription.created_at.strftime('%Y-%m-%d')}: "
                f"{prescription.medication.name}, "
                f"Dosage: {prescription.dosage}, "
                f"Frequency: {prescription.frequency}, "
                f"Duration: {prescription.duration_days} days, "
                f"Instructions: {prescription.instructions or 'As directed'}, "
                f"Prescribed by: Dr. {prescription.doctor.get_full_name()}"
            )
            lines = []
            line = ""
            for word in text.split():
                if len(line + word) < 90:
                    line += word + " "
                else:
                    lines.append(line)
                    line = word + " "
            lines.append(line)

            for line in lines:
                if y < 100:
                    p.showPage()
                    y = height - 50
                p.drawString(60, y, line.strip())
                y -= 15
    else:
        p.drawString(60, y, "No prescriptions recorded.")
        y -= 20

    y -= 20
    if y < 100:
        p.showPage()
        y = height - 50

    # Section: Billing Summary
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Billing Summary")
    y -= 25

    p.setFont("Helvetica", 10)
    if bills.exists():
        total_paid = 0
        total_unpaid = 0

        for bill in bills:
            # Calculate medicine cost (sum of prescriptions for this bill's appointment)
            associated_prescriptions = Prescription.objects.filter(appointment=bill.appointment)
            medicine_cost = sum(p.line_total for p in associated_prescriptions)
            consultation_fee = settings.CONSULTATION_FEE
            expected_total = medicine_cost + consultation_fee

            status = "Paid" if bill.is_paid else "Unpaid"
            if bill.is_paid:
                total_paid += bill.amount
            else:
                total_unpaid += bill.amount

            p.drawString(60, y, f"Bill Date: {bill.created_at.strftime('%Y-%m-%d')}")
            y -= 15
            p.drawString(70, y, f"Medicine Cost: ₹{medicine_cost:.2f}")
            y -= 15
            p.drawString(70, y, f"Consultation Fee: ₹{consultation_fee:.2f}")
            y -= 15
            p.drawString(70, y, f"Expected Total: ₹{expected_total:.2f}")
            y -= 15
            p.drawString(70, y, f"Billed Amount: ₹{bill.amount:.2f}")
            y -= 15
            p.drawString(70, y, f"Status: {status}")
            y -= 15
            p.drawString(70, y, f"Due Date: {bill.due_date.strftime('%Y-%m-%d')}")
            y -= 20

            if y < 100:
                p.showPage()
                y = height - 50
        y -= 20

        # Summary
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, f"Total Paid: ₹{total_paid:.2f}")
        y -= 20
        p.drawString(60, y, f"Total Unpaid: ₹{total_unpaid:.2f}")
        y -= 20
    else:
        p.drawString(60, y, "No bills generated.")
        y -= 20

    y -= 20
    if y < 100:
        p.showPage()
        y = height - 50

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "This medical history report was generated from the eHospital system.")
    y -= 15
    p.drawString(50, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 15

    p.showPage()
    p.save()
    buffer.seek(0)

    # Return PDF
    filename = f"medical_history_{user.username}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@require_GET
@login_required
@role_required('patient')
def get_doctor_schedule(request):
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'success': False, 'working_hours': []})

    try:
        doctor = CustomUser.objects.get(id=doctor_id, role='doctor')
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'working_hours': []})

    availabilities = DoctorAvailability.objects.filter(doctor=doctor)

    day_order = {
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
        'fri': 4, 'sat': 5, 'sun': 6
    }

    sorted_avail = sorted(availabilities, key=lambda x: day_order[x.day_of_week])

    return JsonResponse({
        'success': True,
        'working_hours': [
            {
                'day': avail.get_day_of_week_display(),
                'start_time': avail.start_time.strftime('%H:%M'),
                'end_time': avail.end_time.strftime('%H:%M')
            }
            for avail in sorted_avail
        ]
    })