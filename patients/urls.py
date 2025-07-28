from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('doctor-schedule/', views.view_doctors_schedule, name='view_doctors_schedule'),
    path('book-appointment/<int:schedule_id>/', views.book_appointment, name='book_appointment'),
    path('medical-history/', views.view_medical_history, name='view_medical_history'),
    path('billing/', views.view_billing, name='view_billing'),
    path('pay-bill/<int:billing_id>/', views.pay_bill, name='pay_bill'),
    path('health-education/', views.health_education, name='health_education'),
]
