from django.contrib import admin
from admins.models import DoctorAllocation
from .models import DoctorSchedule

@admin.register(DoctorAllocation)
class DoctorAllocationAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'department', 'room', 'allocated_at')
    list_filter = ('department',)
    search_fields = ('doctor__username', 'department__name')

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'work_days', 'start_time', 'end_time')
    search_fields = ('doctor__username',)

    def work_days(self, obj):
        days = []
        if obj.work_monday:
            days.append('Mon')
        if obj.work_tuesday:
            days.append('Tue')
        if obj.work_wednesday:
            days.append('Wed')
        if obj.work_thursday:
            days.append('Thu')
        if obj.work_friday:
            days.append('Fri')
        if obj.work_saturday:
            days.append('Sat')
        if obj.work_sunday:
            days.append('Sun')
        return ', '.join(days)
    work_days.short_description = 'Working Days'
