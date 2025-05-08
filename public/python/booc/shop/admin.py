# shop/admin.py

from django.contrib import admin
from .models import Product, Order, Payment

class PaymentInline(admin.StackedInline):
    model = Payment
    fk_name = 'order'
    can_delete = False
    readonly_fields = ('full_name', 'email', 'address', 'contact', 'receipt', 'created_at')
    verbose_name = 'Payment'
    verbose_name_plural = 'Payment Details'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available')
    list_filter  = ('available',)
    search_fields= ('name',)
    actions      = ('make_available', 'make_unavailable')

    @admin.action(description="Mark selected products as Available")
    def make_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f"{updated} product(s) marked as available.")

    @admin.action(description="Mark selected products as Not available")
    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f"{updated} product(s) marked as not available.")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ('id', 'product', 'user', 'quantity', 'status', 'scheduled_for', 'ordered_at', 'customer_email')
    list_filter     = ('status', 'ordered_at')
    search_fields   = ('product__name', 'user__username', 'customer_name', 'customer_email')
    inlines         = [PaymentInline]
    readonly_fields = ('ordered_at', 'updated_at')
    fieldsets       = (
        (None, {'fields': ('product', 'user', 'quantity', 'status', 'scheduled_for')}),
        ('Customer Info', {'fields': ('customer_name', 'customer_email', 'customer_address', 'customer_contact')}),
        ('Notes',         {'fields': ('notes',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(self.readonly_fields)
        if obj and hasattr(obj, 'payment'):
            ro += ['customer_name', 'customer_email', 'customer_address', 'customer_contact']
        return ro

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display    = ('id', 'order', 'full_name', 'email', 'contact', 'created_at')
    list_filter     = ('created_at',)
    search_fields   = ('order__id', 'full_name', 'email', 'contact')
    readonly_fields = ('order', 'full_name', 'email', 'address', 'contact', 'receipt', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions
