from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification


class Inventory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    image = models.ImageField(upload_to='inventory/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    low_stock_threshold = models.PositiveIntegerField(default=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Inventory'
    
    def __str__(self):
        return self.name


class Supplies(models.Model):
    inventory = models.ForeignKey(
        Inventory, 
        on_delete=models.CASCADE,
        related_name='supplies'
    )
    
    supplier_name = models.CharField(max_length=100)
    quantity_supplied = models.PositiveIntegerField()
    supply_date = models.DateField()
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Supplies'
    
    def __str__(self):
        return f"{self.supplier_name} - {self.inventory.name} ({self.supply_date})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.inventory.quantity += self.quantity_supplied
            self.inventory.save()


@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, **kwargs):
    if instance.quantity <= instance.low_stock_threshold:
        staff_users = User.objects.filter(is_staff=True)
        
        for user in staff_users:
            Notification.objects.create(
                user=user,
                message=f"Low stock alert: {instance.name} has only {instance.quantity} items left.",
                notification_type='inventory'
            )
