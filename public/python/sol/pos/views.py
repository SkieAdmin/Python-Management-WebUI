from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Order, OrderItem, Employee, Payment, Receipt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from .decorators import role_required
import uuid






from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, Inventory
from .decorators import role_required
from .forms import ProductForm, InventoryForm









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

#---------------------------------------------------------

@login_required
@role_required('manager')
def product_list(request):
    category_id = request.GET.get('category')
    products = Product.objects.all()

    if category_id:
        products = products.filter(category__id=category_id)

    # include pagination and categories context
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'pos/product_list.html', {
        'products': page_obj,
        'categories': categories
    })



#------------------------------------------------------

@login_required
@role_required('manager')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # <-- accept FILES
        if form.is_valid():
            product = form.save()
            # Create initial inventory entry
            initial_stock = int(request.POST.get('initial_stock', 0))
            Inventory.objects.create(
                product=product,
                quantity_in_stock=initial_stock
            )
            messages.success(request, f"Product '{product.name}' added successfully!")
            return redirect('product_list')
    else:
        form = ProductForm()
    
    categories = Category.objects.all()
    return render(request, 'pos/add_product.html', {
        'form': form,
        'categories': categories
    })

@login_required
@role_required('manager')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)  # Accept FILES
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    categories = Category.objects.all()
    return render(request, 'pos/edit_product.html', {
        'form': form,
        'product': product,
        'categories': categories
    })

#-----------------------------------------------------------------

@login_required
@role_required('manager')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
        return redirect('product_list')
    
    return redirect('product_list')
#---------------------------------------------
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Product, Inventory, StockAdjustment
from .forms import InventoryForm
from .decorators import role_required

@login_required
@role_required('manager')
def update_inventory(request, product_id):
    # Get the product or return a 404 error if not found
    product = get_object_or_404(Product, id=product_id)
    
    # Get or create the inventory for the product
    inventory, created = Inventory.objects.get_or_create(product=product, defaults={'quantity_in_stock': 0})
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory)
        
        if form.is_valid():
            # Save the updated inventory
            form.save()
            
            # Record the adjustment in StockAdjustment
            adjustment_type = form.cleaned_data['adjustment_type']
            quantity_adjusted = form.cleaned_data['adjustment']
            StockAdjustment.objects.create(
                product=product,
                adjustment_type=adjustment_type,
                quantity=quantity_adjusted
            )
            
            messages.success(request, f"Inventory for '{product.name}' updated successfully!")
            return redirect('product_list')
    else:
        form = InventoryForm(instance=inventory)
    
    return render(request, 'pos/update_inventory.html', {
        'form': form,
        'product': product
    })
#----------------------------------------
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


#---------------------------------------------------------------
@login_required
@role_required('cashier')
def create_order(request):
    if request.method == "POST":
        # Create a list to track any out-of-stock items
        out_of_stock_items = []
        insufficient_stock_items = []
        
        # First check if all selected products have sufficient stock
        for product in Product.objects.all():
            checkbox_name = f"product_{product.id}"
            quantity_name = f"quantity_{product.id}"
            
            if checkbox_name in request.POST:
                requested_quantity = int(request.POST.get(quantity_name, 0))
                if requested_quantity > 0:
                    # Check if product has inventory
                    try:
                        inventory = product.inventory
                        
                        # Check if product has enough stock
                        if inventory.quantity_in_stock <= 0:
                            out_of_stock_items.append(product.name)
                        elif inventory.quantity_in_stock < requested_quantity:
                            insufficient_stock_items.append({
                                'name': product.name, 
                                'available': inventory.quantity_in_stock,
                                'requested': requested_quantity
                            })
                    except Product.inventory.RelatedObjectDoesNotExist:
                        # If product has no inventory, treat as out of stock
                        out_of_stock_items.append(f"{product.name} (no inventory record)")
        
        # If any stock issues were found, redirect back with error messages
        if out_of_stock_items or insufficient_stock_items:
            error_messages = []
            if out_of_stock_items:
                error_messages.append(f"The following items are out of stock: {', '.join(out_of_stock_items)}")
            
            if insufficient_stock_items:
                for item in insufficient_stock_items:
                    error_messages.append(f"Insufficient stock for {item['name']} (Available: {item['available']}, Requested: {item['requested']})")
            
            # Redirect back with error messages
            return render(request, 'pos/create_order.html', {
                'categories': Category.objects.all(),
                'products_by_category': {
                    category.id: Product.objects.filter(category=category)
                    for category in Category.objects.all()
                },
                'error_messages': error_messages,
                'form_data': request.POST  # Return form data to preserve selections
            })
            
        # If we get here, all stock checks passed
        order = Order.objects.create(employee=request.user.employee, date_created=timezone.now())
        total_amount = 0
        
        for product in Product.objects.all():
            checkbox_name = f"product_{product.id}"
            quantity_name = f"quantity_{product.id}"
            
            if checkbox_name in request.POST:
                quantity = int(request.POST.get(quantity_name, 0))
                if quantity > 0:
                    # Create the order item
                    OrderItem.objects.create(order=order, product=product, quantity=quantity)
                    total_amount += product.price * quantity
                    
                    # Deduct from inventory
                    try:
                        inventory = product.inventory
                        inventory.quantity_in_stock -= quantity
                        inventory.save()
                    except Product.inventory.RelatedObjectDoesNotExist:
                        # This shouldn't happen if our validation above is working correctly
                        # But just in case, create inventory with 0 stock
                        Inventory.objects.create(
                            product=product,
                            quantity_in_stock=0
                        )
        
        payment_method = request.POST.get('payment_method', 'Cash')
        receipt_number = str(uuid.uuid4())[:30]

        # Map for Payment.model
        PAYMENT_METHOD_MAP = {
            "Cash": "cash",
            "Card": "card",
            "Mobile Payment": "mobile",
        }
        payment_method_choice = PAYMENT_METHOD_MAP.get(payment_method, "cash")

        # Create Payment
        payment = Payment.objects.create(
            order=order,
            method=payment_method_choice,
            amount=total_amount
        )

        receipt = Receipt.objects.create(
            order=order,
            payment=payment,  # <-- this line links receipt to payment
            receipt_number=receipt_number,
            payment_method=payment_method,
            total_amount=total_amount,
            date_issued=timezone.now()
        )
        # Update order status to paid
        order.status = 'paid'
        order.save()

        return redirect('view_receipt', receipt_id=receipt.id)

    # GET request - show the order form
    categories = Category.objects.all()
    
    # Get all products with their inventory status
    products_with_inventory = {}
    for category in categories:
        category_products = []
        for product in Product.objects.filter(category=category):
            try:
                inventory = product.inventory
                category_products.append(product)
            except Product.inventory.RelatedObjectDoesNotExist:
                # Create inventory for products without one
                Inventory.objects.create(
                    product=product,
                    quantity_in_stock=0
                )
                category_products.append(product)
        products_with_inventory[category.id] = category_products
    
    return render(request, 'pos/create_order.html', {
        'categories': categories,
        'products_by_category': products_with_inventory
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
            total_earned=Sum('quantity') * Sum('product__price')  # Corrected: Multiply quantity by price
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


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            raw_password = form.cleaned_data['password']
            user.set_password(raw_password)
            user.save()
            # Assuming you have logic for Employee object here
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

#------------------------------------------------------------
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

#---------------------------------------
# views.py
from django.shortcuts import render
from .models import Product, Category, Order, Receipt
from django.utils import timezone

@login_required
@role_required('manager')
def dashboard_manager(request):
    today = timezone.now().date()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.filter(date_created__date=today).count()
    total_sales = sum(
        receipt.total_amount for receipt in Receipt.objects.filter(date_issued__date=today)
    )
    top_products = (
        OrderItem.objects.filter(order__date_created__date=today)
        .values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )
    recent_orders = Order.objects.filter(status='paid').order_by('-date_created')[:5]

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'top_products': top_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'pos/dashboard_manager.html', context)


#---------------------------------------------
@login_required
def dashboard_cashier(request):
    # Fetch latest data
    today = timezone.now().date()
    
    # Orders today count
    orders_today = Order.objects.filter(date_created__date=today).count()
    
    # Total sales today (sum of total_amount in receipts)
    total_sales_today = Receipt.objects.filter(date_issued__date=today).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent receipts
    recent_receipts = Receipt.objects.filter(date_issued__date=today).order_by('-date_issued')[:10]
    
    # Top selling products today
    top_products = (
        OrderItem.objects.filter(order__date_created__date=today)
        .values('product__name', 'product__price')
        .annotate(
            total_quantity=Sum('quantity')
        )
        .order_by('-total_quantity')[:10]
    )
    
    # Calculate total earned per product
    for item in top_products:
        item['total_earned'] = item['total_quantity'] * item['product__price']
    
    context = {
        'orders_today': orders_today,
        'total_sales_today': total_sales_today,
        'recent_receipts': recent_receipts,
        'top_products': top_products,
    }
    
    return render(request, 'pos/dashboard_cashier.html', context)


#-----------------------------------------
from django.shortcuts import render

def landing(request):
    return render(request, 'pos/landing.html')


#---------------------------------------------
