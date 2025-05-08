from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Product(models.Model):
    name        = models.CharField(max_length=255)
    description = models.TextField()
    price       = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    image       = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_PENDING               = 'Pending'
    STATUS_AWAITING_CONFIRMATION = 'Awaiting Confirmation'
    STATUS_CONFIRMED             = 'Confirmed'
    STATUS_CANCELLED             = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING,               'Pending'),
        (STATUS_AWAITING_CONFIRMATION, 'Awaiting Confirmation'),
        (STATUS_CONFIRMED,             'Confirmed'),
        (STATUS_CANCELLED,             'Cancelled'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity    = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    ordered_at  = models.DateTimeField(auto_now_add=True)
    status      = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    receipt     = models.ImageField(upload_to='receipts/', null=True, blank=True)
    note        = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Compute total_price before saving
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} — {self.product.name} ({self.status})"
