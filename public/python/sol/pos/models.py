from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
# Admin is the Django User with is_staff=True

class Employee(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('cashier', 'Cashier')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.price}"

    def __str__(self):
        return f"{self.name} - {self.price}"

class Order(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], default='pending')

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def total_price(self):
        return sum(item.total_price() for item in self.orderitem_set.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        return self.product.price * self.quantity

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment')
    ])
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"

class Receipt(models.Model):
    payment = models.OneToOneField('Payment', on_delete=models.CASCADE, null=True, blank=True)
    receipt_number = models.CharField(max_length=100, unique=True)
    printed_at = models.DateTimeField(auto_now_add=True)
    order = models.OneToOneField('Order', on_delete=models.CASCADE, null=True)
    payment_method = models.CharField(max_length=50, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    date_issued = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Receipt #{self.receipt_number}"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity_in_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_in_stock} in stock"

# class SalesReport(models.Model):
#     date = models.DateField()
#     total_sales = models.DecimalField(max_digits=10, decimal_places=2)
#     total_orders = models.PositiveIntegerField()
#     generated_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Sales Report - {self.date}"

from django.db import models
from django.utils import timezone

class StockAdjustment(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=10, choices=[('add', 'Add'), ('remove', 'Remove'), ('set', 'Set')])
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.adjustment_type} {self.quantity} on {self.timestamp}"
