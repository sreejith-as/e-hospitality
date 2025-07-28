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
