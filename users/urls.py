from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/manager/', views.manager_register, name='manager_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
]

