from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from .forms import LoginForm, CustomerRegisterationForm

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
