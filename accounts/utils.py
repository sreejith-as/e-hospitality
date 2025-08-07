from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

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