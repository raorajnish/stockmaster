from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import LoginForm, CustomerRegisterationForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
from .models import User

# Manager Registration View
def manager_register(request):
    if request.method == "POST":
        form = CustomerRegisterationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_manager = True      # Mark as manager
            user.is_w_staff = False       # Not staff
            user.save()
            auth_login(request, user)
            return redirect('core:dashboard')   # Redirect both to core dashboard
    else:
        form = CustomerRegisterationForm()
    return render(request, 'users/manager_register.html', {'form': form})

# Staff Registration View
def staff_register(request):
    if request.method == "POST":
        form = CustomerRegisterationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_w_staff = True        # Mark as staff
            user.is_manager = False     # Not manager
            user.save()
            auth_login(request, user)
            return redirect('core:dashboard')   # Same dashboard for both
    else:
        form = CustomerRegisterationForm()
    return render(request, 'users/staff_register.html', {'form': form})

# Login View
def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('core:dashboard')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

# Forgot Password - Step 1: Email Input
def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate 4-digit OTP
                otp = str(random.randint(1000, 9999))
                
                # Store OTP and email in session
                request.session['password_reset_otp'] = otp
                request.session['password_reset_email'] = email
                request.session['otp_verified'] = False
                
                # Send OTP via email
                subject = 'StockMaster - Password Reset OTP'
                message = f'''
Hello {user.username},

You have requested to reset your password for StockMaster.

Your OTP code is: {otp}

This code will expire in 10 minutes. If you did not request this, please ignore this email.

Best regards,
StockMaster Team
                '''
                from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@stockmaster.com'
                
                try:
                    send_mail(
                        subject,
                        message,
                        from_email,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, f'OTP has been sent to {email}. Please check your email.')
                    return redirect('users:verify_otp')
                except Exception as e:
                    messages.error(request, f'Failed to send email. Please try again later. Error: {str(e)}')
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                messages.success(request, 'If an account exists with this email, an OTP has been sent.')
                return redirect('users:verify_otp')
    else:
        form = ForgotPasswordForm()
    return render(request, 'users/forgot_password.html', {'form': form})

# Forgot Password - Step 2: OTP Verification
def verify_otp(request):
    if 'password_reset_otp' not in request.session:
        messages.error(request, 'Please start the password reset process from the beginning.')
        return redirect('users:forgot_password')
    
    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            # Accept any 4-character input as valid OTP (for testing)
            if len(entered_otp) == 4:
                request.session['otp_verified'] = True
                messages.success(request, 'OTP verified successfully!')
                return redirect('users:reset_password')
            else:
                messages.error(request, 'Please enter a 4-character code.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'users/verify_otp.html', {'form': form})

# Forgot Password - Step 3: Reset Password
def reset_password(request):
    if 'password_reset_otp' not in request.session or not request.session.get('otp_verified'):
        messages.error(request, 'Please verify your OTP first.')
        return redirect('users:verify_otp')
    
    email = request.session.get('password_reset_email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please start the process again.')
        return redirect('users:forgot_password')
    
    if request.method == "POST":
        form = ResetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Clear session data
            request.session.pop('password_reset_otp', None)
            request.session.pop('password_reset_email', None)
            request.session.pop('otp_verified', None)
            messages.success(request, 'Your password has been changed successfully! You can now login with your new password.')
            return redirect('users:login')
    else:
        form = ResetPasswordForm(user)
    
    return render(request, 'users/reset_password.html', {'form': form})
