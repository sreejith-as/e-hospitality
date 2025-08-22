from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from accounts.models import CustomUser
from .models import Department, Room, Resource, DoctorAllocation
from accounts.utils import role_required
from django.utils.timezone import now
from django.db.models import Count, Sum, Q
from patients.models import Appointment, Billing, MedicalVisit
from accounts.forms import PatientRegistrationForm, DoctorRegistrationForm, AdminRegistrationForm, PatientProfileForm
from .forms import PatientEditForm, DoctorEditForm, AdminEditForm
from doctors.models import Medication, MedicineInventory, DoctorAvailability
from doctors.forms import MedicationForm
from django.core.paginator import Paginator
from admins.models import DoctorAllocation
from django.db import transaction

# -----------------------------
# Dashboard View
# -----------------------------
@login_required
@role_required('admin')
def dashboard(request):
    today = now().date()
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_doctors = CustomUser.objects.filter(role='doctor').count()
    total_admins = CustomUser.objects.filter(role='admin').count()

    total_revenue = Billing.objects.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0

    todays_appointments_count = Appointment.objects.filter(schedule__date=today).count()
    todays_total_revenue = Billing.objects.filter(is_paid=True, due_date=today).aggregate(total=Sum('amount'))['total'] or 0
    todays_bills = Billing.objects.filter(due_date=today)
    total_bills_count = todays_bills.count()
    total_unpaid_bills = todays_bills.filter(is_paid=False).count()
    total_billed_amount = todays_bills.aggregate(total=Sum('amount'))['total'] or 0
    total_paid_amount = todays_bills.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0

    todays_appointment_status = Appointment.objects.filter(schedule__date=today).values('status').annotate(count=Count('id'))
    todays_financial_overview = Billing.objects.filter(due_date=today).values('is_paid').annotate(count=Count('id'), total_amount=Sum('amount'))

    todays_appointments_list = Appointment.objects.filter(schedule__date=today).select_related('patient', 'doctor', 'schedule')
    departments = Department.objects.all()
    billings = Billing.objects.all()

    medications_list = Medication.objects.all().order_by('name')
    paginator = Paginator(medications_list, 10)
    page_number = request.GET.get('page')
    medications = paginator.get_page(page_number)

    # --- Profile Form Handling ---
    profile_form = None
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = PatientProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('admins:dashboard') 
            else:
                messages.error(request, 'Please correct the errors below.')
    if not profile_form: 
        profile_form = PatientProfileForm(instance=request.user)

    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_admins': total_admins,
        'todays_appointments': todays_appointments_count,
        'total_revenue': total_revenue,
        'todays_appointment_status': todays_appointment_status,
        'todays_financial_overview': todays_financial_overview,
        'todays_appointments_list': todays_appointments_list,
        'total_bills_count': total_bills_count,
        'total_unpaid_bills': total_unpaid_bills,
        'total_billed_amount': total_billed_amount,
        'total_paid_amount': total_paid_amount,
        'todays_total_revenue': todays_total_revenue, 
        'departments': departments,
        'billings': billings,
        'medications': medications,
        'profile_form': profile_form,
    }
    return render(request, 'admins/dashboard.html', context)

# -----------------------------
# Profile View
# -----------------------------
@role_required('admin')
def update_admin_profile(request):
    """
    View for the admin to update their profile on a dedicated page.
    """
    user = request.user

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            url = reverse('admins:dashboard') + '#profile'
            return redirect(url)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PatientProfileForm(instance=user)

    return render(request, 'admins/update_admin_profile.html', {'form': form})

# -----------------------------
# List Users
# -----------------------------
@login_required
@role_required('admin')
def list_patients(request):
    # Get the search query from the URL
    search_query = request.GET.get('search', '')

    # Start with all patients
    patients = CustomUser.objects.filter(role='patient')

    # Apply search filter if a query is provided
    if search_query:
        patients = patients.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Order and paginate
    patients = patients.order_by('username')
    paginator = Paginator(patients, 10)  # 10 patients per page
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    # Pass the search query back to the template so it stays in the input field
    return render(request, 'admins/patients.html', {
        'users': users,
        'search_query': search_query
    })

@login_required
@role_required('admin')
def list_doctors(request):
    # Get the search query from the URL
    search_query = request.GET.get('search', '')

    # Start with all doctors
    doctors_queryset = CustomUser.objects.filter(role='doctor')

    # Apply search filter if a query is provided
    if search_query:
        doctors_queryset = doctors_queryset.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Apply prefetch and order
    doctors_queryset = doctors_queryset.select_related().prefetch_related(
        'availabilities',
        'doctorallocation_set__department'
    ).order_by('username')

    # Paginate
    paginator = Paginator(doctors_queryset, 10)
    page_number = request.GET.get('page')
    doctors_page = paginator.get_page(page_number)

    day_names = [
        ('mon', 'Mon'),
        ('tue', 'Tue'),
        ('wed', 'Wed'),
        ('thu', 'Thu'),
        ('fri', 'Fri'),
        ('sat', 'Sat'),
        ('sun', 'Sun'),
    ]

    for doctor in doctors_page: 
        avails = list(doctor.availabilities.all()) 

        # --- Calculate Working Days ---
        working_days = []
        for day_short, day_long in day_names:
            if any(a.day_of_week == day_short for a in avails):
                working_days.append(day_long)
        doctor.working_days = ', '.join(working_days) if working_days else 'Not set'

        # --- Calculate Working Hours ---
        if avails:
            first_avail = avails[0]
            if all(a.start_time == first_avail.start_time and a.end_time == first_avail.end_time for a in avails):
                doctor.working_hours = f"{first_avail.start_time.strftime('%H:%M')} – {first_avail.end_time.strftime('%H:%M')}"
            else:
                doctor.working_hours = "Varies by day"
        else:
            doctor.working_hours = "Not set"

    return render(request, 'admins/doctors.html', {
        'users': doctors_page,
        'search_query': search_query
    })

@login_required
@role_required('admin')
def list_admins(request):
    # Get the search query from the URL
    search_query = request.GET.get('search', '')

    # Start with all admins
    admins = CustomUser.objects.filter(role='admin')

    # Apply search filter if a query is provided
    if search_query:
        admins = admins.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Order and paginate
    admins = admins.order_by('username')
    paginator = Paginator(admins, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    return render(request, 'admins/admins.html', {
        'users': users,
        'role': 'admin',
        'search_query': search_query
    })

# -----------------------------
# Add Users
# -----------------------------
@login_required
@role_required('admin')
def add_patient(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'patient'
            user.save()
            messages.success(request, 'Patient created successfully.')
            return redirect('admins:list_patients')
    else:
        form = PatientRegistrationForm()
    return render(request, 'admins/add_patient.html', {'form': form})

@login_required
@role_required('admin')
def add_doctor(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'doctor'
            user.save()

            # Save doctor-specific schedule and allocation
            department = form.cleaned_data.get('department')
            work_monday = form.cleaned_data.get('work_monday')
            work_tuesday = form.cleaned_data.get('work_tuesday')
            work_wednesday = form.cleaned_data.get('work_wednesday')
            work_thursday = form.cleaned_data.get('work_thursday')
            work_friday = form.cleaned_data.get('work_friday')
            work_saturday = form.cleaned_data.get('work_saturday')
            work_sunday = form.cleaned_data.get('work_sunday')
            start_time = form.cleaned_data.get('start_time')
            end_time = form.cleaned_data.get('end_time')

            from doctors.models import DoctorAvailability
            from admins.models import DoctorAllocation

            # Create DoctorAvailability entries for each day the doctor works
            if work_monday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='mon', start_time=start_time, end_time=end_time)
            if work_tuesday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='tue', start_time=start_time, end_time=end_time)
            if work_wednesday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='wed', start_time=start_time, end_time=end_time)
            if work_thursday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='thu', start_time=start_time, end_time=end_time)
            if work_friday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='fri', start_time=start_time, end_time=end_time)
            if work_saturday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='sat', start_time=start_time, end_time=end_time)
            if work_sunday:
                DoctorAvailability.objects.create(doctor=user, day_of_week='sun', start_time=start_time, end_time=end_time)

            DoctorAllocation.objects.create(
                doctor=user,
                department=department,
                room=None
            )

            messages.success(request, 'Doctor created successfully.')
            return redirect('admins:list_doctors')
    else:
        form = DoctorRegistrationForm()
    return render(request, 'admins/add_doctor.html', {'form': form})

@login_required
@role_required('admin')
def add_admin(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'
            user.save()
            messages.success(request, 'Admin created successfully.')
            return redirect('admins:list_admins')
    else:
        form = AdminRegistrationForm()
    return render(request, 'admins/add_admin.html', {'form': form})

# -----------------------------
# Edit Users
# -----------------------------
@login_required
@role_required('admin')
def edit_patient(request, user_id):
    patient = get_object_or_404(CustomUser, id=user_id, role='patient')

    if request.method == 'POST':
        form = PatientEditForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient updated successfully.')
            return redirect('admins:list_patients')
    else:
        form = PatientEditForm(instance=patient)

    return render(request, 'admins/edit_patient.html', {'form': form, 'patient': patient})

@login_required
@role_required('admin')
def edit_doctor(request, user_id):
    doctor = get_object_or_404(CustomUser, id=user_id, role='doctor')

    if request.method == 'POST':
        form = DoctorEditForm(request.POST, instance=doctor)
        if form.is_valid():
            user = form.save()
            
            # Handle department allocation
            department = form.cleaned_data.get('department')
            if department:
                DoctorAllocation.objects.update_or_create(
                    doctor=user,
                    defaults={'department': department}
                )
            
            messages.success(request, f'Doctor {user.get_full_name} updated successfully.')
            return redirect('admins:list_doctors')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorEditForm(instance=doctor)
        # Pre-populate department if exists
        allocation = doctor.doctorallocation_set.first()
        if allocation:
            form.fields['department'].initial = allocation.department

    return render(request, 'admins/edit_doctor.html', {'form': form, 'doctor': doctor})

@login_required
@role_required('admin')
def edit_admin(request, user_id):
    admin = get_object_or_404(CustomUser, id=user_id, role='admin')

    if request.method == 'POST':
        form = AdminEditForm(request.POST, instance=admin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin updated successfully.')
            return redirect('admins:list_admins')
    else:
        form = AdminEditForm(instance=admin)

    return render(request, 'admins/edit_admin.html', {'form': form, 'admin': admin})

# -----------------------------
# Delete Users
# -----------------------------
@login_required
@role_required('admin')
def delete_patient(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='patient')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Patient deleted successfully.')
        return redirect('admins:list_patients')

    return render(request, 'admins/delete_patient.html', {'user': user, 'current_user': request.user})

@login_required
@role_required('admin')
def delete_doctor(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='doctor')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Doctor deleted successfully.')
        return redirect('admins:list_doctors')

    return render(request, 'admins/delete_doctor.html', {'user': user, 'current_user': request.user})

@login_required
@role_required('admin')
def delete_admin(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='admin')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Admin deleted successfully.')
        return redirect('admins:list_admins')

    return render(request, 'admins/delete_admin.html', {'user': user})

# -----------------------------
# Appointment Views
# -----------------------------
@role_required('admin')
def appointment_detail(request, appointment_id):
    """
    View to display the detailed information of a single appointment.
    """
    # Get the appointment with related patient, doctor, and schedule data
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor', 'schedule'),
        id=appointment_id
    )

    # Optionally, get the associated medical visit if it exists
    medical_visit = MedicalVisit.objects.filter(appointment=appointment).first()

    # Context for the template
    context = {
        'appointment': appointment,
        'medical_visit': medical_visit,
    }

    return render(request, 'admins/appointment_detail.html', context)

@login_required
@role_required('admin')
def all_appointments(request):
    """
    View to display all appointments with search and pagination.
    """
    # Start with all appointments, ordered by date (newest first)
    appointments_list = Appointment.objects.select_related(
        'patient', 
        'doctor', 
        'schedule'
    ).order_by('-schedule__date', '-schedule__start_time')

    # Handle Search
    search_query = request.GET.get('search', '')
    if search_query:
        appointments_list = appointments_list.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__username__icontains=search_query) |
            Q(doctor__first_name__icontains=search_query) |
            Q(doctor__last_name__icontains=search_query) |
            Q(doctor__username__icontains=search_query) |
            Q(schedule__date__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Apply Pagination
    paginator = Paginator(appointments_list, 10)  # 15 appointments per page
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)

    # Pass context to the template
    context = {
        'appointments': appointments,
        'search_query': search_query, # So the search term stays in the input
    }

    return render(request, 'admins/all_appointments.html', context)

# -----------------------------
# Department Views
# -----------------------------
@login_required
@role_required('admin')
def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Department.objects.create(name=name, description=description)
            messages.success(request, 'Department added successfully.')
            url = reverse('admins:dashboard') + '#departments'
            return redirect(url)
        else:
            messages.error(request, 'Name is required.')
    return render(request, 'admins/add_department.html')

@login_required
@role_required('admin')
def edit_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            department.name = name
            department.description = description
            department.save()
            messages.success(request, 'Department updated successfully.')
            url = reverse('admins:dashboard') + '#departments'
            return redirect(url)
        else:
            messages.error(request, 'Name is required.')
    return render(request, 'admins/edit_department.html', {'department': department})

@login_required
@role_required('admin')
def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        url = reverse('admins:dashboard') + '#departments'
        return redirect(url)
    return render(request, 'admins/delete_department.html', {'department': department})

# -----------------------------
# Medication Views
# -----------------------------
@role_required('admin')
def add_medication(request):
    """
    View to handle adding a new medication and its initial stock.
    GET: Renders the dedicated 'add_medication.html' form.
    POST: Processes the form and redirects back to the dashboard.
    """
    if request.method == 'POST':
        # Medicine data
        name = request.POST.get('name')
        price = request.POST.get('price')
        unit = request.POST.get('unit', 'tablet')
        safety_warnings = request.POST.get('safety_warnings', '')

        # Stock data
        quantity = request.POST.get('quantity')
        batch_number = request.POST.get('batch_number', '')
        expiry_date = request.POST.get('expiry_date', None)

        # Validate
        try:
            price = float(price)
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid price or quantity.")
            # On error, re-render the form with the user's data
            return render(request, 'admins/add_medication.html', {
                'name': name,
                'price': price,
                'unit': unit,
                'safety_warnings': safety_warnings,
                'quantity': quantity,
                'batch_number': batch_number,
                'expiry_date': expiry_date,
            })

        # Create medicine
        medicine = Medication.objects.create(
            name=name,
            price=price,
            unit=unit,
            safety_warnings=safety_warnings
        )

        # If quantity > 0, create inventory entry
        if quantity > 0:
            MedicineInventory.objects.create(
                medicine=medicine,
                quantity=quantity,
                batch_number=batch_number,
                expiry_date=expiry_date
            )

        messages.success(request, f"Medicine '{name}' added with {quantity} units in stock.")
        # Redirect back to the main dashboard
        url = reverse('admins:dashboard') + '#medications'
        return redirect(url)

    # If it's a GET request, show the dedicated add page
    else:
        return render(request, 'admins/add_medication.html')

@role_required('admin')
def edit_medication(request, med_id):
    """
    View to handle editing an existing medication and optionally adding stock.
    GET: Renders the dedicated 'edit_medication.html' form.
    POST: Updates the medicine and adds new stock if provided, then redirects.
    """
    medication = get_object_or_404(Medication, id=med_id)
    
    if request.method == 'POST':
        # Medicine data
        name = request.POST.get('name')
        price = request.POST.get('price')
        unit = request.POST.get('unit')
        safety_warnings = request.POST.get('safety_warnings', '')

        # Stock data for adding more
        quantity = request.POST.get('quantity')
        batch_number = request.POST.get('batch_number', '')
        expiry_date = request.POST.get('expiry_date', None)

        # Validate
        try:
            price = float(price)
            # Quantity can be 0 (meaning don't add stock)
            quantity = int(quantity) if quantity else 0
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Invalid price or quantity.")
            # On error, re-render the form with current data
            return render(request, 'admins/edit_medication.html', {
                'medication': medication
            })

        # Update the existing medication
        medication.name = name
        medication.price = price
        medication.unit = unit
        medication.safety_warnings = safety_warnings
        medication.save()

        # If a positive quantity is provided, add new stock
        if quantity > 0:
            MedicineInventory.objects.create(
                medicine=medication,
                quantity=quantity,
                batch_number=batch_number,
                expiry_date=expiry_date
            )

        messages.success(request, f"Medication '{medication.name}' updated.")
        # Redirect back to the main dashboard
        url = reverse('admins:dashboard') + '#medications'
        return redirect(url)

    # If it's a GET request, show the dedicated edit page
    else:
        return render(request, 'admins/edit_medication.html', {
            'medication': medication
        })

@role_required('admin')
def delete_medication(request, med_id):
    """
    View to delete a medication.
    Shows a confirmation page on GET and performs the deletion on POST.
    """
    medication = get_object_or_404(Medication, id=med_id)
    
    if request.method == 'POST':
        # Capture the name before deletion for the success message
        med_name = medication.name
        medication.delete()
        messages.success(request, f"Medicine '{med_name}' deleted successfully.")
        # Redirect back to the dashboard
        url = reverse('admins:dashboard') + '#medications'
        return redirect(url)
    
    # If it's a GET request, show the confirmation page
    return render(request, 'admins/delete_medication.html', {
        'medication': medication
    })

# -----------------------------
# Billing Views
# -----------------------------
@role_required('admin')
def select_patient_for_billing(request):
    """
    Step 1: Admin selects a patient.
    """
    search_query = request.GET.get('search', '')
    patients = CustomUser.objects.filter(role='patient')
    
    if search_query:
        patients = patients.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page')
    patients_page = paginator.get_page(page_number)

    return render(request, 'admins/select_patient.html', {
        'patients': patients_page,
        'search_query': search_query
    })

@role_required('admin')
def select_appointment_for_billing(request, patient_id):
    """
    Step 2: Admin selects a completed appointment for the chosen patient.
    """
    patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
    
    # Get only COMPLETED appointments for this patient
    appointments = Appointment.objects.filter(
        patient=patient, 
        status='completed'
    ).select_related('doctor', 'schedule').order_by('-schedule__date')

    return render(request, 'admins/select_appointment.html', {
        'patient': patient,
        'appointments': appointments
    })

@role_required('admin')
def finalize_invoice(request, appointment_id):
    """
    Step 3: Admin creates or updates the invoice for the selected appointment.
    """
    # Use select_related to get patient and doctor data in one query
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor'), 
        id=appointment_id
    )

    # Fetch prescriptions and diagnosis notes for this appointment
    from doctors.models import Prescription, DiagnosisNote
    
    prescriptions = Prescription.objects.filter(
        appointment=appointment
    ).select_related('medication')
    
    diagnosis_notes = DiagnosisNote.objects.filter(
        appointment=appointment
    )
    
    # Calculate total prescription cost
    from django.db.models import Sum
    prescription_total = prescriptions.aggregate(
        total=Sum('line_total')
    )['total'] or 0

    try:
        existing_bill = Billing.objects.get(appointment=appointment)
    except Billing.DoesNotExist:
        existing_bill = None

    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')

        if not all([amount, description, due_date]):
            messages.error(request, 'All fields are required.')
        else:
            try:
                bill, created = Billing.objects.update_or_create(
                    appointment=appointment,
                    defaults={
                        'patient': appointment.patient,
                        'amount': amount,
                        'description': description,
                        'due_date': due_date,
                        'is_paid': False,
                        'status': 'pending'
                    }
                )
                
                if created:
                    messages.success(request, f'Invoice created successfully for {appointment.patient.get_full_name()}.')
                else:
                    messages.success(request, f'Invoice for {appointment.patient.get_full_name()} has been updated.')
                return redirect('admins:dashboard') 
                
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')

    initial_amount = existing_bill.amount if existing_bill else prescription_total
    initial_description = existing_bill.description if existing_bill else ""
    initial_due_date = existing_bill.due_date if existing_bill else ""

    suggested_description = f"Consultation fee for {appointment.doctor.get_full_name()} on {appointment.schedule.date}"
    if prescriptions.exists():
        med_names = ", ".join([p.medication.name for p in prescriptions])
        suggested_description += f" + Medications: {med_names}"
    final_description = initial_description or suggested_description

    return render(request, 'admins/finalize_invoice.html', {
        'appointment': appointment,
        'suggested_description': final_description,
        'prescriptions': prescriptions,
        'diagnosis_notes': diagnosis_notes,
        'prescription_total': prescription_total,
        'existing_bill': existing_bill,
        'initial_amount': initial_amount,
        'initial_due_date': initial_due_date,
    })

@role_required('admin')
def all_bills(request):
    """
    View to display all billing records with search and pagination.
    """
    # Start with all bills, ordered by creation date (newest first)
    bills_list = Billing.objects.select_related('patient').order_by('-created_at')

    # Handle Search
    search_query = request.GET.get('search', '')
    if search_query:
        bills_list = bills_list.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__username__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Apply Pagination
    paginator = Paginator(bills_list, 10)
    page_number = request.GET.get('page')
    bills = paginator.get_page(page_number)

    # Pass context to the template
    context = {
        'bills': bills,
        'search_query': search_query,
    }

    return render(request, 'admins/all_bills.html', context)
