from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')  # Or use login_required
            if request.user.role == role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this page.")
        return _wrapped_view
    return decorator

def send_verification_email(user, request):
    """Send email verification email to user"""
    token = user.generate_verification_token()
    verification_url = request.build_absolute_uri(
        f'/accounts/verify-email/{user.id}/{token}/'
    )
    
    subject = 'Verify Your Email - E-Hospitality'
    html_message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

def send_password_reset_email(user, request):
    """Send password reset email to user"""
    token = user.generate_password_reset_token()
    reset_url = request.build_absolute_uri(
        f'/accounts/password-reset-confirm/{user.id}/{token}/'
    )
    
    subject = 'Password Reset Request - E-Hospitality'
    html_message = render_to_string('accounts/emails/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
