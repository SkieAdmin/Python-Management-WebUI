from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Order, OrderItem, PaymentTransaction
from .forms import OrderNoteForm, OrderItemForm, PaymentForm, OrderStatusForm, PaymentStatusForm
from inventory.models import Inventory
from notifications.models import Notification

def menu(request):
    menu_items = Inventory.objects.filter(is_available=True).order_by('name')
    return render(request, 'orders/menu.html', {'menu_items': menu_items})

@login_required
def create_order(request):
    if request.user.is_staff:
        messages.error(request, 'Staff cannot create orders.')
        return redirect('dashboard')
    
    try:
        customer = request.user.customer
    except:
        messages.error(request, 'You need to complete your profile before ordering.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = OrderNoteForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                customer=customer,
                notes=form.cleaned_data['notes']
            )
            
            cart = request.session.get('cart', {})
            
            for item_id, quantity in cart.items():
                try:
                    item = Inventory.objects.get(id=item_id)
                    OrderItem.objects.create(
                        order=order,
                        item=item,
                        quantity=quantity,
                        price_at_order=item.price
                    )
                except Inventory.DoesNotExist:
                    pass
            
        
            request.session['cart'] = {}
            
            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_detail', pk=order.id)
    else:
        form = OrderNoteForm()
    

    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    

    for item_id, quantity in cart.items():
        try:
            item = Inventory.objects.get(id=item_id)
            subtotal = item.price * quantity
            cart_items.append({
                'item': item,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except Inventory.DoesNotExist:
            pass
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'total': total
    }
    
    return render(request, 'orders/create_order.html', context)

@login_required
def add_to_cart(request, pk):
    if request.user.is_staff:
        messages.error(request, 'Staff cannot add items to cart.')
        return redirect('dashboard')
    
    item = get_object_or_404(Inventory, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    

    cart = request.session.get('cart', {})
    
  
    item_id = str(item.id)
    if item_id in cart:
        cart[item_id] += quantity
    else:
        cart[item_id] = quantity
    
 
    request.session['cart'] = cart
    
    messages.success(request, f'{item.name} added to cart.')
    return redirect('menu')

@login_required
def view_cart(request):
    
    if request.user.is_staff:
        messages.error(request, 'Staff cannot view cart.')
        return redirect('dashboard')
    

    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
  
    for item_id, quantity in cart.items():
        try:
            item = Inventory.objects.get(id=item_id)
            subtotal = item.price * quantity
            cart_items.append({
                'item': item,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
        except Inventory.DoesNotExist:
            pass
    
    context = {
        'cart_items': cart_items,
        'total': total
    }
    
    return render(request, 'orders/cart.html', context)

@login_required
def remove_from_cart(request, pk):
 
    if request.user.is_staff:
        messages.error(request, 'Staff cannot modify cart.')
        return redirect('dashboard')
    
 
    cart = request.session.get('cart', {})
    
  
    item_id = str(pk)
    if item_id in cart:
        del cart[item_id]
    
    
    request.session['cart'] = cart
    
    messages.success(request, 'Item removed from cart.')
    return redirect('view_cart')

@login_required
def order_detail(request, pk):

    order = get_object_or_404(Order, pk=pk)
    

    if not request.user.is_staff and request.user.customer != order.customer:
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('menu')
    
    context = {
        'order': order,
        'items': order.items.all(),
        'payments': order.payments.all()
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def customer_orders(request):
    if request.user.is_staff:
        return redirect('order_list')
    
    try:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer).order_by('-order_date')
    except:
        orders = []
    
    return render(request, 'orders/customer_orders.html', {'orders': orders})

@login_required
def update_order_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order #{order.id} status updated successfully!')
            return redirect('order_detail', pk=order.id)
    else:
        form = OrderStatusForm(instance=order)
    
    return render(request, 'orders/update_order_status.html', {'form': form, 'order': order})

@login_required
def update_payment_status(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = PaymentStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order #{order.id} payment status updated successfully!')
            return redirect('order_detail', pk=order.id)
    else:
        form = PaymentStatusForm(instance=order)
    
    return render(request, 'orders/update_payment_status.html', {'form': form, 'order': order})

@login_required
def make_payment(request, pk):
    """Make payment for an order"""
    order = get_object_or_404(Order, pk=pk)
    

    if not request.user.is_staff and request.user.customer != order.customer:
        messages.error(request, 'You do not have permission to make payment for this order.')
        return redirect('menu')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, order=order)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.save()
            
            messages.success(request, 'Payment submitted successfully! It will be processed shortly.')
            return redirect('order_detail', pk=order.id)
    else:
        form = PaymentForm(order=order)
    
    return render(request, 'orders/make_payment.html', {'form': form, 'order': order})
