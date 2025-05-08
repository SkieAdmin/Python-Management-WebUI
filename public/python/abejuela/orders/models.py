from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import Customer
from inventory.models import Inventory
from notifications.models import Notification


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_STATUS = (
        ('unpaid', 'Unpaid'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
    )
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='unpaid'
    )
    
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0
    )
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.user.username}"
    
    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='items'
    )
    item = models.ForeignKey(
        Inventory, 
        on_delete=models.CASCADE
    )
    
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(
        max_digits=8, 
        decimal_places=2
    )
    
    def __str__(self):
        return f"{self.quantity} x {self.item.name} in Order #{self.order.id}"
    
    @property
    def subtotal(self):
        return self.price_at_order * self.quantity
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        original_quantity = 0
        if not is_new:
            try:
                original = OrderItem.objects.get(pk=self.pk)
                original_quantity = original.quantity
            except OrderItem.DoesNotExist:
                pass
        
        if not self.price_at_order:
            self.price_at_order = self.item.price
            
        super().save(*args, **kwargs)
        
        if is_new:
            self.item.quantity = max(0, self.item.quantity - self.quantity)
            self.item.save()
        elif self.quantity != original_quantity:
            quantity_difference = self.quantity - original_quantity
            if quantity_difference > 0:
                self.item.quantity = max(0, self.item.quantity - quantity_difference)
                self.item.save()
            elif quantity_difference < 0:
                self.item.quantity += abs(quantity_difference)
                self.item.save()
        
        self.order.calculate_total()


class PaymentTransaction(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
    )
    
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True
    )
    
    receipt_image = models.ImageField(
        upload_to='receipts/', 
        blank=True, 
        null=True
    )
    
    notes = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='processed_payments'
    )
    
    def __str__(self):
        return f"Payment of {self.amount} for Order #{self.order.id}"




@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if created:
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=f"New order #{instance.id} received from {instance.customer.user.username}.",
                notification_type='order' 
            )
    else:

        Notification.objects.create(
            user=instance.customer.user,
            message=f"Your order #{instance.id} status has been updated to {instance.get_status_display()}.",
            notification_type='order' 
        )


@receiver(post_save, sender=PaymentTransaction)
def notify_payment_received(sender, instance, created, **kwargs):
  
    if created:
        
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=f"New payment of {instance.amount} received for Order #{instance.order.id}.",
                notification_type='payment' )
        

        if instance.order.payment_status == 'unpaid':
            instance.order.payment_status = 'processing'
            instance.order.save()
