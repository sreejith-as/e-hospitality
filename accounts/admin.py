from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import CustomUser
from admins.models import DoctorAllocation
from doctors.models import DoctorAvailability  # Replaced DoctorSchedule with DoctorAvailability


# -----------------------------
# Inline: Doctor Allocation
# -----------------------------
class DoctorAllocationInline(admin.StackedInline):
    model = DoctorAllocation
    can_delete = False
    verbose_name_plural = 'Doctor Allocation'
    fields = ('department', 'room')
    extra = 0

    def has_change_permission(self, request, obj=None):
        return True


# -----------------------------
# Inline: Doctor Availability (Weekly Working Hours)
# -----------------------------
class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    can_delete = True
    verbose_name = "Working Day"
    verbose_name_plural = 'Working Hours & Availability'
    fields = ('day_of_week', 'start_time', 'end_time')
    extra = 0
    min_num = 1
    max_num = 7

    def has_change_permission(self, request, obj=None):
        return True


# -----------------------------
# Custom User Admin
# -----------------------------
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'gender')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth')
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_staff', 'is_active', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'role', 'is_staff', 'is_active'
            ),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined')

    def get_inline_instances(self, request, obj=None):
        """
        Show inlines only for doctor users
        """
        if obj and obj.role == 'doctor':
            return [
                DoctorAllocationInline(self.model, self.admin_site),
                DoctorAvailabilityInline(self.model, self.admin_site)
            ]
        return []

    def get_fieldsets(self, request, obj=None):
        return super().get_fieldsets(request, obj)


# -----------------------------
# Register CustomUser with Admin
# -----------------------------
# Try to unregister first (safe)
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass  # Ignore if not already registered

# Now register our custom admin
admin.site.register(CustomUser, CustomUserAdmin)
