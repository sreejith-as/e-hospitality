from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from accounts.forms import PatientRegistrationForm
from accounts.models import CustomUser
from accounts.utils import send_verification_email, send_password_reset_email
from django.contrib.auth.forms import PasswordChangeForm

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.email_verified:
                messages.error(request, 'Please verify your email before logging in.')
                return redirect('accounts:login')
            login(request, user)
            if user.role == 'patient':
                return redirect('patients:dashboard')
            elif user.role == 'doctor':
                return redirect('doctors:dashboard')
            elif user.role == 'admin':
                return redirect('admins:dashboard')
            else:
                logout(request)
                messages.error(request, 'Invalid user role.')
                return redirect('accounts:login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('accounts:login')
    return render(request, 'accounts/login.html')

def user_logout(request):
    messages.get_messages(request)
    logout(request)
    return redirect('accounts:login')

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'patient'
            user.email_verified = False
            user.save()
            
            # Send verification email
            send_verification_email(user, request)
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def verify_email(request, user_id, token):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.is_verification_token_valid(token):
        user.email_verified = True
        user.verification_token = None
        user.verification_token_created_at = None
        user.save()
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('accounts:login')

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            if user.email_verified:
                messages.info(request, 'Email is already verified.')
            else:
                send_verification_email(user, request)
                messages.success(request, 'Verification email sent! Please check your inbox.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
        return redirect('accounts:login')
    return render(request, 'accounts/resend_verification.html')

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            if not user.email_verified:
                messages.error(request, 'Please verify your email before resetting password.')
                return redirect('accounts:password_reset_request')
            
            send_password_reset_email(user, request)
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('accounts:login')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'accounts/password_reset_request.html')

def password_reset_confirm(request, user_id, token):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if not user.is_password_reset_token_valid(token):
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('accounts:password_reset_request')
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.password_reset_token = None
            user.password_reset_token_created_at = None
            user.save()
            messages.success(request, 'Password reset successfully! You can now login with your new password.')
            return redirect('accounts:login')
    else:
        form = SetPasswordForm(user)
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect based on user role
            if request.user.role == 'patient':
                return redirect('patients:dashboard')
            elif request.user.role == 'doctor':
                return redirect('doctors:dashboard')
            elif request.user.role == 'admin':
                return redirect('admins:dashboard')
            else:
                return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Use appropriate template based on user role
    if request.user.role == 'patient':
        return render(request, 'patients/change_password.html', {'form': form})
    elif request.user.role == 'doctor':
        return render(request, 'doctors/change_password.html', {'form': form})
    else:
        return render(request, 'admins/change_password.html', {'form': form})
