from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, CustomerProfileForm, LoginForm
from .models import Customer
from orders.models import Order

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('menu')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                if user.is_staff:
                    return redirect('dashboard')
                else:
                    return redirect('menu')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    recent_orders = Order.objects.all().order_by('-order_date')[:10]
    
    pending_orders = Order.objects.filter(status='pending').count()
    payment_processing = Order.objects.filter(payment_status='processing').count()
    
    context = {
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'payment_processing': payment_processing,
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def customer_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'accounts/customer_list.html', {'customers': customers})

@login_required
def staff_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    staff = User.objects.filter(is_staff=True).order_by('-date_joined')
    return render(request, 'accounts/staff_list.html', {'staff': staff})

@login_required
def customer_dashboard(request):
    if request.user.is_staff:
        return redirect('dashboard')
    
    try:
        customer = request.user.customer
        recent_orders = Order.objects.filter(customer=customer).order_by('-order_date')[:5]
    except Customer.DoesNotExist:
        recent_orders = []
    
    context = {
        'recent_orders': recent_orders,
    }
    
    return render(request, 'accounts/customer_dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        if request.user.is_staff:
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
        else:
            try:
                customer = request.user.customer
                form = CustomerProfileForm(request.POST, instance=customer)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('customer_dashboard')
            except Customer.DoesNotExist:
                form = CustomerProfileForm(request.POST)
                if form.is_valid():
                    customer = form.save(commit=False)
                    customer.user = request.user
                    customer.save()
                    messages.success(request, 'Profile created successfully!')
                    return redirect('customer_dashboard')
    else:
        try:
            if not request.user.is_staff:
                customer = request.user.customer
                form = CustomerProfileForm(instance=customer)
            else:
                form = None
        except Customer.DoesNotExist:
            form = CustomerProfileForm()
    
    return render(request, 'accounts/profile.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
