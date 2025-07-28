from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/add-diagnosis-note/', views.add_diagnosis_note, name='add_diagnosis_note'),
    path('patients/<int:patient_id>/add-treatment/', views.add_treatment, name='add_treatment'),
    path('appointment-schedule/', views.appointment_schedule, name='appointment_schedule'),
    path('medications/', views.medication_list, name='medication_list'),
    path('patients/<int:patient_id>/add-prescription/', views.add_prescription, name='add_prescription'),
]
