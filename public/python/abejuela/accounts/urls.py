from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('customers/', views.customer_list, name='customer_list'),
    path('staff/', views.staff_list, name='staff_list'),
]
