# patients/forms.py
from django import forms
from .models import Appointment
from django.contrib.auth import get_user_model
from admins.models import Department

User = get_user_model()

from django import forms
from .models import Appointment
from django.contrib.auth import get_user_model
from admins.models import Department

User = get_user_model()

class AppointmentBookingForm(forms.ModelForm):
    department = forms.ChoiceField(choices=[], required=True)
    doctor = forms.ModelChoiceField(queryset=User.objects.none(), required=True)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=True)
    symptoms = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta:
        model = Appointment
        fields = ['department', 'doctor', 'date', 'time', 'symptoms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate departments
        self.fields['department'].choices = [('', 'Select Department')] + [
            (dept.id, dept.name) for dept in Department.objects.all()
        ]
        self.fields['department'].label = "Department"
        self.fields['doctor'].label = "Doctor"
        self.fields['date'].label = "Date"
        self.fields['time'].label = "Time Slot"
        self.fields['symptoms'].label = "Symptoms (Optional)"

        # If doctor is passed via GET or session, limit queryset
        if 'department' in self.data:
            dept_id = self.data.get('department')
            self.fields['doctor'].queryset = User.objects.filter(
                role='doctor',
                doctorallocation__department_id=dept_id
            ).distinct()
        elif self.is_bound:
            self.fields['doctor'].queryset = User.objects.none()
        else:
            self.fields['doctor'].queryset = User.objects.filter(role='doctor')

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time_obj = cleaned_data.get('time')

        if doctor and date and time_obj:
            from doctors.models import DoctorAvailability
            from django.utils import timezone
            from datetime import timedelta
            
            # Get the day of week for the selected date
            day_of_week_short = date.strftime('%a').lower()  # e.g., 'mon', 'tue'
            
            try:
                availability = DoctorAvailability.objects.get(doctor=doctor, day_of_week=day_of_week_short)
            except DoctorAvailability.DoesNotExist:
                raise forms.ValidationError("Doctor is not available on the selected date.")
            
            # Check if the time is within the doctor's working hours
            if time_obj < availability.start_time or time_obj >= availability.end_time:
                raise forms.ValidationError("Selected time is outside the doctor's working hours.")
            
            # Check if there's already an appointment at this time
            from patients.models import TimeSlot, Appointment
            try:
                time_slot = TimeSlot.objects.get(
                    doctor=doctor,
                    date=date,
                    start_time=time_obj
                )
                if Appointment.objects.filter(schedule=time_slot, status='booked').exists():
                    raise forms.ValidationError("This time slot is already booked.")
            except TimeSlot.DoesNotExist:
                # This is expected for new appointments - TimeSlot will be created in the view
                pass
                
        return cleaned_data
