import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iligan2l.settings')
django.setup()

# Import models
from django.utils import timezone
from core.models import Product, CustomUser

def add_test_product():
    # Get admin user
    try:
        admin_user = CustomUser.objects.filter(role='Administrator').first()
        if not admin_user:
            print("No admin user found. Please create an admin user first.")
            return
        
        # Create test product
        product = Product(
            name="Test Cement",
            description="High-quality cement for construction",
            unit="kg",
            category="cement",
            stock_quantity=100,
            reorder_level=10,
            last_restock_date=timezone.now(),
            admin=admin_user,
            price=350.00,
            in_stock=True
        )
        product.save()
        
        print(f"Test product created: {product.name}, ID: {product.id}")
        
    except Exception as e:
        print(f"Error creating test product: {str(e)}")

if __name__ == "__main__":
    add_test_product()
