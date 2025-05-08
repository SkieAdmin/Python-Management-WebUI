from django.contrib import admin
from .models import Inventory, Supplies

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'is_available', 'low_stock_threshold', 'created_at')
    list_filter = ('is_available', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')

@admin.register(Supplies)
class SuppliesAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'supplier_name', 'quantity_supplied', 'supply_date', 'cost', 'created_by')
    list_filter = ('supply_date', 'created_at')
    search_fields = ('inventory__name', 'supplier_name')
    date_hierarchy = 'supply_date'
