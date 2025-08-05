from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = 'patients'

urlpatterns = [
    path('overview/', views.overview, name='overview'),
    path('appointments/', views.appointments, name='appointments'),
    path('medical-records/', views.medical_records, name='medical_records'),
    path('prescriptions/', views.prescriptions, name='prescriptions'),
    path('billing/', views.billing, name='billing'),
    path('pay-bill/<int:billing_id>/', views.pay_bill, name='pay_bill'),
    path('health-education/', views.health_education, name='health_education'),
    path('download-medical-history-pdf/', views.download_medical_history_pdf, name='download_medical_history_pdf'),
    path('download-prescription-pdf/<int:prescription_id>/', views.download_prescription_pdf, name='download_prescription_pdf'),
    path('visit-detail/<int:appointment_id>/', views.visit_detail, name='visit_detail'),
    path('download-visit-pdf/<int:appointment_id>/', views.download_visit_pdf, name='download_visit_pdf'),
    path('book-appointment-form/', views.book_appointment_form, name='book_appointment_form'),
    path('doctor-schedule/', views.view_doctors_schedule, name='view_doctors_schedule'),
    path('book-appointment/<int:schedule_id>/', views.book_appointment, name='book_appointment'),
    path('get_doctors_by_department/', views.get_doctors_by_department, name='get_doctors_by_department'),
    path('get_available_time_slots/', views.get_available_time_slots, name='get_available_time_slots'),
    path('dashboard/', RedirectView.as_view(url='/patients/overview/', permanent=True), name='dashboard_redirect'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('edit-appointment/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
]
