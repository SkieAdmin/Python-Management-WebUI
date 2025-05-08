from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('inventory', 'Inventory'),
        ('system', 'System'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='system'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
