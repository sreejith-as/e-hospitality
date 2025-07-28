from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('all-appointments/', views.all_appointments, name='all_appointments'),
    path('manage-departments/', views.manage_departments, name='manage_departments'),
    path('add-department/', views.add_department, name='add_department'),
    path('edit-department/<int:department_id>/', views.edit_department, name='edit_department'),
    path('delete-department/<int:department_id>/', views.delete_department, name='delete_department'),
    path('resources/add/', views.add_resource, name='add_resource'),
    path('doctor-allocations/', views.manage_doctor_allocations, name='manage_doctor_allocations'),
    path('doctor-allocations/add/', views.add_doctor_allocation, name='add_doctor_allocation'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/reset-password/<int:user_id>/', views.reset_user_password, name='reset_user_password'),
    path('create-invoice/', views.create_invoice, name='create_invoice'),
]
