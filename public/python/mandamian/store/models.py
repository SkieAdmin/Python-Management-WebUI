from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
        ('SUPPLIER', 'Supplier')
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    phone = models.CharField(max_length=15, blank=True)

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def update_stock(self, quantity):
        self.stock = quantity
        self.save()
        return True

class StockRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stock_requests')
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplier_requests', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Stock Request for {self.product.name} - {self.quantity} units'

class StockDelivery(models.Model):
    STATUS_CHOICES = [
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]

    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE)
    delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_TRANSIT')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Delivery for {self.stock_request}'

    def update_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart for {self.user.username}'

    def get_total(self):
        return sum(item.get_total() for item in self.cartitem_set.all())

    def clear(self):
        self.cartitem_set.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def get_total(self):
        return self.product.price * self.quantity

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('GCASH', 'GCash'),
        ('COD', 'Cash on Delivery')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    processing_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_id = models.CharField(max_length=100)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='WAITING')
    created_at = models.DateTimeField(auto_now_add=True)

class Supply(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]
    supplier = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    expected_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('PROCESSING', 'Processing'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Delivery for Order #{self.transaction.id}'


class StoreSettings(models.Model):
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    gcash_number = models.CharField(max_length=15, blank=True)
    gcash_name = models.CharField(max_length=100, blank=True)
    gcash_qr_code = models.ImageField(upload_to='store/', null=True, blank=True)
    
    def __str__(self):
        return 'Store Settings'


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
