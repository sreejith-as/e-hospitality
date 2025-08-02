from django import forms
from .models import DoctorSchedule
from admins.models import Department
from accounts.models import CustomUser

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

class DoctorProfileUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    work_monday = forms.BooleanField(required=False)
    work_tuesday = forms.BooleanField(required=False)
    work_wednesday = forms.BooleanField(required=False)
    work_thursday = forms.BooleanField(required=False)
    work_friday = forms.BooleanField(required=False)
    work_saturday = forms.BooleanField(required=False)
    work_sunday = forms.BooleanField(required=False)
    start_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}), required=True)
    end_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}), required=True)
