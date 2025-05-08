from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Order, OrderItem, Employee, Payment, SalesReport, Receipt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from .decorators import role_required
import uuid
@login_required
def home(request):
    try:
        employee = Employee.objects.get(user=request.user)

        if employee.role == 'manager':
            today = timezone.now().date()
            
            # Get top selling products for today
            top_products = (
                OrderItem.objects.filter(order__date_created__date=today)
                .values('product__name')
                .annotate(total_quantity=Sum('quantity'))
                .order_by('-total_quantity')[:5]
            )
            
            # Get recent orders
            recent_orders = Order.objects.filter(
                status='paid'
            ).order_by('-date_created')[:5]
            
            # Calculate total sales for today
            total_sales = sum(
                receipt.total_amount for receipt in Receipt.objects.filter(
                    date_issued__date=today
                )
            )
            
            context = {
                'total_products': Product.objects.count(),
                'total_categories': Category.objects.count(),
                'total_orders': Order.objects.filter(date_created__date=today).count(),
                'total_sales': total_sales,
                'top_products': top_products,
                'recent_orders': recent_orders
            }
            return render(request, 'pos/dashboard_manager.html', context)

        elif employee.role == 'cashier':
            # Your existing cashier dashboard code
            today = timezone.now().date()
            recent_receipts = Receipt.objects.filter(order__employee=employee).order_by('-date_issued')[:5]
            orders_today = Order.objects.filter(employee=employee, date_created__date=today).count()
            total_sales_today = sum(
                receipt.total_amount for receipt in Receipt.objects.filter(
                    order__employee=employee, date_issued__date=today
                )
            )

            top_products = (
                OrderItem.objects.filter(order__employee=employee, order__date_created__date=today)
                .values('product__name')
                .annotate(total_quantity=Sum('quantity'))
                .order_by('-total_quantity')[:5]
            )

            return render(request, 'pos/dashboard_cashier.html', {
                'recent_receipts': recent_receipts,
                'orders_today': orders_today,
                'total_sales_today': total_sales_today,
                'top_products': top_products
            })

    except Employee.DoesNotExist:
        pass

    return render(request, 'pos/home.html')


@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'pos/product_list.html', {'products': products})

@login_required
@role_required('manager')
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        category_id = request.POST['category']
        category = Category.objects.get(id=category_id)
        Product.objects.create(name=name, price=price, category=category)
        return redirect('product_list')
    categories = Category.objects.all()
    return render(request, 'pos/add_product.html', {'categories': categories})

@login_required
def view_receipt(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    order = receipt.order
    order_items = order.orderitem_set.all()

    context = {
        'receipt': receipt,
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'pos/receipt.html', context)

@login_required
@role_required('cashier')
def create_order(request):
    if request.method == "POST":
        order = Order.objects.create(employee=request.user.employee, date_created=timezone.now())
        total_amount = 0

        for product in Product.objects.all():
            checkbox_name = f"product_{product.id}"
            quantity_name = f"quantity_{product.id}"

            if checkbox_name in request.POST:
                quantity = int(request.POST.get(quantity_name, 0))
                if quantity > 0:
                    OrderItem.objects.create(order=order, product=product, quantity=quantity)
                    total_amount += product.price * quantity

        payment_method = request.POST.get('payment_method', 'Cash')
        receipt_number = str(uuid.uuid4())[:30]

        receipt = Receipt.objects.create(
            order=order,
            receipt_number=receipt_number,
            payment_method=payment_method,
            total_amount=total_amount,
            date_issued=timezone.now()
        )

        return redirect('view_receipt', receipt_id=receipt.id)

    categories = Category.objects.all()
    products_by_category = {
        category.id: Product.objects.filter(category=category)
        for category in categories
    }

    return render(request, 'pos/create_order.html', {
        'categories': categories,
        'products_by_category': products_by_category
    })

#------------------------------------------------
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
from .models import Order, OrderItem, Receipt

@login_required
@role_required('manager')
def sales_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today = timezone.now().date()

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = end_date = today

    # Get all orders in the date range
    orders = Order.objects.filter(date_created__date__range=(start_date, end_date))

    # Get corresponding receipts
    receipts = Receipt.objects.filter(order__in=orders)

    # Total sales from receipts
    total_sales = receipts.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Total orders count
    total_orders = orders.count()

    # Top Selling Products
    top_products = (
        OrderItem.objects.filter(order__in=orders)
        .values('product__name')
        .annotate(
            quantity_sold=Sum('quantity'),
            total_earned=Sum('product__price')  # sum of product price * quantity is not exact here
        )
        .order_by('-quantity_sold')[:5]
    )

    # Sales by Employee (from receipts)
    employee_sales = (
        receipts.values('order__employee__user__username')
        .annotate(
            order_count=Count('order'),
            sales=Sum('total_amount')
        )
        .order_by('-sales')
    )

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'top_products': top_products,
        'employee_sales': employee_sales,
    }

    return render(request, 'pos/sales_report.html', context)



#------------------------------------------------

@login_required
@role_required('cashier')
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            raw_password = form.cleaned_data['password']
            user.set_password(raw_password)
            user.save()

            Employee.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                role=form.cleaned_data['role']
            )

            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'pos/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'pos/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
