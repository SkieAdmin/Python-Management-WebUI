from django.shortcuts       import render, redirect, get_object_or_404
from django.contrib.auth    import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib         import messages
from .models                import Product, Order
from .forms                 import OrderForm, PaymentForm, ProductForm, OrderStatusForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q

def landing_page(request):
    """
    Renders the home page. Signup/login are handled in separate views.
    """
    products = Product.objects.all()
    return render(request, 'main/landing_page.html', {
        'products': products,
    })


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        error = 'Invalid credentials or not an admin.'

    return render(request, 'main/admin_login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('landing_page')


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='admin_login')(view_func)


@login_required(login_url='landing_page')
def products_view(request):
    products   = Product.objects.all()
    order_form = OrderForm()
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            messages.success(
                request,
                f'Order placed for {order.product.name} (×{order.quantity}).'
            )
            return redirect('products')
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'main/products.html', {
        'products': products,
        'order_form': order_form,
    })


@login_required(login_url='landing_page')
def orders_view(request):
    if request.user.is_staff:
        orders = Order.objects.select_related('product', 'user') \
                              .all().order_by('-ordered_at')
    else:
        orders = Order.objects.select_related('product') \
                              .filter(user=request.user) \
                              .order_by('-ordered_at')
    return render(request, 'main/orders.html', {'orders': orders})


@login_required(login_url='landing_page')
def create_order(request):
    if request.method != 'POST':
        return redirect('products')
    product = get_object_or_404(Product, pk=request.POST.get('product_id'))
    quantity = int(request.POST.get('quantity', 1))
    note = request.POST.get('note', '').strip()
    Order.objects.create(user=request.user, product=product, quantity=quantity, note=note)
    return redirect('products')


@staff_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added.')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'main/admin_product_form.html', {'form': form, 'title': 'New Product'})


@staff_required
def confirm_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.is_confirmed = True
    order.save()
    messages.success(request, f'Order #{order.id} confirmed.')
    return redirect('admin_orders')


@login_required(login_url='landing_page')
def make_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            order = get_object_or_404(Order, pk=form.cleaned_data['order_id'], user=request.user)
            order.receipt = form.cleaned_data['receipt']
            order.note    = form.cleaned_data.get('note', '')
            order.status  = Order.STATUS_AWAITING_CONFIRMATION
            order.save()
        else:
            messages.error(request, 'Failed to upload receipt.')
    return redirect('orders_list')


@login_required(login_url='landing_page')
def orders_list(request):
    if request.user.is_staff:
        orders = Order.objects.select_related('product','user').all().order_by('-ordered_at')
    else:
        orders = Order.objects.select_related('product').filter(user=request.user).order_by('-ordered_at')
    return render(request, 'main/orders.html', {'orders': orders})



@staff_member_required
def admin_dashboard(request):
    products_count = Product.objects.count()
    orders_count   = Order.objects.count()
    total_revenue  = (
        Order.objects.aggregate(total_revenue=Sum('total_price'))
        .get('total_revenue') or 0
    )
    return render(request, 'main/admin_dashboard.html', {
        'products_count': products_count,
        'orders_count':   orders_count,
        'total_revenue':  total_revenue,
    })


@staff_required
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'main/admin_products.html', {'products': products})


@staff_required
def admin_product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('admin_products')
    return render(request, 'main/admin_product_form.html', {'form': form, 'title': 'New Product'})


@staff_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('admin_products')
    return render(request, 'main/admin_product_form.html', {'form': form, 'title': f'Edit: {product.name}'})


@staff_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('admin_products')

def order_invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'main/order_invoice.html', {'order': order})

@staff_required
def admin_orders(request):
    orders = Order.objects.select_related('product', 'user').order_by('-ordered_at')
    return render(request, 'main/admin_orders.html', {'orders': orders})


@staff_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderStatusForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        return redirect('admin_orders')
    return render(request, 'main/admin_order_detail.html', {'order': order, 'form': form})


@staff_required
def admin_order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    return redirect('admin_orders')


@staff_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')

def login_view(request):
    if request.method == "POST":
        email    = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('landing_page')

        user = authenticate(request, username=user_obj.username, password=password)
        if user:
            login(request, user)
        else:
            messages.error(request, "Invalid credentials.")
    return redirect('landing_page')

def signup_view(request):
    if request.method == "POST":
        full_name     = request.POST.get('full_name')
        email         = request.POST.get('email')
        password      = request.POST.get('password')
        password_conf = request.POST.get('password_confirmation')

        if password != password_conf:
            messages.error(request, "Passwords do not match.")
            return redirect('landing_page')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('landing_page')

        # Create the user (but do NOT log them in)
        username = email.split('@')[0]
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.first_name = full_name
        user.save()

        # Show a success message, then redirect to login
        return redirect('landing_page')     # or redirect('login') if you have a dedicated login page

    # For any non-POST, just bounce them back:
    return redirect('landing_page')



def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.all()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    return render(request, 'your_template.html', {'products': products})




def logout_view(request):
    logout(request)
    return redirect('landing_page')
