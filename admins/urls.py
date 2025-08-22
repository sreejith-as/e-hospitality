from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    #profile
    path('profile/update/', views.update_admin_profile, name='update_admin_profile'),
    
    # Appointment Detail
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('all-appointments/', views.all_appointments, name='all_appointments'),

    # Department Management
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('add-department/', views.add_department, name='add_department'),
    path('edit-department/<int:department_id>/', views.edit_department, name='edit_department'),
    path('delete-department/<int:department_id>/', views.delete_department, name='delete_department'),

    # Doctor Allocation
    path('doctor-allocations/', views.manage_doctor_allocations, name='manage_doctor_allocations'),
    path('doctor-allocations/add/', views.add_doctor_allocation, name='add_doctor_allocation'),

    # Role-based user listing pages
    path('patients/', views.list_patients, name='list_patients'),
    path('doctors/', views.list_doctors, name='list_doctors'),
    path('admins/', views.list_admins, name='list_admins'),

    # Role-based add user pages
    path('add-patients/', views.add_patient, name='add_patient'),
    path('add-doctors/', views.add_doctor, name='add_doctor'),
    path('add-admins/', views.add_admin, name='add_admin'),

    # Role-based edit user pages
    path('edit-patient/<int:user_id>/', views.edit_patient, name='edit_patient'),
    path('edit-doctor/<int:user_id>/', views.edit_doctor, name='edit_doctor'),
    path('edit-admin/<int:user_id>/', views.edit_admin, name='edit_admin'),

    # Role-based delete user pages
    path('delete-patient/<int:user_id>/', views.delete_patient, name='delete_patient'),
    path('delete-doctor/<int:user_id>/', views.delete_doctor, name='delete_doctor'),
    path('delete-admin/<int:user_id>/', views.delete_admin, name='delete_admin'),

    # Role-based reset password pages
    path('patients/reset-password/<int:user_id>/', views.reset_user_password, name='reset_patient_password'),
    path('doctors/reset-password/<int:user_id>/', views.reset_user_password, name='reset_doctor_password'),
    path('admins/reset-password/<int:user_id>/', views.reset_user_password, name='reset_admin_password'),

    # Financial
    path('create-invoice/', views.select_patient_for_billing, name='select_patient_for_billing'),
    path('create-invoice/<int:patient_id>/select-appointment/', views.select_appointment_for_billing, name='select_appointment_for_billing'),
    path('create-invoice/<int:appointment_id>/finalize/', views.finalize_invoice, name='finalize_invoice'),
    path('all-bills/', views.all_bills, name='all_bills'),

    # medicine
    path('add-medication/', views.add_medication, name='add_medication'),
    path('medications/edit/<int:med_id>/', views.edit_medication, name='edit_medication'),
    path('medications/delete/<int:med_id>/', views.delete_medication, name='delete_medication'),
]