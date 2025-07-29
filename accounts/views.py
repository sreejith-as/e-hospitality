from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from accounts.forms import PatientRegistrationForm

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'patient':
                return redirect('patients:overview')
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
    logout(request)
    return redirect('accounts:login')

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'patient'
            user.save()
            return redirect('accounts:login')
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})
