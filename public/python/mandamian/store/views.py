from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F, Sum
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
import json
import uuid
from decimal import Decimal
from .models import User, Product, Transaction, TransactionItem, Payment, Supply, AuditLog, Cart, CartItem, StockRequest, StockDelivery, Delivery, StoreSettings
from .forms import CustomUserCreationForm, ProductForm

def home(request):
    return render(request, 'store/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='Account Created',
                    details=f'Customer account created: {user.username}'
                )
                login(request, user)
                messages.success(request, 'Your account has been created successfully!')
                return redirect('home')
            except Exception as e:
                messages.error(request, 'An error occurred while creating your account. Please try again.')
        else:
            for field in form.errors:
                for error in form[field].errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/register.html', {'form': form})

@login_required
def products(request):
    products = Product.objects.filter(is_active=True, stock__gt=0)
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = {}
    if cart:
        cart_items = {item.product_id: item.quantity for item in cart.cartitem_set.all()}
    return render(request, 'store/products.html', {
        'products': products,
        'cart_items': cart_items
    })

@login_required
@require_POST
def add_to_cart(request, product_id):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({'error': 'Only customers can add items to cart'}, status=403)
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > product.stock:
        return JsonResponse({'error': 'Not enough stock available'}, status=400)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity = F('quantity') + quantity
        cart_item.save()
        cart_item.refresh_from_db()
    else:
        cart_item.quantity = quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Added {quantity} {product.name} to cart',
        'cart_total': cart.get_total()
    })

@login_required
@require_POST
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 0))
    
    if quantity <= 0:
        cart_item.delete()
        message = 'Item removed from cart'
    else:
        if quantity > cart_item.product.stock:
            return JsonResponse({'error': 'Not enough stock available'}, status=400)
        cart_item.quantity = quantity
        cart_item.save()
        message = 'Cart updated'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'cart_total': cart_item.cart.get_total() if quantity > 0 else 0
    })

@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart',
        'cart_total': cart_item.cart.get_total()
    })

@login_required
def view_cart(request):
    if request.user.role != 'CUSTOMER':
        messages.error(request, 'Only customers can view cart')
        return redirect('home')
    
    cart = Cart.objects.filter(user=request.user).first()
    return render(request, 'store/cart.html', {'cart': cart})

@login_required
@require_POST
def checkout(request):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({'error': 'Only customers can checkout'}, status=403)

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.cartitem_set.exists():
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    try:
        # Parse request data
        data = json.loads(request.body)
        selected_items = data.get('items', [])
        delivery_fee = Decimal(data.get('delivery_fee', 50.00))
        
        if not selected_items:
            return JsonResponse({'error': 'No items selected for checkout'}, status=400)
        
        # Get store settings or create default
        store_settings, created = StoreSettings.objects.get_or_create(id=1)
        if created:
            store_settings.delivery_fee = delivery_fee
            store_settings.save()
        
        # Use Django's transaction.atomic() context manager
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            # Calculate subtotal from selected items
            cart_items = cart.cartitem_set.filter(id__in=selected_items)
            if not cart_items.exists():
                return JsonResponse({'error': 'Selected items not found in cart'}, status=400)
            
            subtotal = sum(item.get_total() for item in cart_items)
            total_amount = subtotal + delivery_fee
            
            # Create transaction
            new_transaction = Transaction.objects.create(
                user=request.user,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total_amount=total_amount,
                status='PENDING'
            )

            # Create transaction items
            for item in cart_items:
                TransactionItem.objects.create(
                    transaction=new_transaction,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            
            # Remove selected items from cart
            cart_items.delete()

            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Checkout Started',
                details=f'Transaction #{new_transaction.id} created'
            )

            return JsonResponse({
                'success': True,
                'transaction_id': new_transaction.id
            })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred during checkout: {str(e)}'}, status=500)

@login_required
def checkout_page(request, transaction_id):
    if request.user.role != 'CUSTOMER':
        messages.error(request, 'Access denied. Customer access only.')
        return redirect('home')
    
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if transaction.status != 'PENDING':
        messages.error(request, 'This transaction has already been processed.')
        return redirect('order_tracking')
    
    items = TransactionItem.objects.filter(transaction=transaction)
    store_settings = StoreSettings.objects.first()
    
    return render(request, 'store/checkout_page.html', {
        'transaction': transaction,
        'items': items,
        'subtotal': transaction.subtotal,
        'delivery_fee': transaction.delivery_fee,
        'total_amount': transaction.total_amount,
        'gcash_qr': store_settings.gcash_qr_code if store_settings else None,
        'gcash_number': store_settings.gcash_number if store_settings else None,
        'gcash_name': store_settings.gcash_name if store_settings else None
    })

@login_required
@require_POST
def complete_checkout(request, transaction_id):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if transaction.status != 'PENDING':
        return JsonResponse({'error': 'This transaction has already been processed'}, status=400)
    
    try:
        # Get payment details from POST data
        payment_method = request.POST.get('payment_method')
        reference_id = request.POST.get('reference_id', '')
        
        # Debug logging
        print(f"Payment method: {payment_method}")
        print(f"Reference ID: {reference_id}")
        print(f"POST data: {request.POST}")
        print(f"FILES: {request.FILES}")
        
        if not payment_method:
            return JsonResponse({'error': 'Payment method is required'}, status=400)
        
        if payment_method == 'gcash' and not reference_id:
            return JsonResponse({'error': 'GCash reference number is required'}, status=400)
        
        # Use Django's transaction.atomic() context manager
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            # Update transaction
            transaction.payment_method = 'GCASH' if payment_method == 'gcash' else 'COD'
            transaction.status = 'PROCESSING'
            transaction.processing_date = timezone.now()
            transaction.save()
            
            # Create payment record for GCash
            if payment_method == 'gcash':
                payment = Payment.objects.create(
                    transaction=transaction,
                    amount=transaction.total_amount,
                    reference_id=reference_id,
                    status='WAITING'
                )
                
                # Handle receipt upload
                if 'receipt_image' in request.FILES:
                    payment.receipt_image = request.FILES['receipt_image']
                    payment.save()
            
            # Create delivery record
            delivery = Delivery.objects.create(
                transaction=transaction,
                status='PROCESSING'
            )
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Order Placed',
                details=f'Transaction #{transaction.id}, Payment Method: {transaction.get_payment_method_display()}'
            )
            
            return JsonResponse({'success': True, 'redirect_url': reverse('order_tracking')})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def order_tracking(request):
    if request.user.role != 'CUSTOMER':
        messages.error(request, 'Access denied. Customer access only.')
        return redirect('home')
    
    orders = Transaction.objects.filter(
        user=request.user,
        status__in=['PROCESSING', 'IN_TRANSIT', 'DELIVERED', 'COMPLETED']
    ).order_by('-created_at')
    
    return render(request, 'store/order_tracking.html', {'orders': orders})

@login_required
def get_order_details(request, order_id):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    order = get_object_or_404(Transaction, id=order_id, user=request.user)
    items = TransactionItem.objects.filter(transaction=order)
    
    # Check if there's a delivery associated with this order
    delivery = None
    try:
        delivery_obj = Delivery.objects.filter(transaction=order).first()
        if delivery_obj:
            delivery = {
                'status': delivery_obj.get_status_display(),
                'delivery_date': delivery_obj.delivery_date.strftime('%Y-%m-%d %H:%M') if delivery_obj.delivery_date else None,
                'notes': delivery_obj.notes,
                'created_at': delivery_obj.created_at.strftime('%Y-%m-%d %H:%M')
            }
    except:
        pass
    
    # Get payment information
    payment = Payment.objects.filter(transaction=order).first()
    payment_status = payment.get_status_display() if payment else 'Not Applicable'
    payment_method = order.get_payment_method_display() if order.payment_method else 'Not Specified'
    reference_id = payment.reference_id if payment else None
    
    # Format items data
    items_data = [{
        'product_name': item.product.name,
        'quantity': item.quantity,
        'price': float(item.price)
    } for item in items]
    
    return JsonResponse({
        'id': order.id,
        'status': order.status,
        'status_display': order.get_status_display(),
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        'processing_date': order.processing_date.strftime('%Y-%m-%d %H:%M') if order.processing_date else None,
        'subtotal': float(order.subtotal),
        'delivery_fee': float(order.delivery_fee),
        'total_amount': float(order.total_amount),
        'items': items_data,
        'delivery': delivery,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'reference_id': reference_id
    })

@login_required
@require_POST
def mark_order_received(request, order_id):
    if request.user.role != 'CUSTOMER':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    order = get_object_or_404(Transaction, id=order_id, user=request.user)
    
    if order.status != 'IN_TRANSIT':
        return JsonResponse({'error': 'Only orders in transit can be marked as received'}, status=400)
    
    try:
        with transaction.atomic():
            # Update transaction status
            order.status = 'DELIVERED'
            order.save()
            
            # Update delivery status
            delivery = Delivery.objects.filter(transaction=order).first()
            if delivery:
                delivery.status = 'DELIVERED'
                delivery.delivery_date = timezone.now()
                delivery.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Order Received',
                details=f'Order #{order.id} marked as received by customer'
            )
            
            return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)        

@login_required
def payment_history(request):
    if request.user.role != 'CUSTOMER':
        messages.error(request, 'Access denied.')
        return redirect('home')
    payments = Payment.objects.filter(transaction__user=request.user)
    return render(request, 'store/payment_history.html', {'payments': payments})

@login_required
def inventory(request):
    if request.user.role not in ['STAFF', 'ADMIN']:
        messages.error(request, 'Access denied. Staff or admin access only.')
        return redirect('home')
    
    products = Product.objects.all().order_by('-updated_at')
    form = ProductForm()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Product Added',
                details=f'Product: {product.name}, Price: {product.price}, Stock: {product.stock}'
            )
            messages.success(request, 'Product added successfully!')
            return redirect('inventory')
        else:
            messages.error(request, 'Error adding product. Please check the form.')
    
    return render(request, 'store/inventory.html', {
        'products': products,
        'form': form
    })

@login_required
def get_product(request, product_id):
    if request.user.role not in ['STAFF', 'ADMIN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)
    
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'stock': product.stock,
        'is_active': product.is_active
    })

@login_required
@require_POST
def edit_product(request, product_id):
    if request.user.role not in ['STAFF', 'ADMIN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)
    
    try:
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.is_active = request.POST.get('is_active') == 'true'
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Product Updated',
            details=f'Product: {product.name}, Price: {product.price}, Stock: {product.stock}'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def update_product_stock(request, product_id):
    if request.user.role not in ['STAFF', 'ADMIN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)
    
    try:
        data = json.loads(request.body)
        new_stock = int(data.get('stock', 0))
        
        if new_stock < 0:
            return JsonResponse({'error': 'Stock cannot be negative'}, status=400)
        
        old_stock = product.stock
        product.update_stock(new_stock)
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Stock Updated',
            details=f'Product: {product.name}, Old Stock: {old_stock}, New Stock: {new_stock}'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def stock_requests(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin access only.')
        return redirect('home')
    
    stock_requests = StockRequest.objects.all().order_by('-created_at')
    products = Product.objects.filter(is_active=True)
    suppliers = User.objects.filter(role='SUPPLIER')
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity')
        supplier_id = request.POST.get('supplier')
        notes = request.POST.get('notes', '')
        
        try:
            product = get_object_or_404(Product, id=product_id)
            supplier = get_object_or_404(User, id=supplier_id, role='SUPPLIER')
            
            stock_request = StockRequest.objects.create(
                product=product,
                quantity=int(quantity),
                requested_by=request.user,
                supplier=supplier,
                notes=notes
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Stock Request Created',
                details=f'Product: {product.name}, Quantity: {quantity}, Supplier: {supplier.username}'
            )
            
            messages.success(request, 'Stock request created successfully!')
            return redirect('stock_requests')
        except Exception as e:
            messages.error(request, f'Error creating stock request: {str(e)}')
    
    return render(request, 'store/stock_requests.html', {
        'stock_requests': stock_requests,
        'products': products,
        'suppliers': suppliers
    })

@login_required
def stock_delivery_progress(request):
    if request.user.role not in ['ADMIN', 'STAFF']:
        messages.error(request, 'Access denied. Admin or Staff access only.')
        return redirect('home')
    
    # Get all stock requests with their deliveries
    stock_requests = StockRequest.objects.all().order_by('-created_at')
    
    # Get delivery information for each request
    delivery_info = {}
    for stock_request in stock_requests:
        delivery = StockDelivery.objects.filter(stock_request=stock_request).first()
        if delivery:
            delivery_info[stock_request.id] = delivery
    
    return render(request, 'store/stock_delivery_progress.html', {
        'stock_requests': stock_requests,
        'delivery_info': delivery_info
    })

@login_required
def get_stock_request(request, request_id):
    if request.user.role not in ['ADMIN', 'SUPPLIER']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    stock_request = get_object_or_404(StockRequest, id=request_id)
    
    # Check if there's a delivery associated with this request
    delivery = None
    try:
        delivery_obj = stock_request.stockdelivery_set.first()
        if delivery_obj:
            delivery = {
                'status': delivery_obj.get_status_display(),
                'delivery_date': delivery_obj.delivery_date.strftime('%Y-%m-%d %H:%M') if delivery_obj.delivery_date else None,
                'notes': delivery_obj.notes
            }
    except:
        pass
    
    return JsonResponse({
        'id': stock_request.id,
        'product_name': stock_request.product.name,
        'quantity': stock_request.quantity,
        'supplier_name': stock_request.supplier.username,
        'status': stock_request.get_status_display(),
        'notes': stock_request.notes,
        'created_at': stock_request.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': stock_request.updated_at.strftime('%Y-%m-%d %H:%M'),
        'delivery': delivery
    })

@login_required
@require_POST
def cancel_stock_request(request, request_id):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    stock_request = get_object_or_404(StockRequest, id=request_id)
    
    if stock_request.status != 'PENDING':
        return JsonResponse({'error': 'Only pending requests can be cancelled'}, status=400)
    
    try:
        stock_request.status = 'CANCELLED'
        stock_request.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Stock Request Cancelled',
            details=f'Request #{request_id} for {stock_request.product.name}'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def transactions(request):
    if request.user.role not in ['STAFF', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('home')
    transactions = Transaction.objects.all()
    return render(request, 'store/transactions.html', {'transactions': transactions})

@login_required
def get_transaction_details(request, transaction_id):
    if request.user.role not in ['STAFF', 'ADMIN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    transaction = get_object_or_404(Transaction, id=transaction_id)
    items = TransactionItem.objects.filter(transaction=transaction)
    
    # Check if there's a delivery associated with this transaction
    delivery = None
    try:
        delivery_obj = Delivery.objects.filter(transaction=transaction).first()
        if delivery_obj:
            delivery = {
                'status': delivery_obj.get_status_display(),
                'delivery_date': delivery_obj.delivery_date.strftime('%Y-%m-%d %H:%M') if delivery_obj.delivery_date else None,
                'notes': delivery_obj.notes,
                'created_at': delivery_obj.created_at.strftime('%Y-%m-%d %H:%M')
            }
    except:
        pass
    
    # Get payment information
    payment = Payment.objects.filter(transaction=transaction).first()
    payment_status = payment.get_status_display() if payment else 'Not Applicable'
    payment_method = transaction.get_payment_method_display() if transaction.payment_method else 'Not Specified'
    reference_id = payment.reference_id if payment else None
    
    # Format items data
    items_data = [{
        'product_name': item.product.name,
        'quantity': item.quantity,
        'price': float(item.price),
        'total': float(item.price * item.quantity)
    } for item in items]
    
    return JsonResponse({
        'id': transaction.id,
        'customer': transaction.user.username,
        'status': transaction.status,
        'status_display': transaction.get_status_display(),
        'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M'),
        'processing_date': transaction.processing_date.strftime('%Y-%m-%d %H:%M') if transaction.processing_date else None,
        'subtotal': float(transaction.subtotal),
        'delivery_fee': float(transaction.delivery_fee),
        'total_amount': float(transaction.total_amount),
        'items': items_data,
        'delivery': delivery,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'reference_id': reference_id
    })

@login_required
def payments(request):
    if request.user.role not in ['STAFF', 'ADMIN']:
        messages.error(request, 'Access denied.')
        return redirect('home')
    payments = Payment.objects.all()
    return render(request, 'store/payments.html', {'payments': payments})

@login_required
def supply_status(request):
    if request.user.role != 'SUPPLIER':
        messages.error(request, 'Access denied.')
        return redirect('home')
    supplies = Supply.objects.filter(supplier=request.user)
    return render(request, 'store/supply_status.html', {'supplies': supplies})

@login_required
def store_settings(request):
    if request.user.role not in ['ADMIN', 'STAFF']:
        messages.error(request, 'Access denied. Admin or staff access only.')
        return redirect('home')
    
    # Get or create store settings
    settings, created = StoreSettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        try:
            # Update delivery fee
            delivery_fee = request.POST.get('delivery_fee')
            if delivery_fee:
                settings.delivery_fee = Decimal(delivery_fee)
            
            # Update GCash information
            settings.gcash_number = request.POST.get('gcash_number', '')
            settings.gcash_name = request.POST.get('gcash_name', '')
            
            # Handle QR code upload
            if 'gcash_qr_code' in request.FILES:
                settings.gcash_qr_code = request.FILES['gcash_qr_code']
            
            settings.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Store Settings Updated',
                details=f'Delivery Fee: {settings.delivery_fee}, GCash Number: {settings.gcash_number}'
            )
            
            messages.success(request, 'Store settings updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    return render(request, 'store/store_settings.html', {'settings': settings})

@login_required
def audit(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('home')
    audit_logs = AuditLog.objects.all()
    return render(request, 'store/audit.html', {'audit_logs': audit_logs})

@login_required
def user_management(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('home')
    users = User.objects.all()
    return render(request, 'store/user_management.html', {'users': users})

@login_required
@require_POST
def toggle_user(request, user_id):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    # Don't allow toggling self
    if user == request.user:
        return JsonResponse({'error': 'You cannot deactivate your own account'}, status=400)
    
    # Toggle user status
    user.is_active = not user.is_active
    user.save()
    
    # Log the action
    AuditLog.objects.create(
        user=request.user,
        action=f'User {"Activated" if user.is_active else "Deactivated"}',
        details=f'User: {user.username}'
    )
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active
    })

@login_required
@require_POST
def delete_user(request, user_id):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
        
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        return JsonResponse({'error': 'Cannot delete your own account'}, status=400)
    
    username = user.username
    user.delete()
    
    # Log the action
    AuditLog.objects.create(
        user=request.user,
        action='User Deleted',
        details=f'User: {username}'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'User {username} has been deleted'
    })

@login_required
@require_POST
def create_staff(request):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
        
    form = CustomUserCreationForm(request.POST)
    if form.is_valid():
        user = form.save()
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Staff Account Created',
            details=f'User: {user.username}, Role: {user.role}'
        )
        return JsonResponse({
            'success': True,
            'message': f'Staff account {user.username} created successfully'
        })
    return JsonResponse({'error': form.errors}, status=400)

@login_required
@require_POST
def update_user_role(request, user_id):
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    # Don't allow updating own role
    if user == request.user:
        return JsonResponse({'error': 'You cannot change your own role'}, status=400)
    
    try:
        new_role = request.POST.get('role')
        if new_role not in [role[0] for role in User.ROLE_CHOICES]:
            return JsonResponse({'error': 'Invalid role'}, status=400)
        
        old_role = user.get_role_display()
        user.role = new_role
        user.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='User Role Updated',
            details=f'User: {user.username}, Old Role: {old_role}, New Role: {user.get_role_display()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} role updated to {user.get_role_display()}',
            'new_role': user.get_role_display(),
            'role_code': user.role
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def supplier_dashboard(request):
    if request.user.role != 'SUPPLIER':
        messages.error(request, 'Access denied. Supplier access only.')
        return redirect('home')
    
    stock_requests = StockRequest.objects.filter(supplier=request.user).order_by('-created_at')
    pending_count = stock_requests.filter(status='PENDING').count()
    in_transit_count = stock_requests.filter(status='IN_TRANSIT').count()
    
    return render(request, 'store/supplier_dashboard.html', {
        'stock_requests': stock_requests,
        'pending_count': pending_count,
        'in_transit_count': in_transit_count
    })

@login_required
def admin_stock_requests(request):
    if request.user.role != 'SUPPLIER':
        messages.error(request, 'Access denied. Supplier access only.')
        return redirect('home')
    
    # Get all pending and approved stock requests for this supplier
    stock_requests = StockRequest.objects.filter(
        supplier=request.user,
        status__in=['PENDING', 'APPROVED']
    ).order_by('-created_at')
    
    return render(request, 'store/admin_stock_requests.html', {
        'stock_requests': stock_requests
    })

@login_required
def delivery_progression(request):
    if request.user.role != 'SUPPLIER':
        messages.error(request, 'Access denied. Supplier access only.')
        return redirect('home')
    
    # Get all approved, in-transit, and delivered stock requests for this supplier
    stock_requests = StockRequest.objects.filter(
        supplier=request.user,
        status__in=['APPROVED', 'IN_TRANSIT', 'DELIVERED']
    ).order_by('-created_at')
    
    # Get delivery information for each request
    delivery_info = {}
    for stock_request in stock_requests:
        delivery = StockDelivery.objects.filter(stock_request=stock_request).first()
        if delivery:
            delivery_info[stock_request.id] = delivery
    
    return render(request, 'store/delivery_progression.html', {
        'stock_requests': stock_requests,
        'delivery_info': delivery_info
    })

@login_required
@require_POST
def handle_stock_request(request, action, request_id):
    if request.user.role != 'SUPPLIER':
        return JsonResponse({'success': False, 'error': 'Access denied. Supplier access only.'})
    
    try:
        stock_request = StockRequest.objects.get(id=request_id, supplier=request.user)
    except StockRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Stock request not found.'})
    
    try:
        if action == 'accept':
            if stock_request.status != 'PENDING':
                return JsonResponse({'success': False, 'error': 'Can only accept pending requests.'})
            
            stock_request.status = 'APPROVED'
            stock_request.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Stock Request Accepted',
                details=f'Request #{request_id} for {stock_request.product.name}'
            )
            
            return JsonResponse({'success': True, 'message': 'Stock request accepted successfully.'})
        
        elif action == 'reject':
            if stock_request.status != 'PENDING':
                return JsonResponse({'success': False, 'error': 'Can only reject pending requests.'})
            
            stock_request.status = 'REJECTED'
            stock_request.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Stock Request Rejected',
                details=f'Request #{request_id} for {stock_request.product.name}'
            )
            
            return JsonResponse({'success': True, 'message': 'Stock request rejected successfully.'})
        
        elif action == 'start-delivery':
            if stock_request.status != 'APPROVED':
                return JsonResponse({'success': False, 'error': 'Can only start delivery for approved requests.'})
            
            stock_request.status = 'IN_TRANSIT'
            stock_request.save()
            
            # Create a delivery record
            StockDelivery.objects.create(
                stock_request=stock_request,
                status='IN_TRANSIT',
                supplier=request.user
            )
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Delivery Started',
                details=f'Request #{request_id} for {stock_request.product.name}'
            )
            
            return JsonResponse({'success': True, 'message': 'Delivery started successfully.'})
        
        elif action == 'complete-delivery':
            if stock_request.status != 'IN_TRANSIT':
                return JsonResponse({'success': False, 'error': 'Can only complete delivery for in-transit requests.'})
            
            stock_request.status = 'DELIVERED'
            stock_request.save()
            
            # Update delivery record
            delivery = StockDelivery.objects.filter(stock_request=stock_request).first()
            if delivery:
                delivery.status = 'DELIVERED'
                delivery.delivery_date = timezone.now()
                delivery.save()
            
            # Update product stock
            product = stock_request.product
            product.stock_quantity += stock_request.quantity
            product.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Delivery Completed',
                details=f'Request #{request_id} for {stock_request.product.name}'
            )
            
            return JsonResponse({'success': True, 'message': 'Delivery completed successfully.'})
        
        elif action == 'add-notes':
            # Get notes from request body
            data = json.loads(request.body)
            notes = data.get('notes', '')
            
            delivery = StockDelivery.objects.filter(stock_request=stock_request).first()
            if delivery:
                delivery.notes = notes
                delivery.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='Delivery Notes Updated',
                    details=f'Notes added for Request #{request_id}'
                )
                
                return JsonResponse({'success': True, 'message': 'Delivery notes updated successfully.'})
            else:
                return JsonResponse({'success': False, 'error': 'Delivery record not found.'})
        
        elif action == 'cancel-delivery':
            if stock_request.status not in ['APPROVED', 'IN_TRANSIT']:
                return JsonResponse({'success': False, 'error': 'Can only cancel approved or in-transit deliveries.'})
            
            stock_request.status = 'CANCELLED'
            stock_request.save()
            
            # Update the delivery record if it exists
            delivery = StockDelivery.objects.filter(stock_request=stock_request).first()
            if delivery:
                delivery.status = 'CANCELLED'
                delivery.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='Delivery Cancelled',
                details=f'Request #{request_id} for {stock_request.product.name}'
            )
            
            return JsonResponse({'success': True, 'message': 'Delivery cancelled successfully.'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action.'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
