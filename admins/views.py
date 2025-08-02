from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from accounts.models import CustomUser
from .models import Department, Room, Resource, DoctorAllocation
from accounts.utils import role_required
from django.utils.timezone import now
from django.db.models import Count, Sum
from patients.models import Appointment, Billing


@login_required
@role_required('admin')
def dashboard(request):
    today = now().date()
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_doctors = CustomUser.objects.filter(role='doctor').count()
    todays_appointments_count = Appointment.objects.filter(schedule__date=today).count()
    total_revenue = Billing.objects.aggregate(total=Sum('amount'))['total'] or 0

    todays_appointment_status = Appointment.objects.filter(schedule__date=today).values('status').annotate(count=Count('id'))
    todays_financial_overview = Billing.objects.filter(due_date=today).values('is_paid').annotate(count=Count('id'), total_amount=Sum('amount'))

    todays_appointments_list = Appointment.objects.filter(schedule__date=today).select_related('patient', 'doctor', 'schedule')
    departments = Department.objects.all()
    billings = Billing.objects.all()

    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'todays_appointments': todays_appointments_count,
        'total_revenue': total_revenue,
        'todays_appointment_status': todays_appointment_status,
        'todays_financial_overview': todays_financial_overview,
        'todays_appointments_list': todays_appointments_list,
        'departments': departments,
        'billings': billings,
    }
    return render(request, 'admins/dashboard.html', context)


@login_required
@role_required('admin')
def all_appointments(request):
    appointments = Appointment.objects.select_related('patient', 'doctor', 'schedule').order_by('-schedule__date', '-schedule__start_time')
    return render(request, 'admins/all_appointments.html', {'appointments': appointments})


@login_required
@role_required('admin')
def manage_departments(request):
    departments = Department.objects.all()
    return render(request, 'admins/manage_departments.html', {'departments': departments})


@login_required
@role_required('admin')
def user_management_landing(request):
    total_patients = CustomUser.objects.filter(role='patient').count()
    total_doctors = CustomUser.objects.filter(role='doctor').count()
    total_admins = CustomUser.objects.filter(role='admin').count()

    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_admins': total_admins,
    }
    return render(request, 'admins/user_management_landing.html', context)

# Role-based user listing views
@login_required
@role_required('admin')
def list_patients(request):
    patients = CustomUser.objects.filter(role='patient').order_by('username')
    return render(request, 'admins/patients.html', {'users': patients, 'role': 'patient'})

@login_required
@role_required('admin')
def list_doctors(request):
    doctors = CustomUser.objects.filter(role='doctor').order_by('username')
    return render(request, 'admins/doctors.html', {'users': doctors, 'role': 'doctor'})

@login_required
@role_required('admin')
def list_admins(request):
    admins = CustomUser.objects.filter(role='admin').order_by('username')
    return render(request, 'admins/admins.html', {'users': admins, 'role': 'admin'})

@login_required
@role_required('admin')
def manage_users_by_role(request, role):
    if role not in ['patient', 'doctor', 'admin']:
        messages.error(request, 'Invalid user role.')
        return redirect('admins:user_management_landing')

    users = CustomUser.objects.filter(role=role).order_by('username')
    return render(request, 'admins/manage_users_by_role.html', {'users': users, 'role': role})


# ✅ Single, reusable edit_user
@login_required
@role_required('admin')
def edit_patient(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='patient')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient updated successfully.')
            return redirect('admins:list_patients')
    else:
        form = PatientRegistrationForm(instance=user)

    return render(request, 'admins/edit_patient.html', {'form': form, 'user': user})

@login_required
@role_required('admin')
def edit_doctor(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='doctor')

    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()

            # Update doctor-specific schedule and allocation
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

            from doctors.models import DoctorSchedule
            from admins.models import DoctorAllocation

            # Update or create DoctorSchedule
            schedule, created = DoctorSchedule.objects.update_or_create(
                doctor=user,
                defaults={
                    'work_monday': work_monday,
                    'work_tuesday': work_tuesday,
                    'work_wednesday': work_wednesday,
                    'work_thursday': work_thursday,
                    'work_friday': work_friday,
                    'work_saturday': work_saturday,
                    'work_sunday': work_sunday,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )

            # Update or create DoctorAllocation
            allocation, created = DoctorAllocation.objects.update_or_create(
                doctor=user,
                defaults={
                    'department': department,
                    'room': None,
                }
            )

            messages.success(request, 'Doctor updated successfully.')
            return redirect('admins:list_doctors')
    else:
        form = DoctorRegistrationForm(instance=user)

    return render(request, 'admins/edit_doctor.html', {'form': form, 'user': user})

@login_required
@role_required('admin')
def edit_admin(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='admin')

    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin updated successfully.')
            return redirect('admins:list_admins')
    else:
        form = AdminRegistrationForm(instance=user)

    return render(request, 'admins/edit_admin.html', {'form': form, 'user': user})


# ✅ Single, reusable delete_user
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


@login_required
@role_required('admin')
def create_invoice(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')

        if not all([patient_id, amount, due_date]):
            messages.error(request, 'All fields are required.')
        else:
            patient = get_object_or_404(CustomUser, id=patient_id, role='patient')
            Billing.objects.create(
                patient=patient,
                amount=amount,
                due_date=due_date,
                is_paid=False
            )
            messages.success(request, 'Invoice created successfully.')
            return redirect('admins:dashboard')

    patients = CustomUser.objects.filter(role='patient')
    return render(request, 'admins/create_invoice.html', {'patients': patients})


@login_required
@role_required('admin')
def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Department.objects.create(name=name, description=description)
            messages.success(request, 'Department added successfully.')
            return redirect('admins:manage_departments')
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
            return redirect('admins:manage_departments')  # Always redirect to list
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
        return redirect('admins:manage_departments')
    return render(request, 'admins/delete_department.html', {'department': department})


@login_required
@role_required('admin')
def manage_rooms(request):
    rooms = Room.objects.select_related('department').all()
    return render(request, 'admins/manage_rooms.html', {'rooms': rooms})


@login_required
@role_required('admin')
def add_room(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        department_id = request.POST.get('department')
        room_number = request.POST.get('room_number')
        capacity = request.POST.get('capacity')

        if all([department_id, room_number, capacity]):
            department = get_object_or_404(Department, id=department_id)
            Room.objects.create(
                department=department,
                room_number=room_number,
                capacity=capacity
            )
            messages.success(request, 'Room added successfully.')
            return redirect('admins:manage_rooms')
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admins/add_room.html', {'departments': departments})


@login_required
@role_required('admin')
def manage_resources(request):
    resources = Resource.objects.all()
    return render(request, 'admins/manage_resources.html', {'resources': resources})


@login_required
@role_required('admin')
def add_resource(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')

        if name and quantity:
            Resource.objects.create(
                name=name,
                description=description,
                quantity=quantity
            )
            messages.success(request, 'Resource added successfully.')
            return redirect('admins:manage_resources')
        else:
            messages.error(request, 'Name and quantity are required.')

    return render(request, 'admins/add_resource.html')


@login_required
@role_required('admin')
def manage_doctor_allocations(request):
    allocations = DoctorAllocation.objects.select_related('doctor', 'department', 'room').all()
    return render(request, 'admins/manage_doctor_allocations.html', {'allocations': allocations})


@login_required
@role_required('admin')
def add_doctor_allocation(request):
    doctors = CustomUser.objects.filter(role='doctor')
    departments = Department.objects.all()
    rooms = Room.objects.all()

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        department_id = request.POST.get('department')
        room_id = request.POST.get('room')

        if not doctor_id or not department_id:
            messages.error(request, 'Doctor and department are required.')
        else:
            doctor = get_object_or_404(CustomUser, id=doctor_id)
            department = get_object_or_404(Department, id=department_id)
            room = get_object_or_404(Room, id=room_id) if room_id else None

            DoctorAllocation.objects.create(
                doctor=doctor,
                department=department,
                room=room
            )
            messages.success(request, 'Doctor allocation added successfully.')
            return redirect('admins:manage_doctor_allocations')

    return render(request, 'admins/add_doctor_allocation.html', {
        'doctors': doctors,
        'departments': departments,
        'rooms': rooms
    })


# ✅ New: Add user (kept clean)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from accounts.models import CustomUser
from .models import Department, Room, Resource, DoctorAllocation
from accounts.utils import role_required
from django.utils.timezone import now
from django.db.models import Count, Sum
from patients.models import Appointment, Billing
from accounts.forms import PatientRegistrationForm, DoctorRegistrationForm, AdminRegistrationForm

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

            from doctors.models import DoctorSchedule
            from admins.models import DoctorAllocation

            DoctorSchedule.objects.create(
                doctor=user,
                work_monday=work_monday,
                work_tuesday=work_tuesday,
                work_wednesday=work_wednesday,
                work_thursday=work_thursday,
                work_friday=work_friday,
                work_saturday=work_saturday,
                work_sunday=work_sunday,
                start_time=start_time,
                end_time=end_time
            )

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


# ✅ Reset password (cleaned)
@login_required
@role_required('admin')
def reset_user_password(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successfully.')
            return redirect('admins:manage_users_by_role', role=user.role)
        else:
            messages.error(request, 'New password is required.')
    return render(request, 'admins/reset_user_password.html', {'user': user})