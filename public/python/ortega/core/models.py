from django.db import models  # Core Django model functionality
from django.contrib.auth.models import AbstractUser  # Base user model to extend
from django.utils import timezone  # For handling dates and times

# -------------------------------
# AUTHENTICATION: Custom User
# -------------------------------
class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's built-in AbstractUser.
    Adds a role field to distinguish between customers and administrators.
    Inherits standard fields like username, email, password, first_name, last_name, etc.
    """
    # Define available user roles in the system
    ROLE_CHOICES = (
        ('Customer', 'Customer'),  # Regular customers who can browse and purchase products
        ('Administrator', 'Administrator'),  # Administrators who can manage inventory and orders
    )
    # Role field to determine user permissions and access levels
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Customer')

    def __str__(self):
        """String representation of the user showing username and role"""
        return f"{self.username} ({self.role})"


# -------------------------------
# PRODUCT MODEL
# -------------------------------
class Product(models.Model):
    """
    Product model representing items in the hardware store inventory.
    Stores product details, pricing, stock information, and categorization.
    """
    name = models.CharField(max_length=255)  # Product name (e.g., 'Hammer', 'Screwdriver Set')
    description = models.TextField()  # Detailed product description
    unit = models.CharField(max_length=50)  # Unit of measurement (e.g., 'piece', 'kg', 'meter')
    category = models.CharField(max_length=100)  # Product category (e.g., 'Tools', 'Lumber', 'Cement')
    stock_quantity = models.PositiveIntegerField()  # Current quantity in stock
    reorder_level = models.PositiveIntegerField()  # Threshold at which to reorder product
    last_restock_date = models.DateField(default=timezone.now)  # Date of last inventory restock
    admin = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,  # Delete products if the admin user is deleted
        limit_choices_to={'role': 'Administrator'}  # Only administrators can be assigned to products
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Product price
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Product image
    in_stock = models.BooleanField(default=True)  # Whether the product is currently in stock

    def __str__(self):
        """String representation of the product showing its name"""
        return self.name

    def update_stock(self, quantity):
        """
        Update the product's stock quantity and in_stock status.
        
        Args:
            quantity (int): The quantity to subtract from current stock
        """
        self.stock_quantity -= quantity  # Reduce stock by the specified quantity
        self.in_stock = self.stock_quantity > 0  # Update in_stock status based on remaining quantity
        self.save()  # Save changes to the database


# -------------------------------
# ORDER MODEL
# -------------------------------
class Order(models.Model):
    """
    Order model representing customer purchases.
    Tracks order details, status, customer information, and total amount.
    Individual items in the order are stored in the OrderItem model.
    """
    # Define possible order statuses
    STATUS_CHOICES = (
        ('Pending', 'Pending'),  # Order placed but not processed yet
        ('Processing', 'Processing'),  # Order is being processed
        ('Completed', 'Completed'),  # Order has been fulfilled and delivered
        ('Cancelled', 'Cancelled'),  # Order was cancelled
    )
    # Link to the customer who placed the order
    customer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,  # Delete orders if the customer is deleted
        limit_choices_to={'role': 'Customer'}  # Only customers can place orders
    )
    order_date = models.DateTimeField(auto_now_add=True)  # Date and time when order was placed
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Total order amount
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')  # Current order status

    def __str__(self):
        """String representation of the order showing order ID and customer"""
        return f"Order #{self.pk} by {self.customer.username}"
    
    @classmethod
    def create_from_cart(cls, cart, status='Pending'):
        """
        Class method to create a new order from a shopping cart.
        Transfers all items from the cart to a new order and updates product stock.
        
        Args:
            cart: The Cart object to convert to an order
            status: Initial status for the order (default: 'Pending')
            
        Returns:
            The newly created Order object
        """
        # Create the order with information from the cart
        order = cls.objects.create(
            customer=cart.customer,  # Customer who owns the cart
            total_amount=cart.get_total_price(),  # Total price of all items in cart
            status=status  # Initial order status
        )
        
        # Create order items from cart items (transfer items to order)
        for cart_item in cart.cartitem_set.all():
            # Create an order item for each cart item
            OrderItem.objects.create(
                order=order,  # Link to the parent order
                product=cart_item.product,  # Product being ordered
                quantity=cart_item.quantity,  # Quantity ordered
                price=cart_item.product.price  # Price at time of order
            )
            
            # Update product stock quantities
            cart_item.product.update_stock(cart_item.quantity)  # Reduce product stock
        
        # Clear the cart after creating the order
        cart.clear()  # Remove all items from cart
        
        return order  # Return the newly created order


# -------------------------------
# ORDER ITEM MODEL
# -------------------------------
class OrderItem(models.Model):
    """
    OrderItem model representing individual products within an order.
    Each order can have multiple order items, each linked to a specific product.
    Stores quantity and price at time of order (in case product price changes later).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Link to the parent order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Product being ordered
    quantity = models.PositiveIntegerField()  # Quantity of this product ordered
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def __str__(self):
        """String representation showing quantity, product name, and order ID"""
        return f"{self.quantity} x {self.product.name} in Order #{self.order.pk}"

    def get_total_price(self):
        """Calculate the total price for this order item (quantity * price)"""
        return self.quantity * self.price


# -------------------------------
# PAYMENT MODEL
# -------------------------------
class Payment(models.Model):
    """
    Payment model representing payment information for an order.
    Tracks payment method, amount, date, and status.
    Each order can have one payment record.
    """
    # Define available payment methods
    PAYMENT_METHOD_CHOICES = (
        ('Cash', 'Cash'),  # Cash payment on delivery
        ('Credit Card', 'Credit Card'),  # Credit card payment
        ('Debit Card', 'Debit Card'),  # Debit card payment
        ('GCash', 'GCash'),  # GCash mobile payment
        ('PayMaya', 'PayMaya'),  # PayMaya mobile payment
        ('Bank Transfer', 'Bank Transfer'),  # Bank transfer payment
    )
    
    # Define possible payment statuses
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),  # Payment initiated but not confirmed
        ('Completed', 'Completed'),  # Payment successfully processed
        ('Failed', 'Failed'),  # Payment failed to process
        ('Refunded', 'Refunded'),  # Payment was refunded to customer
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Link to the order being paid for
    payment_date = models.DateTimeField(default=timezone.now)  # Date and time of payment
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Payment amount
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='Cash')  # Method of payment
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Pending')  # Current payment status
    admin = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'Administrator'}, 
        null=True, 
        blank=True  # Optional link to admin who processed the payment
    )
    reference_number = models.CharField(max_length=100, blank=True, null=True)  # Payment reference number (e.g., receipt number)

    def __str__(self):
        """String representation showing payment amount and order ID"""
        return f"Payment of ₱{self.amount} for Order #{self.order.pk}"
        
    @classmethod
    def create_from_order(cls, order, payment_method='Cash', admin=None):
        """
        Class method to create a payment record from an order.
        
        Args:
            order: The Order object being paid for
            payment_method: Method of payment (default: 'Cash')
            admin: Administrator processing the payment (optional)
            
        Returns:
            The newly created Payment object
        """
        payment = cls.objects.create(
            order=order,  # Link to the order
            amount=order.total_amount,  # Payment amount matches order total
            payment_method=payment_method,  # Method of payment specified
            payment_status='Completed',  # Mark payment as completed
            admin=admin,  # Administrator who processed the payment
            reference_number=f"PAY-{order.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}"  # Generate unique reference number
        )
        
        # Update order status to completed since payment is complete
        order.status = 'Completed'  # Mark order as completed
        order.save()  # Save changes to the database
        
        return payment  # Return the newly created payment


# -------------------------------
# STORE MODEL
# -------------------------------
class Store(models.Model):
    """
    Store model representing the hardware store's information.
    Used for displaying contact information and store details.
    Designed as a singleton - only one store record should exist.
    """
    name = models.CharField(max_length=100, default="Iligan2L Hardware")  # Store name
    address = models.TextField(default="123 Main Street, Iligan City, Philippines")  # Store address
    phone = models.CharField(max_length=20, default="+63 912 345 6789")  # Contact phone number
    email = models.EmailField(default="info@iligan2l.com")  # Contact email address
    
    # Since we only need one store record (singleton pattern)
    @classmethod
    def get_store_settings(cls):
        """
        Class method to get or create the store settings.
        Ensures only one store record exists by always using ID 1.
        
        Returns:
            The Store object with store information
        """
        store, created = cls.objects.get_or_create(pk=1)  # Always use ID 1 for the store
        return store  # Return the store object
    
    def __str__(self):
        """String representation showing the store name"""
        return self.name


# -------------------------------
# INVENTORY MODEL
# -------------------------------
class Inventory(models.Model):
    """
    Inventory model for tracking product stock levels.
    Note: This model is complementary to the stock_quantity field in Product model.
    Used for more detailed inventory tracking and history.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Link to the product
    quantity = models.PositiveIntegerField()  # Current quantity in inventory
    reorder_level = models.PositiveIntegerField()  # Threshold at which to reorder
    last_restock_date = models.DateField()  # Date of last inventory restock
    admin = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'Administrator'}  # Only administrators can manage inventory
    )

    def __str__(self):
        """String representation showing product name and quantity"""
        return f"Inventory of {self.product.name}: {self.quantity}"


# -------------------------------
# CART MODEL
# -------------------------------
class Cart(models.Model):
    """
    Cart model representing a customer's shopping cart.
    Each customer can have one active cart at a time.
    Contains cart items (CartItem) for individual products.
    """
    customer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'Customer'}  # Only customers can have carts
    )
    created_at = models.DateTimeField(auto_now_add=True)  # When the cart was created
    updated_at = models.DateTimeField(auto_now=True)  # When the cart was last updated
    is_active = models.BooleanField(default=True)  # Whether the cart is active or checked out
    
    def __str__(self):
        """String representation showing the customer's username"""
        return f"Cart for {self.customer.username}"
    
    def get_total_price(self):
        """
        Calculate the total price of all items in the cart.
        
        Returns:
            Decimal: The sum of all cart items' total prices
        """
        return sum(item.get_total_price() for item in self.cartitem_set.all())
    
    def get_total_items(self):
        """
        Count the total number of items in the cart.
        
        Returns:
            int: The sum of all cart items' quantities
        """
        return sum(item.quantity for item in self.cartitem_set.all())
    
    def clear(self):
        """Remove all items from the cart by deleting all cart items"""
        self.cartitem_set.all().delete()


# -------------------------------
# CART ITEM MODEL
# -------------------------------
class CartItem(models.Model):
    """
    CartItem model representing individual products in a shopping cart.
    Each cart can have multiple cart items, each linked to a specific product.
    Tracks quantity and when the item was added to the cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)  # Link to the parent cart
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Product in the cart
    quantity = models.PositiveIntegerField(default=1)  # Quantity of this product in cart
    added_at = models.DateTimeField(auto_now_add=True)  # When the item was added to cart
    
    class Meta:
        # Ensure a product can only appear once in a cart (update quantity instead)
        unique_together = ('cart', 'product')
    
    def __str__(self):
        """String representation showing quantity, product name, and cart"""
        return f"{self.quantity} x {self.product.name} in {self.cart}"
    
    def get_total_price(self):
        """
        Calculate the total price for this cart item (quantity * price).
        
        Returns:
            Decimal: The product price multiplied by quantity
        """
        return self.product.price * self.quantity


class Activity(models.Model):
    """
    Model to track various activities in the system for the activity feed.
    This includes order status changes, product restocks, and other notable events.
    """
    # Activity types for categorization and styling
    ACTIVITY_TYPES = (
        ('order', 'Order'),
        ('product', 'Product'),
        ('user', 'User'),
    )
    
    type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='order')
    title = models.CharField(max_length=255)  # Description of the activity
    timestamp = models.DateTimeField(auto_now_add=True)  # When the activity occurred
    
    class Meta:
        verbose_name_plural = 'Activities'
        ordering = ['-timestamp']  # Most recent first
    
    def __str__(self):
        """String representation of the activity"""
        return self.title
