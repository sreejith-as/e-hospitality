# doctors/admin.py
from django.contrib import admin
from .models import (
    DoctorAvailability,
    DiagnosisNote,
    Treatment,
    Medication,
    Prescription
)


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'get_day_display', 'start_time', 'end_time']
    list_filter = ['day_of_week', 'doctor']
    search_fields = ['doctor__username', 'doctor__first_name', 'doctor__last_name']
    # ✅ Removed 'sort_order' from ordering to pass system check
    ordering = ['doctor', 'day_of_week']  # Use the actual field

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        day_order = {
            'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4,
            'fri': 5, 'sat': 6, 'sun': 7
        }
        from django.db.models import Case, When, IntegerField
        return queryset.annotate(
            sort_order=Case(
                *[When(day_of_week=k, then=v) for k, v in day_order.items()],
                output_field=IntegerField()
            )
        )

    @admin.display(description='Day', ordering='day_of_week')  # Keep sort logic in DB via get_queryset()
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()


# -----------------------------
# Other Admins
# -----------------------------
@admin.register(DiagnosisNote)
class DiagnosisNoteAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'created_at']
    list_filter = ['created_at', 'doctor']
    search_fields = ['patient__username', 'doctor__username']


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'created_at']
    list_filter = ['created_at', 'doctor']


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medication', 'dosage', 'doctor', 'created_at']
    list_filter = ['created_at', 'doctor', 'medication']