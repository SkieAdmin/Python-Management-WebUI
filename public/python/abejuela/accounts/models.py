from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Customer.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_customer(sender, instance, **kwargs):
    if not instance.is_staff:
        try:
            instance.customer.save() 
        except Customer.DoesNotExist:
            Customer.objects.create(user=instance)
