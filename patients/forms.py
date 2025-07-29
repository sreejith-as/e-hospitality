from django import forms
from .models import Appointment, DoctorSchedule
from django.contrib.auth import get_user_model

User = get_user_model()

class AppointmentBookingForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(queryset=User.objects.filter(role='doctor'), required=True)
    date = forms.DateField(widget=forms.SelectDateWidget)
    time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), required=True)
    symptoms = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'symptoms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].label = "Select Doctor"
        self.fields['date'].label = "Select Date"
        self.fields['time'].label = "Select Time"
        self.fields['symptoms'].label = "Describe your symptoms"

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if doctor and date and time:
            # Check if doctor has schedule on that date and time
            if not DoctorSchedule.objects.filter(doctor=doctor, date=date, start_time=time).exists():
                raise forms.ValidationError(f"Doctor {doctor.username} is not available on {date} at {time}. Please choose another time, date, or doctor.")
        return cleaned_data
