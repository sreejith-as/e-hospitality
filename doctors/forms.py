# doctors/forms.py
from django import forms
from .models import DoctorAvailability, Prescription
from admins.models import Department
from accounts.models import CustomUser
from .models import Medication

# -----------------------------
# Form for Doctor Availability (replaces DoctorScheduleForm)
# -----------------------------
class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['day_of_week'].label = "Day of Week"
        self.fields['start_time'].label = "Start Time"
        self.fields['end_time'].label = "End Time"


# -----------------------------
# Formset for managing all weekly availability
# -----------------------------
DoctorAvailabilityFormSet = forms.inlineformset_factory(
    CustomUser,
    DoctorAvailability,
    form=DoctorAvailabilityForm,
    fields=['day_of_week', 'start_time', 'end_time'],
    extra=7,
    can_delete=True,
    min_num=0,
    validate_min=False
)


# -----------------------------
# Doctor Profile Update Form
# -----------------------------
class DoctorProfileUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=True
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        label="Department"
    )

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['first_name'].initial = doctor.first_name
            self.fields['last_name'].initial = doctor.last_name
            self.fields['email'].initial = doctor.email
            self.fields['phone_number'].initial = doctor.phone_number
            self.fields['gender'].initial = doctor.gender
            if hasattr(doctor, 'doctorallocation'):
                self.fields['department'].initial = doctor.doctorallocation.department


# -----------------------------
# New: Doctor Availability Simple Form
# -----------------------------
from django.forms.widgets import TimeInput, CheckboxSelectMultiple
from django import forms

class DoctorAvailabilitySimpleForm(forms.Form):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    working_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=CheckboxSelectMultiple,
        required=False,
        label="Working Days"
    )
    start_time = forms.TimeField(
        widget=TimeInput(format='%I:%M %p', attrs={'type': 'time'}),
        label="Start Time"
    )
    end_time = forms.TimeField(
        widget=TimeInput(format='%I:%M %p', attrs={'type': 'time'}),
        label="End Time"
    )


# -----------------------------
# Prescription Form
# -----------------------------
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medication', 'dosage', 'instructions']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }

class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'description', 'safety_warnings', 'price', 'unit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'safety_warnings': forms.Textarea(attrs={'rows': 2}),
        }