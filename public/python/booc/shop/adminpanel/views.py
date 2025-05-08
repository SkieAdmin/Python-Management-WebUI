# shop/adminpanel/views.py
from django.shortcuts               import render, redirect, get_object_or_404
from django.contrib                 import messages
from django.contrib.auth            import logout
from django.contrib.auth.decorators import user_passes_test
from django.http                    import JsonResponse
from django.template.loader         import render_to_string
from django import forms

from shop.models import Product, Order, Payment
from shop.forms  import PaymentForm

staff_only = user_passes_test(lambda u: u.is_staff, login_url='shop_admin:login')

def logout_view(request):
    logout(request)
    return redirect('shop_admin:login')

@staff_only
def dashboard(request):
    stats = {
        'products': Product.objects.count(),
        'orders':   Order.objects.count(),
        'payments': Payment.objects.count(),
    }
    recent_orders = Order.objects.order_by('-ordered_at')[:5]
    return render(request, 'shop/adminpanel/dashboard.html', {
        'products': stats['products'],
        'orders':   stats['orders'],
        'payments': stats['payments'],
        'recent_orders': recent_orders,
    })

def _handle_modal(request, FormCls, instance, tpl):
    if request.method == 'POST':
        form = FormCls(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    else:
        form = FormCls(instance=instance)
    html = render_to_string(tpl, {'form': form, 'editing': bool(instance)}, request)
    return JsonResponse({'success': False, 'html': html})

# ─── PRODUCTS ───────────────────────────────────────────
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','price','image','available']

@staff_only
def product_list(request):
    return render(request, 'shop/adminpanel/products.html', {
        'products': Product.objects.order_by('name')
    })

@staff_only
def product_form(request, pk=None):
    inst = get_object_or_404(Product, pk=pk) if pk else None
    return _handle_modal(request, ProductForm, inst,
                         'shop/adminpanel/includes/product_form.html')

@staff_only
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, "Product deleted.")
    return redirect('shop_admin:product_list')

# ─── ORDERS ───────────────────────────────────────────
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product','customer_name','customer_email',
                  'scheduled_for','quantity','notes','status']

@staff_only
def order_list(request):
    return render(request, 'shop/adminpanel/orders.html', {
        'orders': Order.objects.order_by('-ordered_at')
    })

@staff_only
def order_form(request, pk=None):
    inst = get_object_or_404(Order, pk=pk) if pk else None
    return _handle_modal(request, OrderForm, inst,
                         'shop/adminpanel/includes/order_form.html')

@staff_only
def order_delete(request, pk):
    get_object_or_404(Order, pk=pk).delete()
    messages.success(request, "Order deleted.")
    return redirect('shop_admin:order_list')

# ─── PAYMENTS ───────────────────────────────────────────
@staff_only
def payment_list(request):
    return render(request, 'shop/adminpanel/payments.html', {
        'payments': Payment.objects.order_by('-created_at')
    })

@staff_only
def payment_form(request, pk=None):
    inst = get_object_or_404(Payment, pk=pk) if pk else None
    return _handle_modal(request, PaymentForm, inst,
                         'shop/adminpanel/includes/payment_form.html')

@staff_only
def payment_delete(request, pk):
    Payment.objects.filter(pk=pk).delete()
    messages.success(request, "Payment deleted.")
    return redirect('shop_admin:payment_list')
