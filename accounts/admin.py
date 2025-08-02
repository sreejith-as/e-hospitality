from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser
from admins.models import DoctorAllocation
from doctors.models import DoctorSchedule

class DoctorAllocationInline(admin.StackedInline):
    model = DoctorAllocation
    can_delete = False
    verbose_name_plural = 'Doctor Allocation'

class DoctorScheduleInline(admin.StackedInline):
    model = DoctorSchedule
    can_delete = False
    verbose_name_plural = 'Doctor Schedule'

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'date_of_birth', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj and obj.role == 'doctor':
            inline_instances = [DoctorAllocationInline(self.model, self.admin_site), DoctorScheduleInline(self.model, self.admin_site)]
        return inline_instances

admin.site.register(CustomUser, CustomUserAdmin)
