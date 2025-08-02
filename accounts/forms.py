from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser

class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='First name')
    last_name = forms.CharField(max_length=30, required=True, help_text='Last name')
    email = forms.EmailField(max_length=254, required=True, help_text='Email address')
    phone_number = forms.CharField(max_length=15, required=True, help_text='Phone number')
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth', 'password1', 'password2')

from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from admins.models import Department

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='First name')
    last_name = forms.CharField(max_length=30, required=True, help_text='Last name')
    email = forms.EmailField(max_length=254, required=True, help_text='Email address')
    phone_number = forms.CharField(max_length=15, required=True, help_text='Phone number')
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    work_monday = forms.BooleanField(required=False)
    work_tuesday = forms.BooleanField(required=False)
    work_wednesday = forms.BooleanField(required=False)
    work_thursday = forms.BooleanField(required=False)
    work_friday = forms.BooleanField(required=False)
    work_saturday = forms.BooleanField(required=False)
    work_sunday = forms.BooleanField(required=False)
    start_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth', 'department', 'work_monday', 'work_tuesday', 'work_wednesday', 'work_thursday', 'work_friday', 'work_saturday', 'work_sunday', 'start_time', 'end_time', 'password1', 'password2')

class AdminRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='First name')
    last_name = forms.CharField(max_length=30, required=True, help_text='Last name')
    email = forms.EmailField(max_length=254, required=True, help_text='Email address')
    phone_number = forms.CharField(max_length=15, required=True, help_text='Phone number')
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    # Add any admin-specific fields here if needed

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth', 'password1', 'password2')
