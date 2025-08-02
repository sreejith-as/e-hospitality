from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('all-appointments/', views.all_appointments, name='all_appointments'),
    
    # Department Management
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('add-department/', views.add_department, name='add_department'),
    path('edit-department/<int:department_id>/', views.edit_department, name='edit_department'),
    path('delete-department/<int:department_id>/', views.delete_department, name='delete_department'),

    # Room Management
    path('manage-rooms/', views.manage_rooms, name='manage_rooms'),
    path('add-room/', views.add_room, name='add_room'),

    # Resource Management
    path('manage-resources/', views.manage_resources, name='manage_resources'),  # ✅ Added missing URL
    path('resources/add/', views.add_resource, name='add_resource'),

    # Doctor Allocation
    path('doctor-allocations/', views.manage_doctor_allocations, name='manage_doctor_allocations'),
    path('doctor-allocations/add/', views.add_doctor_allocation, name='add_doctor_allocation'),

    # User Management
    path('users/', views.user_management_landing, name='user_management_landing'),

    # Role-based user listing pages
    path('patients/', views.list_patients, name='list_patients'),
    path('doctors/', views.list_doctors, name='list_doctors'),
    path('admins/', views.list_admins, name='list_admins'),

    # Role-based add user pages
    path('patients/add/', views.add_patient, name='add_patient'),
    path('doctors/add/', views.add_doctor, name='add_doctor'),
    path('admins/add/', views.add_admin, name='add_admin'),

    # Role-based edit user pages
    path('patients/edit/<int:user_id>/', views.edit_patient, name='edit_patient'),
    path('doctors/edit/<int:user_id>/', views.edit_doctor, name='edit_doctor'),
    path('admins/edit/<int:user_id>/', views.edit_admin, name='edit_admin'),

    # Role-based delete user pages
    path('patients/delete/<int:user_id>/', views.delete_patient, name='delete_patient'),
    path('doctors/delete/<int:user_id>/', views.delete_doctor, name='delete_doctor'),
    path('admins/delete/<int:user_id>/', views.delete_admin, name='delete_admin'),

    # Role-based reset password pages
    path('patients/reset-password/<int:user_id>/', views.reset_user_password, name='reset_patient_password'),
    path('doctors/reset-password/<int:user_id>/', views.reset_user_password, name='reset_doctor_password'),
    path('admins/reset-password/<int:user_id>/', views.reset_user_password, name='reset_admin_password'),

    # Financial
    path('create-invoice/', views.create_invoice, name='create_invoice'),
]