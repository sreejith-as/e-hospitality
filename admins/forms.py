from django import forms
from django.contrib.auth.forms import UserChangeForm
from accounts.models import CustomUser
from admins.models import Department, DoctorAllocation, HealthArticle
from doctors.models import DoctorAvailability

class PatientEditForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'})
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth']

class DoctorEditForm(forms.ModelForm):
    # --- Basic User Fields (from CustomUser) ---
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'})
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )

    # --- Doctor-Specific Fields ---
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the department this doctor belongs to."
    )

    # --- Working Days (Derived from DoctorAvailability model) ---
    WORK_DAYS_CHOICES = [
        ('work_monday', 'Monday'),
        ('work_tuesday', 'Tuesday'),
        ('work_wednesday', 'Wednesday'),
        ('work_thursday', 'Thursday'),
        ('work_friday', 'Friday'),
        ('work_saturday', 'Saturday'),
        ('work_sunday', 'Sunday'),
    ]

    # Create BooleanFields for each working day
    work_monday = forms.BooleanField(required=False, label='Monday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_tuesday = forms.BooleanField(required=False, label='Tuesday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_wednesday = forms.BooleanField(required=False, label='Wednesday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_thursday = forms.BooleanField(required=False, label='Thursday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_friday = forms.BooleanField(required=False, label='Friday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_saturday = forms.BooleanField(required=False, label='Saturday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    work_sunday = forms.BooleanField(required=False, label='Sunday', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    # --- Working Hours (Common for selected days) ---
    start_time = forms.TimeField(
        required=False, # Make optional, validation can enforce if days are selected
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text='Working start time (applies to selected days)'
    )
    end_time = forms.TimeField(
        required=False, # Make optional, validation can enforce if days are selected
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text='Working end time (applies to selected days)'
    )

    class Meta:
        model = CustomUser
        # Include all relevant fields from CustomUser and the added doctor-specific fields
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth']

    def __init__(self, *args, **kwargs):
        # Pop the 'user' instance if passed explicitly (optional, but useful for clarity)
        # user_instance = kwargs.pop('user', None) # Not strictly needed if using instance correctly

        # Call the parent's __init__ to initialize the form
        super().__init__(*args, **kwargs)

        # --- Pre-population Logic for Editing ---
        if self.instance and self.instance.pk:  # Check if we are editing an existing user
            # 1. Pre-populate CustomUser fields (handled automatically by ModelForm if fields match)
            #    But we set initial values explicitly to ensure they are correct.
            self.fields['username'].initial = self.instance.username
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email
            self.fields['phone_number'].initial = self.instance.phone_number
            self.fields['gender'].initial = self.instance.gender
            if self.instance.date_of_birth:
                 self.fields['date_of_birth'].initial = self.instance.date_of_birth

            # 2. Pre-populate Department
            try:
                # Get the DoctorAllocation for this doctor
                allocation = self.instance.doctorallocation_set.first() # Assumes OneToOne or gets the first
                if allocation:
                    self.fields['department'].initial = allocation.department
            except Exception as e:
                # Handle potential issues fetching allocation
                print(f"Error fetching department allocation for user {self.instance.pk}: {e}")
                # Consider adding a user message or logging


            # 3. Pre-populate Working Days and Hours
            try:
                # Fetch existing availabilities for this doctor user
                availabilities = DoctorAvailability.objects.filter(doctor=self.instance)

                # Create a map from day_of_week code to True
                day_map = {avail.day_of_week: True for avail in availabilities}

                # Set initial values for working day checkboxes
                self.fields['work_monday'].initial = day_map.get('mon', False)
                self.fields['work_tuesday'].initial = day_map.get('tue', False)
                self.fields['work_wednesday'].initial = day_map.get('wed', False)
                self.fields['work_thursday'].initial = day_map.get('thu', False)
                self.fields['work_friday'].initial = day_map.get('fri', False)
                self.fields['work_saturday'].initial = day_map.get('sat', False)
                self.fields['work_sunday'].initial = day_map.get('sun', False)

                # Pre-populate common start/end time if availabilities exist
                # This assumes all selected days have the *same* hours.
                # If not, this logic needs adjustment (e.g., store in form or show message).
                if availabilities.exists():
                     # Get times from the first availability record as an example
                     first_avail = availabilities.first()
                     self.fields['start_time'].initial = first_avail.start_time
                     self.fields['end_time'].initial = first_avail.end_time

            except Exception as e:
                # Handle potential errors during availability lookup
                print(f"Error pre-populating doctor availability in form for user {self.instance.pk}: {e}")
                # Consider adding a user message or logging

    def clean(self):
        """
        Custom validation to ensure working days and times are consistent.
        """
        cleaned_data = super().clean()
        # Collect selected working days
        selected_days = [
            day_key for day_key, _ in self.WORK_DAYS_CHOICES
            if cleaned_data.get(day_key)
        ]
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # Validate: If any day is selected, start and end times must be provided.
        if selected_days and (not start_time or not end_time):
            raise forms.ValidationError("Please provide both start time and end time if selecting working days.")

        # Optional: Validate start_time < end_time
        if start_time and end_time and start_time >= end_time:
             raise forms.ValidationError("End time must be after start time.")

        # Optional: Validate that at least one day is selected if times are provided?
        # if (start_time or end_time) and not selected_days:
        #     raise forms.ValidationError("Please select at least one working day if providing times.")

        return cleaned_data

    def save(self, commit=True):
        """
        Override the save method to handle saving the related DoctorAllocation
        and DoctorAvailability records.
        """
        # Save the CustomUser instance first (if commit=True)
        user = super().save(commit=commit)

        if commit:
            # 1. Save DoctorAllocation
            department = self.cleaned_data.get('department')
            if department:
                # Use update_or_create to handle existing allocations
                DoctorAllocation.objects.update_or_create(
                    doctor=user,
                    defaults={'department': department}
                    # Room is handled elsewhere or assumed null for now
                )

            # 2. Save DoctorAvailability
            # Get selected days and times from cleaned_data
            selected_days_map = {
                'work_monday': 'mon',
                'work_tuesday': 'tue',
                'work_wednesday': 'wed',
                'work_thursday': 'thu',
                'work_friday': 'fri',
                'work_saturday': 'sat',
                'work_sunday': 'sun',
            }
            start_time = self.cleaned_data.get('start_time')
            end_time = self.cleaned_data.get('end_time')

            # Prepare list of days to be saved
            days_to_save = [
                day_code for form_day, day_code in selected_days_map.items()
                if self.cleaned_data.get(form_day)
            ]

            # Delete existing availabilities for this doctor (simpler than update logic)
            # This assumes the form represents the *complete* set of availabilities.
            DoctorAvailability.objects.filter(doctor=user).delete()

            # Create new DoctorAvailability records for selected days
            availability_objects = [
                DoctorAvailability(
                    doctor=user,
                    day_of_week=day_code,
                    start_time=start_time,
                    end_time=end_time
                )
                for day_code in days_to_save
                if start_time and end_time # Only create if times are provided
            ]
            if availability_objects:
                DoctorAvailability.objects.bulk_create(availability_objects)

        # Return the saved user instance
        return user

class AdminEditForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'})
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth']

class HealthArticleForm(forms.ModelForm):
    """
    Form for admins to create and edit health education articles.
    """
    class Meta:
        model = HealthArticle
        fields = ['title', 'content',]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a compelling title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Write your health education article here...'
            }),
        }

