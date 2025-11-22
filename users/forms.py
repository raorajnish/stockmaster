from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, SetPasswordForm

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': 'True', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}))

class CustomerRegisterationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'True', 'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # fields to be displayed in the form

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        }),
        label='Email Address'
    )

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': 'Enter any 4 characters',
            'autofocus': True,
            'maxlength': '4',
            'style': 'font-size: 1.5rem; letter-spacing: 0.5rem;'
        }),
        label='OTP Code',
        help_text='Enter any 4-character code'
    )

class ResetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autofocus': True
        }),
        help_text='Your password must contain at least 8 characters.'
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control'
        })
    )

