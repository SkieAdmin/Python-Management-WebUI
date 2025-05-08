from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    landmark = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.full_name


# MenuItem Model
# In your models.py
class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)
    available = models.BooleanField(default=True)  # This field needs to be added
    
    # Rest of your model...

    def __str__(self):
        return self.name


# Order Model
class Order(models.Model):
    # Choices for order status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Cancelled', 'Cancelled'),  # Added 'Cancelled' for flexibility
    ]

    # Choices for payment status
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    gcash_reference = models.CharField(max_length=50, blank=True, null=True)
    gcash_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order by {self.customer.username} - {self.item.name} (x{self.quantity})"

    def calculate_total_price(self):
        return self.quantity * self.item.price

    class Meta:
        ordering = ['-date_time']  # Orders the records by date_time in descending order


# Reservation Model
class Reservation(models.Model):
    # Choices for reservation status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Cancelled', 'Cancelled'),  # Added 'Cancelled' for flexibility
    ]

    # Choices for payment status
    PAYMENT_STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
    ]

    # Choices for package deals
    PACKAGE_DEAL_CHOICES = [
        ('paklay', 'Paklay'),
        ('dinuguan', 'Dinuguan'),
        ('none', 'None'),
    ]

    # Choices for delivery options
    DELIVERY_OPTION_CHOICES = [
        ('pickup', 'Pick-up'),
        ('door', 'Door-to-Door'),
    ]

    

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")
    kilos = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Unpaid')
    reserved_at = models.DateTimeField(auto_now_add=True)
    package_deal = models.CharField(max_length=20, choices=PACKAGE_DEAL_CHOICES, default='none')
    delivery_option = models.CharField(max_length=20, choices=DELIVERY_OPTION_CHOICES, default='pickup')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gcash_reference = models.CharField(max_length=100, blank=True, null=True)
    gcash_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            profile = self.customer.profile  # Accessing the Profile model to get full name
            return f"Reservation by {profile.full_name} - {self.kilos}kg on {self.delivery_date}"
        except Profile.DoesNotExist:
            return f"Reservation by {self.customer.username} - {self.kilos}kg on {self.delivery_date}"

    def calculate_total_price(self):
        return self.price + (self.delivery_fee if self.delivery_option == 'door' else 0)

    class Meta:
        ordering = ['-reserved_at']  # Orders the records by reserved_at in descending order


        