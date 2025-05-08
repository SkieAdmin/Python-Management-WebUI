# shop/models.py

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.db.models import ProtectedError

class Product(models.Model):
    name        = models.CharField(max_length=100)
    description = models.TextField()
    price       = models.DecimalField(max_digits=8, decimal_places=2)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)
    available   = models.BooleanField(
                      default=True,
                      help_text="Uncheck to hide this product from shoppers"
                  )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('order_product', kwargs={'product_id': self.pk})


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),

    ]

    product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                         related_name='orders', null=True, blank=True)
    customer_name    = models.CharField(max_length=100, default='', blank=True)
    customer_email   = models.EmailField(default='', blank=True)
    customer_address = models.TextField(default='', blank=True)
    customer_contact = models.CharField(max_length=50, default='', blank=True)
    scheduled_for    = models.DateTimeField(null=True)
    notes            = models.TextField(default='', blank=True)
    quantity         = models.PositiveIntegerField(default=1)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ordered_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.user:
            if not self.customer_email:
                self.customer_email = self.user.email or ''
            if not self.customer_name:
                full_name = self.user.get_full_name()
                self.customer_name = full_name or self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        uname = self.user.username if self.user else 'Anonymous'
        return f"Order #{self.id} by {uname} – {self.product.name} (x{self.quantity})"


class Payment(models.Model):
    order      = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    full_name  = models.CharField(max_length=200)
    email      = models.EmailField()
    address    = models.TextField()
    contact    = models.CharField(max_length=50)
    receipt    = models.ImageField(upload_to='receipts/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ('add', 'change', 'view')  # remove delete

    def __str__(self):
        return f"Payment for Order #{self.order.id}"

    def delete(self, *args, **kwargs):
        raise ProtectedError("Payments may not be deleted.", self)
