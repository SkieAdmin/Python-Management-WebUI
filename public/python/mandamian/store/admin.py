from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Transaction, TransactionItem, Payment, Supply, AuditLog

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )

class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 1

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [TransactionItemInline]

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'amount', 'reference_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')

class SupplyAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'quantity', 'status', 'expected_arrival', 'actual_arrival')
    list_filter = ('status', 'expected_arrival', 'actual_arrival')

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('action', 'details')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Supply, SupplyAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
