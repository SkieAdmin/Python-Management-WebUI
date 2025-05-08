# shop/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.http import require_http_methods

from .forms import PaymentForm
from .models import Product, Order


def home(request):
    products = Product.objects.all() if request.user.is_staff else Product.objects.filter(available=True)
    return render(request, 'shop/home.html', {'products': products})


def products(request):
    products = Product.objects.all() if request.user.is_staff else Product.objects.filter(available=True)
    return render(request, 'shop/products.html', {'products': products})


@login_required(login_url='login')
@require_http_methods(["POST"])
def order_product(request, product_id):
    """
    For direct POST /order/<id>/ (optional).
    """
    product = get_object_or_404(Product, pk=product_id, available=True)
    full_name     = request.POST.get("full_name", "").strip()
    email         = request.POST.get("email", "").strip()
    address       = request.POST.get("address", "").strip()
    contact       = request.POST.get("contact", "").strip()
    quantity      = int(request.POST.get("quantity", 1))
    scheduled_for = request.POST.get("scheduled_for", "").strip()
    notes         = request.POST.get("notes", "").strip()

    if not all([full_name, email, address, contact, scheduled_for]):
        messages.error(request, "Please fill in all required fields.")
        return redirect(reverse('products'))

    Order.objects.create(
        product=product,
        user=request.user,
        customer_name=full_name,
        customer_email=email,
        customer_address=address,
        customer_contact=contact,
        quantity=quantity,
        scheduled_for=scheduled_for,
        notes=notes
    )
    messages.success(request, "Your order has been placed!")
    return redirect(reverse('products') + '?ordered=1')


@login_required(login_url='login')
@require_http_methods(["POST"])
def submit_order(request):
    """
    Receives modal POST from products.html → creates Order → redirect to /orders/.
    """
    product_id = request.POST.get("product_id")
    product = get_object_or_404(Product, pk=product_id, available=True)

    full_name     = request.POST.get("full_name", "").strip()
    email         = request.POST.get("email", "").strip()
    address       = request.POST.get("address", "").strip()
    contact       = request.POST.get("contact", "").strip()
    quantity      = int(request.POST.get("quantity", 1))
    scheduled_for = request.POST.get("scheduled_for", "").strip()
    notes         = request.POST.get("notes", "").strip()

    if not all([full_name, email, address, contact, scheduled_for]):
        messages.error(request, "Please fill in all required fields.")
        return redirect(reverse('products'))

    Order.objects.create(
        product=product,
        user=request.user,
        customer_name=full_name,
        customer_email=email,
        customer_address=address,
        customer_contact=contact,
        quantity=quantity,
        scheduled_for=scheduled_for,
        notes=notes
    )
    messages.success(request, "Your order has been placed!")
    return redirect('orders')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    next_url = request.GET.get('next', 'home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            messages.success(request, f'Welcome back, {request.user.username}!')
            return redirect(next_url)
        messages.error(request, 'Invalid credentials.')
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form, 'next': next_url})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! Please log in.')
            return redirect(reverse('home') + '?open=login')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'shop/signup.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required(login_url='login')
def orders(request):
    visible_statuses = ['pending', 'processing', 'shipped', 'delivered']
    orders = Order.objects.filter(user=request.user, status__in=visible_statuses).order_by('-ordered_at')
    return render(request, 'shop/orders.html', {
        'orders': orders,
        'visible_statuses': visible_statuses
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def submit_payment(request):
    """
    Handles receipt upload → redirects to /orders/ with messages.
    """
    order_id = request.POST.get('order_id')
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if hasattr(order, 'payment'):
        messages.error(request, "Payment already submitted.")
        return redirect('orders')

    form = PaymentForm(request.POST, request.FILES)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.order = order
        payment.save()
        messages.success(request, "Payment submitted. Thank you!")
    else:
        messages.error(request, "Please fix the errors in your payment form.")

    return redirect('orders')
