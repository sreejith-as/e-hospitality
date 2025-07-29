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
    path('book-appointment-form/', views.book_appointment_form, name='book_appointment_form'),
    path('doctor-schedule/', views.view_doctors_schedule, name='view_doctors_schedule'),
    path('book-appointment/<int:schedule_id>/', views.book_appointment, name='book_appointment'),
    path('dashboard/', RedirectView.as_view(url='/patients/overview/', permanent=True), name='dashboard_redirect'),
]
