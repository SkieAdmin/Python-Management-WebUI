from django.contrib import admin
from .models import Order, OrderItem, PaymentTransaction

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'status', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('customer__user__username', 'customer__user__email')
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline, PaymentTransactionInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'price_at_order', 'subtotal')
    list_filter = ('order__order_date',)
    search_fields = ('order__id', 'item__name')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'transaction_date', 'processed_by')
    list_filter = ('payment_method', 'transaction_date')
    search_fields = ('order__id', 'reference_number')
    date_hierarchy = 'transaction_date'
