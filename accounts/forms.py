from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from admins.models import Department

# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser

class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
        help_text='First name'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
        help_text='Last name'
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        help_text='Email address'
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
        help_text='Phone number'
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select your gender'
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd-mm-yyyy'}),
        help_text='Date of birth'
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username'}),
        help_text='Username (letters, digits, @, ., +, -, _ only)'
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a strong password'}),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        help_text='Confirm your password'
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'gender',
            'date_of_birth',
            'password1',
            'password2'
        )

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

class PatientProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'gender',
            'date_of_birth',
            'address',
            'profile_picture',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }