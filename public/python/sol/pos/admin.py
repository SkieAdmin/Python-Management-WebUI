from django.contrib import admin
from .models import *

admin.site.register(Employee)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Receipt)
admin.site.register(Inventory)
# admin.site.register(SalesReport)
