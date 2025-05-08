# Import necessary Django modules and functions
from django.shortcuts import render, redirect, get_object_or_404  # For rendering templates, redirecting, and getting objects
from django.contrib.auth.decorators import login_required  # For restricting views to authenticated users
from django.contrib.auth import authenticate, login, logout  # For authentication functionality
from django.contrib import messages  # For flash messages
from django.http import JsonResponse, HttpResponse  # For returning JSON and HTTP responses
from django.db.models import Q, Sum, F  # For complex database queries
from django.utils import timezone  # For handling dates and times
import json  # For JSON serialization/deserialization

# Import models from the current application
from .models import Order, OrderItem, Product, CustomUser, Payment, Cart, CartItem
from .forms import AddProductForm, CustomRegisterForm  # Import forms for product management

# Profile view - Displays the user's profile information
@login_required  # Ensures only logged-in users can access this view
def profile_view(request):
    # Get all orders for the current user, ordered by most recent first
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')
    
    # Get order items for each order to display in the history
    for order in orders:
        # Add items as an attribute to each order for easy access in the template
        order.items = OrderItem.objects.filter(order=order)
    
    # Render the profile template with the current user's information and orders
    return render(request, 'core/profile.html', {
        'user': request.user,
        'orders': orders,
    })

# Landing page - Main entry point for the website
def landing_page(request):
    # Get search term and category from query parameters for filtering products
    search_term = request.GET.get('search', '')  # Get search term or empty string if not provided
    current_category = request.GET.get('category', '')  # Get category filter or empty string if not provided
    sort_by = request.GET.get('sort', 'newest')  # Default sort by newest if not specified
    
    # Get all products from the database
    products = Product.objects.all()
    
    # Apply search filter if provided - will be used to filter products by name or description
    if search_term:
        products = products.filter(name__icontains=search_term)
    
    # Apply category filter if provided
    if current_category:
        products = products.filter(category__iexact=current_category)
    
    # Apply sorting
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    else:  # newest
        products = products.order_by('-id')
    
    # Get distinct categories for the filter
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'search_term': search_term,
        'sort_by': sort_by
    }
    
    # Render the landing page template with the context data
    return render(request, 'core/landing_page.html', context)

# Informational pages - Static content pages
def about_page(request):
    # Render the about page template
    return render(request, 'core/about.html')

def contact_page(request):
    # Render the contact page template
    return render(request, 'core/contact.html')

# Auth views - Handle user authentication
def login_view(request):
    # Process login form submission
    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Authenticate the user against the database
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # If authentication successful, log the user in
            login(request, user)
            # Redirect based on user role
            if user.role == 'Administrator':
                return redirect('admin_dashboard')  # Admins go to admin dashboard
            else:  # Default to customer dashboard
                return redirect('customer_dashboard')  # Customers go to customer dashboard
        else:
            # If authentication failed, show error message
            messages.error(request, 'Invalid username or password')
    
    # If GET request or authentication failed, show login form
    return render(request, 'core/login.html')

def register_view(request):
    # Process registration form submission
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = CustomRegisterForm(request.POST)
        
        # Validate the form
        if form.is_valid():
            # Save the user with role set to Customer
            user = form.save(commit=False)
            user.role = 'Customer'
            user.save()
            
            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            # Redirect to customer dashboard
            messages.success(request, 'Registration successful! Welcome to Iligan2L Construction Supply.')
            return redirect('customer_dashboard')
        else:
            # If form is invalid, show error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # If GET request, create an empty form
        form = CustomRegisterForm()
    
    # Render the registration form
    return render(request, 'core/register.html', {'form': form})

def admin_register_view(request):
    # Render the administrator registration form
    return render(request, 'core/admin_register.html')

def logout_view(request):
    # Log the user out and clear their session
    logout(request)
    # Redirect to the home page after logout
    return redirect('home')

# Dashboard views - Different dashboards based on user role
@login_required  # Ensure user is logged in to access dashboard
def customer_dashboard(request):
    # Get query parameters for filtering and sorting products
    search_term = request.GET.get('search', '')  # Get search term from URL query parameters
    current_category = request.GET.get('category', '')  # Get category filter from URL
    sort_by = request.GET.get('sort', 'newest')  # Default sort is by newest products
    
    # Start with all products from the database
    products = Product.objects.all()
    
    # Apply search filter if provided - case-insensitive search in product names
    if search_term:
        products = products.filter(name__icontains=search_term)
    
    # Apply category filter if provided - exact match on category (case-insensitive)
    if current_category:
        products = products.filter(category__iexact=current_category)
    
    # Apply sorting based on the sort parameter
    if sort_by == 'name':
        products = products.order_by('name')  # Sort alphabetically by name
    elif sort_by == 'price_low':
        products = products.order_by('price')  # Sort by price, lowest first
    elif sort_by == 'price_high':
        products = products.order_by('-price')  # Sort by price, highest first
    else:  # newest
        products = products.order_by('-id')  # Sort by ID descending (newest first)
    
    # Get distinct categories for the category filter dropdown
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    # Prepare context data to pass to the template
    context = {
        'products': products,  # Filtered and sorted products
        'categories': categories,  # All available categories for filter dropdown
        'current_category': current_category,  # Currently selected category
        'search_term': search_term,  # Current search term
        'sort_by': sort_by  # Current sort method
    }
    
    # Render the customer dashboard template with the context data
    return render(request, 'core/customer_dashboard.html', context)

@login_required  # Ensure user is logged in to access dashboard
def staff_dashboard(request):
    # Get product statistics for dashboard overview
    total_products = Product.objects.count()  # Count total products
    total_customers = CustomUser.objects.filter(role='Customer').count()  # Count customers
    total_orders = Order.objects.count()  # Count all orders
    
    # Calculate total revenue from completed orders (same as customer management page)
    total_revenue = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get product categories data for pie chart visualization
    categories = Product.objects.values('category').distinct()  # Get unique categories
    category_stats = []  # Will hold category names for chart labels
    category_counts = []  # Will hold count of products in each category
    
    # Process each category to get counts for the pie chart
    for category in categories:
        category_name = category['category'].capitalize()  # Capitalize for display
        count = Product.objects.filter(category=category['category']).count()  # Count products in this category
        category_stats.append(category_name)  # Add to labels list
        category_counts.append(count)  # Add to data list
    
    # Get sales trend data for the last 6 months for line chart
    months = []  # Will hold month names for x-axis
    sales_data = []  # Will hold sales amounts for y-axis
    
    # Loop through last 6 months (5 months ago to current month)
    for i in range(5, -1, -1):
        # Calculate date for current month in the loop
        date = timezone.now() - timezone.timedelta(days=30 * i)
        month_name = date.strftime('%b')  # Format as short month name (e.g., Jan, Feb)
        months.append(month_name)  # Add to months list for chart
        
        # Calculate start and end dates for the month
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # First day of month
        if i > 0:
            # For past months, calculate the last day of the month
            next_month = month_start + timezone.timedelta(days=32)  # Go to next month
            month_end = next_month.replace(day=1) - timezone.timedelta(days=1, microseconds=1)  # Last day of current month
        else:
            # For current month, use current date as end date
            month_end = timezone.now()
        
        # Query database for completed payments in this month
        month_sales = Payment.objects.filter(
            payment_date__gte=month_start,  # Greater than or equal to start of month
            payment_date__lte=month_end,  # Less than or equal to end of month
            payment_status='Completed'  # Only count completed payments
        ).aggregate(Sum('amount'))['amount__sum'] or 0  # Sum amounts, default to 0 if None
        
        sales_data.append(float(month_sales))  # Add the month's sales to the data array
    
    # Get recent activities for the activity feed on the dashboard
    recent_activities = []  # Will hold combined activities for the feed
    
    # Try to get activities from the Activity model if the table exists
    try:
        from .models import Activity
        # Get activities from the Activity model
        db_activities = Activity.objects.all()[:5]  # Get 5 most recent activities
        
        # Add activities from the database
        for activity in db_activities:
            recent_activities.append({
                'type': activity.type,  # Activity type for styling
                'title': activity.title,  # Activity description
                'time': activity.timestamp.strftime('%b %d, %Y %H:%M')  # Formatted timestamp
            })
    except:
        # If Activity table doesn't exist yet, just continue without it
        pass
    
    # If we don't have enough activities from the database, add some from orders and products
    if len(recent_activities) < 5:
        # Get recent orders
        recent_orders = Order.objects.order_by('-order_date')[:3]
        
        # Add recent orders to activities list
        for order in recent_orders:
            recent_activities.append({
                'type': 'order',  # Activity type for styling
                'title': f'New order #{order.id} from {order.customer.username}',  # Activity description
                'time': order.order_date.strftime('%b %d, %Y %H:%M')  # Formatted timestamp
            })
        
        # Get recent product restocks
        recent_products = Product.objects.order_by('-last_restock_date')[:3]
        
        # Add recent product restocks to activities list
        for product in recent_products:
            recent_activities.append({
                'type': 'product',  # Activity type for styling
                'title': f'Product "{product.name}" was restocked',  # Activity description
                'time': product.last_restock_date.strftime('%b %d, %Y')  # Formatted timestamp
            })
    
    # Sort all activities by time and take the 5 most recent
    recent_activities = sorted(recent_activities, key=lambda x: x['time'], reverse=True)[:5]
    
    # Get products with low stock (at or below reorder level) for alerts
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('reorder_level')).order_by('stock_quantity')[:5]  # Get 5 products with lowest stock
    
    # Prepare context data for the dashboard template
    context = {
        'total_products': total_products,  # Total number of products in inventory
        'total_customers': total_customers,  # Total number of customer accounts
        'total_orders': total_orders,  # Total number of orders placed
        'total_revenue': total_revenue,  # Total revenue from completed payments
        'category_stats': json.dumps(category_stats),  # JSON string of category names for pie chart
        'category_counts': json.dumps(category_counts),  # JSON string of category counts for pie chart
        'months': json.dumps(months),  # JSON string of month labels for sales chart
        'sales_data': json.dumps(sales_data),  # JSON string of sales data for sales chart
        'recent_activities': recent_activities,  # List of recent orders and restocks
        'low_stock_products': low_stock_products  # Products that need to be restocked
    }
    
    # Render the staff dashboard template with the context data
    return render(request, 'core/staff_dashboard.html', context)

@login_required  # Ensure user is logged in to access dashboard
def admin_dashboard(request):
    # Handle product creation from the product form
    if request.method == 'POST':
        try:
            # Get form data submitted by the administrator
            name = request.POST.get('name')  # Product name
            description = request.POST.get('description')  # Product description
            category = request.POST.get('category')  # Product category
            unit = request.POST.get('unit')  # Unit of measurement (e.g., kg, piece)
            price = request.POST.get('price')  # Product price
            stock_quantity = request.POST.get('stock_quantity')  # Initial stock quantity
            reorder_level = request.POST.get('reorder_level')  # Level at which to reorder
            
            # Create new product instance with form data
            product = Product(
                name=name,  # Product name
                description=description,  # Product description
                category=category,  # Product category
                unit=unit,  # Unit of measurement
                price=price,  # Product price
                stock_quantity=stock_quantity,  # Initial stock quantity
                reorder_level=reorder_level,  # Reorder threshold
                admin=request.user,  # Set current user as the product admin
                in_stock=int(stock_quantity) > 0  # Set in_stock based on quantity
            )
            
            # Handle product image upload if provided
            if 'image' in request.FILES:
                product.image = request.FILES['image']  # Assign uploaded image to product
                
            # Save the product to the database
            product.save()
            # Show success message to the user
            messages.success(request, f'Product "${name}" added successfully!')
            # Redirect back to admin dashboard to see the new product
            return redirect('admin_dashboard')
        except Exception as e:
            # Handle any errors during product creation
            messages.error(request, f'Error adding product: {str(e)}')
    
    # Get query parameters for filtering and sorting products in the admin view
    search_term = request.GET.get('search', '')  # Get search term from URL query parameters
    current_category = request.GET.get('category', '')  # Get category filter from URL
    sort_by = request.GET.get('sort', 'newest')  # Default sort is by newest products
    
    # Start with all products from the database
    products = Product.objects.all()
    
    # Apply search filter if provided - case-insensitive search in product names
    if search_term:
        products = products.filter(name__icontains=search_term)  # Filter products containing search term
    
    # Apply category filter if provided - exact match on category (case-insensitive)
    if current_category:
        products = products.filter(category__iexact=current_category)  # Filter by selected category
    
    # Apply sorting based on the sort parameter
    if sort_by == 'name':
        products = products.order_by('name')  # Sort alphabetically by name
    elif sort_by == 'price_low':
        products = products.order_by('price')  # Sort by price, lowest first
    elif sort_by == 'price_high':
        products = products.order_by('-price')  # Sort by price, highest first (note the minus sign)
    else:  # newest first (default)
        products = products.order_by('-id')  # Sort by ID descending (newest first)
    
    # Get unique categories for the filter dropdown
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    # Prepare context data to pass to the template
    context = {
        'products': products,  # Filtered and sorted products
        'search_term': search_term,  # Current search term for maintaining state
        'current_category': current_category,  # Currently selected category
        'sort_by': sort_by,  # Current sort method
        'categories': categories,  # All available categories for filter dropdown
    }
    
    # Render the admin dashboard template with the context data
    return render(request, 'core/admin_dashboard.html', context)

@login_required  # Ensure user is logged in to access dashboard
def inventory_dashboard(request):
    # Get all products for inventory management
    products = Product.objects.all()
    
    # Calculate inventory statistics
    total_products = products.count()  # Total number of products
    in_stock_count = products.filter(stock_quantity__gt=0).count()  # Count of products with stock > 0
    
    # Get products with low stock (in stock but below or at reorder level)
    low_stock_products = [p for p in products if p.stock_quantity > 0 and p.stock_quantity <= p.reorder_level]
    low_stock_count = len(low_stock_products)  # Count of products with low stock
    
    # Count products that are completely out of stock
    out_of_stock_count = products.filter(stock_quantity=0).count()
    
    # Get unique categories for the filter dropdown in inventory view
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    # Prepare context data for the inventory dashboard template
    context = {
        'products': products,  # All products for inventory management
        'total_products': total_products,  # Total count of products
        'in_stock_count': in_stock_count,  # Count of products in stock
        'low_stock_count': low_stock_count,  # Count of products with low stock
        'out_of_stock_count': out_of_stock_count,  # Count of products out of stock
        'categories': categories,  # Categories for filtering
    }
    
    # Render the inventory dashboard template with the context data
    return render(request, 'core/inventory_dashboard.html', context)

@login_required  # Ensure user is logged in to access customer management
def customer_management(request):
    # Get all customers (users with role 'Customer')
    customers = CustomUser.objects.filter(role='Customer')
    
    # Get search parameter from URL query string
    search_term = request.GET.get('search', '')  # Default to empty string if not provided
    
    # If search term provided, filter customers by username, email, or name
    if search_term:
        # Use Q objects to create OR conditions in the filter
        customers = customers.filter(username__icontains=search_term) | \
                   customers.filter(email__icontains=search_term) | \
                   customers.filter(first_name__icontains=search_term) | \
                   customers.filter(last_name__icontains=search_term)  # Search across multiple fields
    
    # Calculate total revenue from all completed orders
    from django.db.models import Sum
    revenue = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Render the customer management template with the filtered customers and revenue data
    return render(request, 'core/customer_management.html', {
        'customers': customers,  # List of customers (filtered if search term provided)
        'search_term': search_term,  # Current search term for maintaining state
        'revenue': revenue  # Total revenue from completed orders
    })

@login_required  # Ensure user is logged in to access settings
def settings_dashboard(request):
    # Import Store model here to avoid circular imports
    from .models import Store
    # Get current store settings from database
    store = Store.get_store_settings()  # Uses the class method to get or create store settings
    
    # Handle form submissions for settings updates
    if request.method == 'POST':
        if 'update_profile' in request.POST:  # Check which form was submitted
            # Update user profile information
            user = request.user
            # Get form data with fallback to current values
            user.username = request.POST.get('username', user.username)  # Update username
            user.first_name = request.POST.get('first_name', user.first_name)  # Update first name
            user.last_name = request.POST.get('last_name', user.last_name)  # Update last name
            user.email = request.POST.get('email', user.email)  # Update email
            # Save changes to the database
            user.save()
            # Show success message to the user
            messages.success(request, 'Profile updated successfully!')
            
        elif 'update_store' in request.POST:  # Store settings form was submitted
            # Update store information
            store.name = request.POST.get('store_name', store.name)  # Update store name
            store.address = request.POST.get('store_address', store.address)  # Update address
            store.phone = request.POST.get('store_phone', store.phone)  # Update phone number
            store.email = request.POST.get('store_email', store.email)  # Update email address
            # Save changes to the database
            store.save()
            # Show success message to the user
            messages.success(request, 'Store settings updated successfully!')
            
        elif 'change_password' in request.POST:  # Password change form was submitted
            # Get password data from the form
            current_password = request.POST.get('current_password')  # Current password for verification
            new_password = request.POST.get('new_password')  # New password
            confirm_password = request.POST.get('confirm_password')  # Confirmation of new password
            
            # Validate password change request
            if not request.user.check_password(current_password):
                # Current password doesn't match what's in the database
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                # New password and confirmation don't match
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                # New password is too short
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                # All validation passed, update the password
                request.user.set_password(new_password)  # Set the new password (hashes it automatically)
                request.user.save()  # Save the user with the new password
                # Show success message and redirect to login
                messages.success(request, 'Password changed successfully. Please log in again.')
                return redirect('login')  # Redirect to login page since the session is invalidated
    
    # Render the settings dashboard template with user and store data
    return render(request, 'core/settings_dashboard.html', {
        'user': request.user,  # Current user data for the profile form
        'store': store  # Store settings data for the store form
    })

# Product views - Handle product display and management
@login_required  # Ensure user is logged in to view product details
def product_detail(request, pk):
    # Get the product by ID or return 404 if not found
    product = get_object_or_404(Product, pk=pk)
    
    # Check if user is authenticated to determine which template to use
    if not request.user.is_authenticated:
        # For non-logged in users, show the customer version of the product detail page
        template_name = 'core/product_detail_customer.html'
        is_customer = False
    else:
        # Determine if the user is a customer by checking their role
        is_customer = hasattr(request.user, 'role') and request.user.role == 'Customer'
        
        # Choose template based on user role - different templates for admin vs customer
        if request.user.role == 'Administrator' or request.user.is_staff:
            template_name = 'core/product_detail_admin.html'  # Admin view with edit options
        else:
            template_name = 'core/product_detail_customer.html'  # Customer view with purchase options
    
    # Get related products (same category) for product recommendations
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]  # Limit to 4 products
    
    # Render the appropriate template with product data
    return render(request, template_name, {
        'product': product,  # The main product being viewed
        'is_customer': is_customer,  # Whether the user is a customer (for UI customization)
        'related_products': related_products  # Related products for recommendations
    })

# Category-specific product pages
def cement_page(request):
    # Render the cement category page
    return render(request, 'core/cement.html')

def nails_page(request):
    # Render the nails category page
    return render(request, 'core/nails.html')

def lumber_page(request):
    # Render the lumber category page
    return render(request, 'core/lumber.html')

def tools_page(request):
    # This function renders the tools category page.
    # It is used to display products that belong to the 'tools' category.
    return render(request, 'core/tools.html')

@login_required
def edit_product(request, pk):
    # This function is used to edit existing products in the database.
    # It handles both GET and POST requests.
    # For GET requests, it renders the edit product form with the product's current data.
    # For POST requests, it updates the product's data in the database.
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = AddProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = AddProductForm(instance=product)
    
    return render(request, 'core/edit_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, pk):
    # This function is used to delete products from the database.
    # It handles both GET and POST requests.
    # For GET requests, it renders the delete product confirmation page.
    # For POST requests, it deletes the product from the database.
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    product.delete()
    messages.success(request, f'Product "{product_name}" has been deleted.')
    return redirect('admin_dashboard')

# Cart and checkout views - Handle shopping cart and checkout process
@login_required  # Ensure user is logged in to view cart
def cart_view(request):
    # Attempt to get the user's active cart and related information
    try:
        # Get the active cart for the current user
        cart = Cart.objects.get(customer=request.user, is_active=True)
        # Get all items in the cart
        cart_items = CartItem.objects.filter(cart=cart)
        # Calculate the total price of all items in the cart
        cart_total = cart.get_total_price()
    except Cart.DoesNotExist:
        # If no active cart exists, set default values
        cart = None
        cart_items = []
        cart_total = 0
    
    # Prepare context data for the cart template
    context = {
        'cart': cart,  # The cart object
        'cart_items': cart_items,  # Items in the cart
        'cart_total': cart_total  # Total price of all items
    }
    
    # Render the cart template with the context data
    return render(request, 'core/cart.html', context)

@login_required  # Ensure user is logged in to update cart items
def update_cart_item(request, item_id):
    # Get the cart item that belongs to the current user or return 404
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    
    # Handle POST requests for updating cart items
    if request.method == 'POST':
        # Get the action to perform (increase, decrease, remove)
        action = request.POST.get('action')
        
        if action == 'update':
            # Get the new quantity from the form data (default to 1 if not provided)
            new_quantity = int(request.POST.get('quantity', 1))
            # Get the current quantity in the cart
            original_quantity = cart_item.quantity
            # Calculate the difference between new and original quantity
            quantity_difference = new_quantity - original_quantity
            
            # If increasing quantity, check if enough stock is available
            if quantity_difference > 0:
                # Check if the product has enough stock for the increase
                if not cart_item.product.in_stock or cart_item.product.stock_quantity < quantity_difference:
                    # Show error message if not enough stock
                    messages.error(request, 'Not enough stock available for the requested quantity')
                    return redirect('cart_view')
                
                # Update product stock (decrease by the additional quantity)
                product = cart_item.product
                product.stock_quantity -= quantity_difference  # Reduce stock by the additional quantity
                # If stock is depleted, mark as out of stock
                if product.stock_quantity <= 0:
                    product.stock_quantity = 0  # Ensure stock doesn't go negative
                    product.in_stock = False  # Mark as out of stock
                product.save()  # Save changes to the database
            
            # If decreasing quantity, return stock to inventory
            elif quantity_difference < 0:
                # Update product stock (increase by the returned quantity)
                product = cart_item.product
                product.stock_quantity += abs(quantity_difference)  # Add back the returned quantity
                product.in_stock = True  # Mark as in stock since we're adding inventory
                product.save()  # Save changes to the database
            
            # Update cart item quantity with the new value
            cart_item.quantity = new_quantity
            cart_item.save()  # Save changes to the database
            # Show success message to the user
            messages.success(request, f'Updated {cart_item.product.name} quantity to {new_quantity}.')
        
        elif action == 'remove':  # Remove item from cart completely
            # Store product name for success message
            product_name = cart_item.product.name
            
            # Return the product quantity to inventory when removing from cart
            product = cart_item.product
            product.stock_quantity += cart_item.quantity  # Add all quantities back to inventory
            product.in_stock = True  # Mark product as in stock
            product.save()  # Save changes to the database
            
            # Delete the cart item completely
            cart_item.delete()  # Remove from database
            # Show success message to the user
            messages.success(request, f'Removed {product_name} from your cart.')
    
    # Redirect back to the cart view after any action
    return redirect('cart_view')

@login_required  # Ensure user is logged in to add items to cart
def add_to_cart_menu(request, pk):
    # Get the product by ID or return 404 if not found
    product = get_object_or_404(Product, pk=pk)
    quantity = 1  # Default quantity to add
    
    # If this is a POST request, get the quantity from the form submission
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not specified
    
    # Check if the product is in stock and has enough quantity
    if not product.in_stock or product.stock_quantity < quantity:
        # Show error message if product is out of stock or insufficient quantity
        messages.error(request, 'Product is out of stock or not enough quantity available')
        return redirect('product_detail', pk=pk)  # Redirect back to product detail page
    
    # Check if the user has the Customer role (only customers can add to cart)
    if not hasattr(request.user, 'role') or request.user.role != 'Customer':
        # If the user is not a Customer (e.g., they're an Administrator),
        # temporarily treat them as a Customer for cart purposes
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Find a customer user to use for the cart (or create one if needed)
        customer = User.objects.filter(role='Customer').first()
        if not customer:
            # If no customer exists, create one (this should rarely happen)
            customer = User.objects.create(
                username='temp_customer',
                role='Customer'
            )
    else:
        # User is a customer, use their account for the cart
        customer = request.user
        
    # Get or create an active cart for the customer
    cart, created = Cart.objects.get_or_create(
        customer=customer,  # The customer who owns the cart
        is_active=True  # Only get active carts (not checked out)
    )
    
    # Check if the product is already in the cart to update quantity instead of creating new item
    try:
        # Try to find an existing cart item for this product
        cart_item = CartItem.objects.get(cart=cart, product=product)
        # If found, increase the quantity
        cart_item.quantity += quantity
        cart_item.save()  # Save the updated quantity
        # Show success message with the increased quantity
        messages.success(request, f'Added {quantity} more {product.name} to your cart.')
    except CartItem.DoesNotExist:
        # If product not in cart, create a new cart item
        CartItem.objects.create(
            cart=cart,  # The cart to add the item to
            product=product,  # The product being added
            quantity=quantity  # The quantity to add
        )
        # Show success message for new item added
        messages.success(request, f'Added {product.name} to your cart.')
        
    # Update the product's stock quantity to reflect items in cart
    product.stock_quantity -= quantity  # Reduce available stock
    # If stock reaches zero, mark as out of stock
    if product.stock_quantity <= 0:
        product.stock_quantity = 0  # Ensure stock doesn't go negative
        product.in_stock = False  # Mark as out of stock
    product.save()  # Save changes to the database
    
    # Redirect to the cart view to show the updated cart
    return redirect('cart_view')

# AJAX view for adding items to cart without page refresh
def add_to_cart_ajax(request):
    if request.method == 'POST':
        try:
            # Try to get data from POST form data (standard form submission)
            product_id = request.POST.get('product_id')  # Get product ID from form data
            
            # If not in POST, check if it's JSON data (for AJAX requests)
            if not product_id and request.body:
                import json
                try:
                    # Parse JSON data from request body
                    data = json.loads(request.body)
                    product_id = data.get('product_id')  # Get product ID from JSON
                    quantity = int(data.get('quantity', 1))  # Get quantity with default of 1
                except json.JSONDecodeError:
                    # Return error response if JSON is invalid
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid JSON data'
                    })
            else:
                # Get quantity from form data if not from JSON
                quantity = int(request.POST.get('quantity', 1))  # Default to 1 if not specified
            
            # Validate that product ID was provided
            if not product_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Product ID is required'
                })
            
            # Get the product by ID or return 404 if not found
            product = get_object_or_404(Product, id=product_id)
            
            # Check if the product is in stock and has enough quantity
            if not product.in_stock or product.stock_quantity < quantity:
                # Return error response if product is out of stock or insufficient quantity
                return JsonResponse({
                    'success': False,
                    'message': 'Product is out of stock or not enough quantity available'
                })
            
            # Check if the user has the Customer role (only customers can add to cart)
            if not hasattr(request.user, 'role') or request.user.role != 'Customer':
                # If the user is not a Customer (e.g., they're an Administrator),
                # temporarily treat them as a Customer for cart purposes
                from django.contrib.auth import get_user_model
                User = get_user_model()
                # Find a customer user to use for the cart (or create one if needed)
                customer = User.objects.filter(role='Customer').first()
                if not customer:
                    # If no customer exists, create one (this should rarely happen)
                    customer = User.objects.create(
                        username='temp_customer',
                        role='Customer'
                    )
            else:
                # User is a customer, use their account for the cart
                customer = request.user
                
            # Get or create an active cart for the customer
            cart, created = Cart.objects.get_or_create(
                customer=customer,  # The customer who owns the cart
                is_active=True  # Only get active carts (not checked out)
            )
            
            # Check if the product is already in the cart to update quantity instead of creating new item
            try:
                # Try to find an existing cart item for this product
                cart_item = CartItem.objects.get(cart=cart, product=product)
                # If found, increase the quantity
                cart_item.quantity += quantity
                cart_item.save()  # Save the updated quantity
            except CartItem.DoesNotExist:
                # If product not in cart, create a new cart item
                cart_item = CartItem.objects.create(
                    cart=cart,  # The cart to add the item to
                    product=product,  # The product being added
                    quantity=quantity  # The quantity to add
                )
            
            # Update the product's stock quantity to reflect items in cart
            product.stock_quantity -= quantity  # Reduce available stock
            # If stock reaches zero, mark as out of stock
            if product.stock_quantity <= 0:
                product.stock_quantity = 0  # Ensure stock doesn't go negative
                product.in_stock = False  # Mark as out of stock
            product.save()  # Save changes to the database
            
            # Get the updated cart count and total price for the response
            cart_items_count = cart.get_total_items()  # Total number of items in cart
            cart_total_price = cart.get_total_price()  # Total price of all items in cart
            
            # Prepare product image URL for cart dropdown display
            image_url = ''
            if product.image:
                image_url = product.image.url  # Use the product's actual image if available
            else:
                # Use a placeholder image if product has no image
                image_url = '/static/images/placeholder.jpg'
                
            # Return success response with cart information for updating the UI
            return JsonResponse({
                'success': True,  # Operation was successful
                'message': f'{product.name} added to cart',  # Success message
                'cart_count': cart_items_count,  # Updated cart count for badge
                'cart_total': cart_total_price,  # Updated cart total for display
                'new_stock': product.stock_quantity,  # Updated stock quantity
                'product_info': {  # Product information for cart dropdown
                    'id': product.id,  # Product ID
                    'name': product.name,  # Product name
                    'price': float(product.price),  # Product price as float for JS
                    'image': image_url,  # Product image URL
                    'quantity': quantity  # Quantity added to cart
                }
            })
        except Exception as e:
            # Handle any exceptions that might occur during processing
            import traceback
            # Log the error details for debugging
            print(f'Error in add_to_cart_ajax: {str(e)}')
            print(traceback.format_exc())
            # Return error response with the exception message
            return JsonResponse({
                'success': False,  # Operation failed
                'message': str(e)  # Error message
            })
    
    # Return error for non-POST requests
    return JsonResponse({
        'success': False,  # Operation failed
        'message': 'Invalid request method'  # Error message
    })

@login_required  # Ensure user is logged in to checkout
def checkout_view(request):
    # Attempt to get the user's active cart
    try:
        # Get the active cart for the current user
        cart = Cart.objects.get(customer=request.user, is_active=True)
        
        # Check if specific items were selected for checkout from the cart page
        selected_item_ids = request.GET.getlist('selected_items')  # Get list of selected item IDs
        
        if selected_item_ids:
            # If specific items were selected, only include those in checkout
            cart_items = cart.cartitem_set.filter(id__in=selected_item_ids)  # Filter by selected IDs
        else:
            # If no specific items were selected, include all items in cart
            cart_items = cart.cartitem_set.all()  # Get all items in cart
        
        # Check if there are any items to checkout
        if not cart_items.exists():
            # Show warning message if cart is empty
            messages.warning(request, 'Your cart is empty. Please add products before checkout.')
            # Redirect back to cart page
            return redirect('cart_view')
            
        # Calculate total price for selected items only (important for partial checkouts)
        total_price = sum(item.get_total_price() for item in cart_items)  # Sum of all selected items
        total_items = cart_items.count()  # Count of selected items
    except Cart.DoesNotExist:
        # Handle case where user has no active cart
        messages.warning(request, 'Your cart is empty. Please add products before checkout.')
        # Redirect to dashboard to browse products
        return redirect('customer_dashboard')
    
    # Handle form submission for checkout
    if request.method == 'POST':
        # Get shipping and payment information from the form
        payment_method = request.POST.get('payment_method')  # Payment method selected
        address = request.POST.get('address')  # Shipping address
        city = request.POST.get('city')  # City
        postal_code = request.POST.get('postal_code')  # Postal/ZIP code
        phone = request.POST.get('phone')  # Contact phone number
        
        # Create a new order in the database
        order = Order.objects.create(
            customer=request.user,  # Customer who placed the order
            total_amount=total_price,  # Total amount for the order
            status='Pending'  # Initial status of the order
        )
        
        # Store shipping information in the session for reference later
        request.session['shipping_info'] = {
            'address': f'{address}, {city}, {postal_code}',  # Full address
            'phone': phone  # Contact phone
        }
        
        # Create order items from selected cart items (transfer from cart to order)
        for cart_item in cart_items:
            # Create order item records for each cart item
            OrderItem.objects.create(
                order=order,  # Link to the parent order
                product=cart_item.product,  # Product being ordered
                quantity=cart_item.quantity,  # Quantity ordered
                price=cart_item.product.price  # Price at time of order (in case price changes later)
            )
            
            # Remove the checked out items from the cart
            cart_item.delete()  # Delete cart items that have been transferred to order
        
        # Create a payment record for the order
        Payment.objects.create(
            order=order,  # Link to the order
            payment_date=timezone.now(),  # Current date and time
            payment_method=payment_method,  # Method selected by customer
            amount=total_price,  # Total amount paid
            payment_status='Pending'  # Initial payment status
        )
        
        # Mark the cart as inactive since order has been placed
        cart.is_active = False  # Deactivate the cart
        cart.save()  # Save changes to the database
        
        # Show success message to the user
        messages.success(request, f'Your order has been placed successfully! Order #{order.id}')
        
        # Redirect to order history page to show the new order
        return redirect('order_history')
    
    # For GET requests, show the checkout form page
    context = {
        'cart_items': cart_items,  # Items to be checked out
        'total_price': total_price,  # Total price to be paid
        'total_items': total_items  # Number of items in checkout
    }
    
    return render(request, 'core/checkout.html', context)

@login_required  # Ensure user is logged in to view order confirmation
def order_confirmation(request, order_id):
    # Render the order confirmation page with the order ID
    # This is shown after a successful checkout
    return render(request, 'core/order_confirmation.html', {'order_id': order_id})

@login_required  # Ensure user is logged in to view order history
def order_history(request):
    # Get all orders for the current user, ordered by most recent first
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')  # Newest orders first
    
    # Get order items for each order to display in the history
    for order in orders:
        # Add items as an attribute to each order for easy access in the template
        order.items = OrderItem.objects.filter(order=order)  # Items belonging to this order
    
    # Prepare context data for the template
    context = {
        'orders': orders,  # List of user's orders with their items
        'page_title': 'My Orders'  # Page title for the template
    }
    
    # Render the order history template with the context data
    return render(request, 'core/order_history.html', context)

@login_required  # Ensure user is logged in to view order details
def order_detail(request, order_id):
    try:
        # Get the specific order by ID
        order = Order.objects.get(id=order_id)  # The order to display
        # Get all items in this order
        order_items = OrderItem.objects.filter(order=order)  # Products in the order
        
        # Try to get payment information for this order
        try:
            payment = Payment.objects.get(order=order)  # Payment details
        except Payment.DoesNotExist:
            # Handle case where payment record doesn't exist yet
            payment = None
        
        # Prepare context data for the template
        context = {
            'order': order,  # The order object
            'order_items': order_items,  # Items in the order
            'payment': payment  # Payment information
        }
        
        # Use different templates based on user role for appropriate view
        # If the user is an Administrator or Staff, use the staff template with more options
        if request.user.role == 'Administrator' or request.user.is_staff:
            return render(request, 'core/staff_order_detail.html', context)  # Admin/staff view
        else:
            return render(request, 'core/order_detail.html', context)  # Customer view
    except Order.DoesNotExist:
        # Handle case where order doesn't exist or doesn't belong to user
        messages.error(request, 'Order not found')  # Show error message
        return redirect('all_orders')  # Redirect to orders list

@login_required  # Ensure user is logged in to view all orders (admin/staff only)
def all_orders(request):
    # Get all orders in the system, ordered by most recent first
    orders = Order.objects.all().order_by('-order_date')  # Newest orders first
    # Render the all orders template with the orders list
    return render(request, 'core/all_orders.html', {'orders': orders})

@login_required  # Ensure user is logged in to view pending orders (admin/staff only)
def pending_orders(request):
    # Get all pending orders that need to be processed
    orders = Order.objects.filter(status='Pending').order_by('-order_date')  # Newest pending orders first
    # Render the pending orders template with the filtered orders list
    return render(request, 'core/pending_orders.html', {'orders': orders})

@login_required  # Ensure user is logged in to view completed orders (admin/staff only)
def completed_orders(request):
    # Get all completed orders
    orders = Order.objects.filter(status='Completed').order_by('-order_date')  # Newest completed orders first
    # Render the completed orders template with the filtered orders list
    return render(request, 'core/completed_orders.html', {'orders': orders})

@login_required
def complete_order(request, order_id):
    # Only staff/admin can complete orders
    if not request.user.is_staff and not request.user.role == 'Administrator':
        messages.error(request, 'You do not have permission to complete orders')
        return redirect('pending_orders')
    
    try:
        # Get the order by ID
        order = Order.objects.get(id=order_id)
        
        # Only pending orders can be completed
        if order.status != 'Pending':
            messages.error(request, 'Only pending orders can be completed')
            return redirect('pending_orders')
        
        # Update the order status to Completed
        order.status = 'Completed'
        order.save()
        
        # Try to record this activity for the activity feed
        try:
            from .models import Activity
            Activity.objects.create(
                type='order',
                title=f'Order #{order.id} from {order.customer.username} marked as completed by {request.user.username}'
            )
        except:
            # If Activity table doesn't exist yet, just continue without recording
            pass
        
        # Show success message
        messages.success(request, f'Order #{order_id} has been marked as completed')
        
    except Order.DoesNotExist:
        # Handle case where order doesn't exist
        messages.error(request, 'Order not found')
    
    # Redirect back to pending orders page
    return redirect('pending_orders')

@login_required
def cancel_order(request, order_id):
    # Only staff/admin can cancel orders
    if not request.user.is_staff and not request.user.role == 'Administrator':
        messages.error(request, 'You do not have permission to cancel orders')
        return redirect('pending_orders')
    
    try:
        # Get the order by ID
        order = Order.objects.get(id=order_id)
        
        # Only pending orders can be canceled
        if order.status != 'Pending':
            messages.error(request, 'Only pending orders can be canceled')
            return redirect('pending_orders')
        
        # Update the order status to Canceled
        order.status = 'Canceled'
        order.save()
        
        # Try to record this activity for the activity feed
        try:
            from .models import Activity
            Activity.objects.create(
                type='order',
                title=f'Order #{order.id} from {order.customer.username} canceled by {request.user.username}'
            )
        except:
            # If Activity table doesn't exist yet, just continue without recording
            pass
        
        # Show success message
        messages.success(request, f'Order #{order_id} has been canceled')
        
    except Order.DoesNotExist:
        # Handle case where order doesn't exist
        messages.error(request, 'Order not found')
    
    # Redirect back to pending orders page
    return redirect('pending_orders')