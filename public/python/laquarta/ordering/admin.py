from django.contrib import admin
from django.utils.html import format_html
from .models import MenuItem, Order, Reservation


# MenuItem Admin
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']


# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'item', 'quantity', 'status', 'payment_status', 'date_time']
    list_filter = ['status', 'payment_status', 'date_time']
    search_fields = ['customer__username', 'item__name']
    list_editable = ['payment_status']  # Allow editing payment status directly in the list view

    # Add custom actions for bulk update of payment status
    actions = ['mark_as_paid', 'mark_as_unpaid']

    # Action to mark orders as paid
    def mark_as_paid(self, request, queryset):
        updated_count = queryset.update(payment_status='Paid')
        self.message_user(request, f"{updated_count} selected order(s) have been marked as Paid.")

    # Action to mark orders as unpaid
    def mark_as_unpaid(self, request, queryset):
        updated_count = queryset.update(payment_status='Unpaid')
        self.message_user(request, f"{updated_count} selected order(s) have been marked as Unpaid.")

    # Descriptions for custom actions
    mark_as_paid.short_description = "Mark selected orders as Paid"
    mark_as_unpaid.short_description = "Mark selected orders as Unpaid"

    # Restrict payment status actions to admin users only
    def get_actions(self, request):
        actions = super().get_actions(request)

        # Only allow these actions if the user is a superuser
        if not request.user.is_superuser:
            if 'mark_as_paid' in actions:
                del actions['mark_as_paid']
            if 'mark_as_unpaid' in actions:
                del actions['mark_as_unpaid']

        return actions


# Reservation Admin
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'customer',
        'kilos',
        'price',
        'delivery_fee',
        'calculate_total_price_display',
        'delivery_option',
        'package_deal',
        'status',
        'payment_status',
        'delivery_date',
        'reserved_at',
        'gcash_remarks'  # Display GCash screenshot in the admin
    ]
    list_filter = ['status', 'payment_status', 'delivery_option', 'delivery_date']
    search_fields = ['customer__username', 'kilos', 'package_deal']

    # Display calculated total price in the admin
    @admin.display(description='Total Price')
    def calculate_total_price_display(self, obj):
        return obj.calculate_total_price()

    # Display GCash remarks (receipt screenshot or message)
    @admin.display(description='Remarks (GCash Receipt)')
    def gcash_remarks(self, obj):
        if obj.gcash_screenshot:
            # Display GCash screenshot as an image in the admin
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: contain;" />',
                obj.gcash_screenshot.url
            )
        return "No receipt submitted"