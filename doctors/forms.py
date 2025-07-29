from django import forms
from .models import DoctorSchedule

class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = [
            'work_monday',
            'work_tuesday',
            'work_wednesday',
            'work_thursday',
            'work_friday',
            'work_saturday',
            'work_sunday',
            'start_time',
            'end_time',
        ]
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }
