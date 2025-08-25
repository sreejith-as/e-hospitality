from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<int:user_id>/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('password-reset-request/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<int:user_id>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change-password/', views.change_password, name='change_password'),
]
