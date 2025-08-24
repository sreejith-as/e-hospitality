from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('patient_detail/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('todays-appointments/', views.todays_appointments, name='todays_appointments'),
    path('appointment-schedule/', views.appointment_schedule, name='appointment_schedule'),

    # Upcoming appointments
    path('upcoming-appointments/', views.upcoming_appointments, name='upcoming_appointments'),

    # Appointment details view (read-only)
    path('appointments/<int:appointment_id>/', views.appointment_details, name='appointment_details'),
    
    # Appointment details update view
    path('search-medicine/', views.search_medicine, name='search_medicine'),
    path('appointments/<int:appointment_id>/update/', views.appointment_details_update, name='appointment_details_update'),

    # Bills
    path('bills/', views.all_bills, name='all_bills'),
    path('bills/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bills/<int:bill_id>/edit/', views.bill_edit, name='bill_edit'),
]
