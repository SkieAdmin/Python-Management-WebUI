from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display   = ('name', 'price')
    search_fields  = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = (
        'id', 'user', 'product', 'quantity', 'total_price',
        'ordered_at', 'status', 'note', 'receipt_preview'
    )
    list_filter     = ('status', 'ordered_at', 'product')
    search_fields   = ('product__name', 'user__username', 'note')
    readonly_fields = ('total_price', 'ordered_at', 'receipt_preview')
    fieldsets       = (
        (None, {
            'fields': (
                'user', 'product', 'quantity', 'total_price',
                'ordered_at', 'status', 'note'
            )
        }),
        ('Receipt', {
            'fields': ('receipt', 'receipt_preview'),
            'description': 'Upload or change the payment receipt image here.'
        }),
    )
    actions         = (
        'mark_awaiting_confirmation',
        'mark_confirmed',
        'mark_cancelled',
    )

    def receipt_preview(self, obj):
        """Show a small preview of the uploaded receipt, if any."""
        if obj.receipt:
            return format_html(
                '<img src="{}" style="max-height:150px; border:1px solid #ddd; padding:4px;" />',
                obj.receipt.url
            )
        return "(no receipt)"
    receipt_preview.short_description = "Current Receipt"

    def mark_awaiting_confirmation(self, request, queryset):
        """Bulk action: Set status to 'Awaiting Confirmation'."""
        updated = queryset.update(status=Order.STATUS_AWAITING_CONFIRMATION)
        self.message_user(request, f"{updated} order(s) marked as Awaiting Confirmation.")
    mark_awaiting_confirmation.short_description = "Mark selected orders as Awaiting Confirmation"

    def mark_confirmed(self, request, queryset):
        """Bulk action: Set status to 'Confirmed'."""
        updated = queryset.update(status=Order.STATUS_CONFIRMED)
        self.message_user(request, f"{updated} order(s) marked as Confirmed.")
    mark_confirmed.short_description = "Mark selected orders as Confirmed"

    def mark_cancelled(self, request, queryset):
        """Bulk action: Set status to 'Cancelled'."""
        updated = queryset.update(status=Order.STATUS_CANCELLED)
        self.message_user(request, f"{updated} order(s) marked as Cancelled.")
    mark_cancelled.short_description = "Mark selected orders as Cancelled"
