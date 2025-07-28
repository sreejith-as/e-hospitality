from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from accounts.models import CustomUser
from .models import Department, Room, Resource, DoctorAllocation
from accounts.utils import role_required

@login_required
@role_required('admin')
def dashboard(request):
    return render(request, 'admins/dashboard.html')

@login_required
@role_required('admin')
def manage_departments(request):
    departments = Department.objects.all()
    return render(request, 'admins/manage_departments.html', {'departments': departments})

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
def manage_rooms(request):
    rooms = Room.objects.select_related('department').all()
    return render(request, 'admins/manage_rooms.html', {'rooms': rooms})

@login_required
@role_required('admin')
def add_room(request):
    from .models import Department
    departments = Department.objects.all()
    if request.method == 'POST':
        department_id = request.POST.get('department')
        room_number = request.POST.get('room_number')
        capacity = request.POST.get('capacity')
        if department_id and room_number and capacity:
            department = get_object_or_404(Department, id=department_id)
            Room.objects.create(department=department, room_number=room_number, capacity=capacity)
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
            Resource.objects.create(name=name, description=description, quantity=quantity)
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
        if doctor_id and department_id:
            doctor = get_object_or_404(CustomUser, id=doctor_id)
            department = get_object_or_404(Department, id=department_id)
            room = get_object_or_404(Room, id=room_id) if room_id else None
            DoctorAllocation.objects.create(doctor=doctor, department=department, room=room)
            messages.success(request, 'Doctor allocation added successfully.')
            return redirect('admins:manage_doctor_allocations')
        else:
            messages.error(request, 'Doctor and department are required.')
    return render(request, 'admins/add_doctor_allocation.html', {'doctors': doctors, 'departments': departments, 'rooms': rooms})

@login_required
@role_required('admin')
def manage_users(request):
    users = CustomUser.objects.filter(role__in=['doctor', 'patient']).order_by('role', 'username')
    return render(request, 'admins/manage_users.html', {'users': users})

@login_required
@role_required('admin')
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        if username and email and role and password:
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            else:
                user = CustomUser.objects.create_user(username=username, email=email, password=password, role=role)
                messages.success(request, f'{role.capitalize()} user created successfully.')
                return redirect('admins:manage_users')
        else:
            messages.error(request, 'All fields are required.')
    return render(request, 'admins/add_user.html')

@login_required
@role_required('admin')
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        if email and role:
            user.email = email
            user.role = role
            user.save()
            messages.success(request, 'User updated successfully.')
            return redirect('admins:manage_users')
        else:
            messages.error(request, 'Email and role are required.')
    return render(request, 'admins/edit_user.html', {'user': user})

@login_required
@role_required('admin')
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('admins:manage_users')
    return render(request, 'admins/delete_user.html', {'user': user})

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
            return redirect('admins:manage_users')
        else:
            messages.error(request, 'New password is required.')
    return render(request, 'admins/reset_user_password.html', {'user': user})
