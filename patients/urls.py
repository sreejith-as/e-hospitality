from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = 'patients'

urlpatterns = [
    # Main Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Edit Profile
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    # Redirect old standalone pages to dashboard with correct tab
    path('medical-records/', RedirectView.as_view(url='/patients/dashboard/#medical-records', permanent=True)),
    path('prescriptions/', RedirectView.as_view(url='/patients/dashboard/#prescriptions', permanent=True)),
    path('billing/', RedirectView.as_view(url='/patients/dashboard/#billing', permanent=True)),

    # Booking & Appointments
    path('appointments/', views.appointments, name='appointments'),
    path('book-appointment-form/', views.book_appointment_form, name='book_appointment_form'),
    path('doctor-schedule/', views.view_doctors_schedule, name='view_doctors_schedule'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('edit-appointment/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),

    # Medical Record
    path('medical-record/<int:appointment_id>/', views.medical_record_detail, name='medical_record_detail'),
    
    # Billing
    path('pay-bill/<int:billing_id>/', views.pay_bill, name='pay_bill'),

    # Health & Education
    path('health-article/<int:article_id>/', views.view_health_article, name='view_health_article'),

    # PDF Downloads
    path('download-medical-history-pdf/', views.download_medical_history_pdf, name='download_medical_history_pdf'),
    path('download-prescription-pdf/<int:prescription_id>/', views.download_prescription_pdf, name='download_prescription_pdf'),
    path('visit-detail/<int:appointment_id>/', views.visit_detail, name='visit_detail'),
    path('download-visit-pdf/<int:appointment_id>/', views.download_visit_pdf, name='download_visit_pdf'),

    # AJAX
    path('get_doctors_by_department/', views.get_doctors_by_department, name='get_doctors_by_department'),
    path('get_available_time_slots/', views.get_available_time_slots, name='get_available_time_slots'),
    path('get_doctor_schedule/', views.get_doctor_schedule, name='get_doctor_schedule'),

    # Payment
    path('payment-success/', views.payment_success, name='payment_success'),

    # Dashboard Redirect (Root for patients)
    path('', RedirectView.as_view(url='/patients/dashboard/', permanent=True), name='dashboard'),
]