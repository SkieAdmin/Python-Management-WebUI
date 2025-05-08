from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, OrderForm, PaymentForm, ReservationForm, ProfileForm, MenuItemForm
from .models import MenuItem, Order, Reservation
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import ReservationUpdateForm
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import ReservationPaymentForm
from django.utils import timezone
from django.http import Http404
from django.db.models import Count
from datetime import timedelta
from django.core.mail import send_mail
import traceback

# ==============================
# AUTHENTICATION VIEWS
# ==============================

@csrf_protect
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'There was an error in the registration form. Please try again.')
    else:
        form = RegisterForm()
    return render(request, 'ordering/register.html', {'form': form})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('custom_admin_dashboard' if user.is_staff else 'menu')
        messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'ordering/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('login')
    
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt: {username}")  # Debug print
        user = authenticate(request, username=username, password=password)
        if user:
            print(f"Authentication successful, is_staff: {user.is_staff}")  # Debug print
            login(request, user)
            redirect_url = 'custom_admin_dashboard' if user.is_staff else 'menu'
            print(f"Redirecting to: {redirect_url}")  # Debug print
            return redirect(redirect_url)
        else:
            print("Authentication failed")  # Debug print
        messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'ordering/login.html')
# ==============================
# ADMIN AUTHENTICATION
# ==============================

@csrf_protect
def custom_admin_register(request):
    """
    A simplified admin registration function that mirrors Django's createsuperuser command
    and bypasses standard password validation to ensure it works consistently.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            return render(request, 'ordering/custom_admin_register.html', {
                'error': 'Both username and password are required.'
            })
        
        try:
            # Check if user exists
            if User.objects.filter(username=username).exists():
                return render(request, 'ordering/custom_admin_register.html', {
                    'error': f"User '{username}' already exists."
                })
            
            # Create a regular user first (this will hash the password)
            user = User.objects.create_user(username=username, password=password)
            
            # Then upgrade permissions to superuser/staff
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            # Success message - but don't login yet, redirect to login page
            messages.success(request, f"Admin user '{username}' created successfully! Please log in.")
            return redirect('custom_admin_login')
            
        except Exception as e:
            error_message = str(e)
            print("ADMIN REGISTRATION ERROR:", error_message)
            print(traceback.format_exc())
            
            return render(request, 'ordering/custom_admin_register.html', {
                'error': f"Registration error: {error_message}"
            })
    
    # For GET requests
    return render(request, 'ordering/custom_admin_register.html')

@csrf_protect
def custom_admin_login(request):
    """
    Simplified admin login function with clear error messages
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            return render(request, 'ordering/custom_admin_login.html', {
                'error': 'Both username and password are required.'
            })
        
        # Check if user exists first
        try:
            user_exists = User.objects.filter(username=username).exists()
            if not user_exists:
                return render(request, 'ordering/custom_admin_login.html', {
                    'error': f"User '{username}' does not exist. Please register first."
                })
                
            # User exists, try to authenticate
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Make sure they have admin privileges
                if not user.is_staff:
                    user.is_staff = True
                    user.save()
                    messages.info(request, 'Account upgraded to admin status.')
                
                # Log the user in
                login(request, user)
                messages.success(request, f'Welcome, {username}!')
                return redirect('custom_admin_dashboard')
            else:
                # Authentication failed but user exists = wrong password
                return render(request, 'ordering/custom_admin_login.html', {
                    'error': 'Invalid password. Please try again.'
                })
                
        except Exception as e:
            error_message = str(e)
            print("LOGIN ERROR:", error_message)
            
            return render(request, 'ordering/custom_admin_login.html', {
                'error': f"Login error: {error_message}"
            })
    
    # For GET requests
    return render(request, 'ordering/custom_admin_login.html')

# ==============================
# USER PROFILE
# ==============================

@login_required
def profile_view(request):
    return render(request, 'ordering/profile.html', {'user': request.user})

@login_required
def view_profile(request):
    return render(request, 'ordering/profile.html')

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'ordering/edit_profile.html', {'form': form})

# ==============================
# MENU VIEWS
# ==============================

@login_required
def menu_view(request):
    items = MenuItem.objects.all()
    return render(request, 'ordering/menu.html', {'items': items})

# ==============================
# ORDER VIEWS
# ==============================

@login_required
def order_view(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    
    # Check if the item is available before allowing order
    if not item.available:
        messages.error(request, f"Sorry, {item.name} is currently unavailable.")
        return redirect('menu')
        
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        total = item.price * quantity
        Order.objects.create(
            customer=request.user,
            item=item,
            quantity=quantity,
            total_price=total,
            status='Pending',
            payment_status='Unpaid'
        )
        messages.success(request, 'Order placed successfully!')
        return redirect('order_history')
    return render(request, 'ordering/order.html', {'item': item})

@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'ordering/order_history.html', {'orders': orders})

@login_required
def pay_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, instance=order)
        
        if form.is_valid():
            updated_order = form.save(commit=False)
            updated_order.payment_status = 'Pending'  # Set to Pending after uploading proof
            updated_order.save()
            
            messages.success(request, 'Payment proof uploaded successfully! Please wait for admin confirmation.')
            return redirect('order_history')
        else:
            messages.error(request, 'Payment form submission failed. Please try again.')
    else:
        form = PaymentForm(instance=order)

    return render(request, 'ordering/pay.html', {'form': form, 'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.payment_status == 'Unpaid':
        order.delete()
        messages.success(request, 'Order cancelled successfully.')
    else:
        messages.error(request, 'Paid orders cannot be cancelled.')
    return redirect('order_history')

# ==============================
# RESERVATION VIEWS
# ==============================

@login_required
def reservation_package(request):
    reservations = Reservation.objects.filter(customer=request.user)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.customer = request.user
            reservation.package_deal = request.POST.get('package_deal', 'none')
            reservation.delivery_option = request.POST.get('delivery_option', 'pickup')

            price_mapping = {
                20: 7500, 30: 10000, 40: 12500,
                50: 15000, 60: 17500, 70: 20000
            }

            reservation.price = price_mapping.get(reservation.kilos, 0)
            if reservation.delivery_option == 'door':
                reservation.price += 500

            reservation.save()
            messages.success(request, 'Reservation made successfully!')
            return redirect('reservation_package')
        else:
            messages.error(request, 'There was an error in the reservation form.')
    else:
        form = ReservationForm()

    return render(request, 'ordering/reservation_package.html', {
        'form': form,
        'reservations': reservations
    })

@login_required
def pay_reservation(request, reservation_id):
    # Make sure this reservation belongs to the current user
    reservation = get_object_or_404(Reservation, id=reservation_id, customer=request.user)

    if request.method == 'POST':
        form = ReservationPaymentForm(request.POST, request.FILES, instance=reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.save()
            messages.success(request, 'Payment proof submitted. Please wait for admin confirmation.')
            return redirect('reservation_package')
        else:
            messages.error(request, 'Payment form submission failed. Please try again.')
    else:
        form = ReservationPaymentForm(instance=reservation)

    return render(request, 'ordering/pay.html', {
        'form': form,
        'reservation': reservation
    })

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.delete()
    messages.success(request, 'Reservation cancelled successfully.')
    return redirect('reservation_package')

# ==============================
# ADMIN DASHBOARD & MANAGEMENT
# ==============================

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('menu')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def custom_admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('menu')
        
    try:
        today = timezone.now()
        one_week_ago = today - timedelta(days=7)
        one_month_ago = today - timedelta(days=30)
        
        # Current counts with error handling
        try:
            total_orders = Order.objects.count()
            # Count pending orders for notifications
            pending_orders_count = Order.objects.filter(status='Pending').count()
            # Get recent orders for notification display (last 5)
            recent_orders = Order.objects.filter(status='Pending').order_by('-date_time')[:5]
        except Exception as e:
            print(f"Error counting orders: {e}")
            total_orders = 0
            pending_orders_count = 0
            recent_orders = []
        
        # Debug: Print all reservations with their actual status values
        try:
            all_reservations = Reservation.objects.all()
            print(f"Total reservations in database: {all_reservations.count()}")
            
            # Get all unique status values
            actual_statuses = set(all_reservations.values_list('status', flat=True))
            print(f"Actual status values in database: {actual_statuses}")
            
            # Count reservations by each status value that actually exists
            status_counts = {}
            for status in actual_statuses:
                count = Reservation.objects.filter(status=status).count()
                status_counts[status] = count
                print(f"Status '{status}': {count} reservations")
            
            # For now, count all reservations as active
            active_reservations = all_reservations.count()
            
            # Count pending reservations for notifications
            pending_reservations_count = Reservation.objects.filter(status='Pending').count()
            # Get recent reservations for notification display (last 5)
            recent_reservations = Reservation.objects.filter(status='Pending').order_by('-reserved_at')[:5]
            
        except Exception as e:
            print(f"Error processing reservations: {e}")
            active_reservations = 0
            status_counts = {}
            actual_statuses = set()
            pending_reservations_count = 0
            recent_reservations = []
        
        # Count regular users (non-staff, non-superuser)
        try:
            regular_user_count = User.objects.filter(is_staff=False, is_superuser=False).count()
            # Count admin users separately if needed
            admin_count = User.objects.filter(is_staff=True).count()
            # Total user count (for reference)
            total_user_count = User.objects.count()
        except Exception as e:
            print(f"Error counting users: {e}")
            regular_user_count = 0
            admin_count = 0
            total_user_count = 0
        
        try:
            menu_items_count = MenuItem.objects.count()
        except Exception as e:
            print(f"Error counting menu items: {e}")
            menu_items_count = 0
            
        # Count pending payments (orders and reservations with payment proof uploaded but not marked as paid)
        try:
            # Orders with payment proof but not paid
            order_payments = Order.objects.filter(
                gcash_screenshot__isnull=False, 
                payment_status='Unpaid'
            ).count()
            
            # Reservations with payment proof but not paid
            reservation_payments = Reservation.objects.filter(
                gcash_screenshot__isnull=False, 
                payment_status='Unpaid'
            ).count()
            
            pending_payments_count = order_payments + reservation_payments
            
            # Get recent payment proofs (from both orders and reservations)
            recent_order_payments = Order.objects.filter(
                gcash_screenshot__isnull=False, 
                payment_status='Unpaid'
            ).order_by('-date_time')[:3]
            
            recent_reservation_payments = Reservation.objects.filter(
                gcash_screenshot__isnull=False, 
                payment_status='Unpaid'
            ).order_by('-date_time')[:3]
            
            # Combine the two querysets for the template
            recent_payments = list(recent_order_payments) + list(recent_reservation_payments)
            # Sort by date_time in descending order
            recent_payments.sort(key=lambda x: x.date_time, reverse=True)
            # Take the 5 most recent
            recent_payments = recent_payments[:5]
            
        except Exception as e:
            print(f"Error counting payment proofs: {e}")
            pending_payments_count = 0
            recent_payments = []
        
        # Calculate percentage changes (simplified example)
        orders_percentage = 12
        reservations_percentage = 5
        users_percentage = 8
        new_menu_items = 3
        
        # Total notifications count (for grand total if needed)
        total_notifications = pending_orders_count + pending_reservations_count + pending_payments_count
        
        context = {
            # Basic dashboard data
            'total_orders': total_orders,
            'active_reservations': active_reservations,
            'user_count': regular_user_count,
            'admin_count': admin_count,
            'total_user_count': total_user_count,
            'menu_items_count': menu_items_count,
            'orders_percentage': orders_percentage,
            'reservations_percentage': reservations_percentage,
            'users_percentage': users_percentage,
            'new_menu_items': new_menu_items,
            
            # Notification counts
            'pending_orders_count': pending_orders_count,
            'pending_reservations_count': pending_reservations_count,
            'pending_payments_count': pending_payments_count,
            'total_notifications': total_notifications,
            
            # Recent items for notifications section
            'recent_orders': recent_orders,
            'recent_reservations': recent_reservations,
            'recent_payments': recent_payments,
            
            # Debug info
            'debug_info': {
                'total_reservations': all_reservations.count() if 'all_reservations' in locals() else 0,
                'actual_statuses': list(actual_statuses) if 'actual_statuses' in locals() else [],
                'status_counts': status_counts if 'status_counts' in locals() else {},
            }
        }
        
        return render(request, 'ordering/custom_admin_dashboard.html', context)
    except Exception as e:
        # Global error handling
        print(f"Error in dashboard view: {e}")
        context = {
            'error_message': str(e),
            # Default empty values for notification counts
            'pending_orders_count': 0,
            'pending_reservations_count': 0,
            'pending_payments_count': 0,
            'total_notifications': 0,
            'recent_orders': [],
            'recent_reservations': [],
            'recent_payments': [],
        }
        return render(request, 'ordering/custom_admin_dashboard.html', context)
# ==============================
# MENU MANAGEMENT (ADMIN ONLY)
# ==============================

@login_required
@admin_required
def menu_list(request):
    items = MenuItem.objects.all()
    return render(request, 'ordering/menu_list.html', {'items': items})

@login_required
@admin_required
def menu_add(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('menu_list')
        else:
            messages.error(request, 'Failed to add menu item. Please check the form.')
    else:
        form = MenuItemForm()
    return render(request, 'ordering/menu_form.html', {'form': form, 'title': 'Add Menu Item'})

@login_required
@admin_required
def menu_edit(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('menu_list')  # Redirect to menu list after successful edit
        else:
            messages.error(request, 'Failed to update menu item. Please check the form.')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'ordering/menu_form.html', {'form': form, 'title': 'Edit Menu Item'})

@login_required
@admin_required
def menu_delete(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('menu_list')
    return render(request, 'ordering/menu_confirm_delete.html', {'item': item})

@login_required
@admin_required
def toggle_menu_availability(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.available = not item.available
    item.save()
    
    # Redirect to the menu list page
    return redirect('menu_list')  # Use the correct URL name from your urls.py

# ==============================
# ORDER MANAGEMENT (ADMIN ONLY)
# ==============================

@staff_member_required
def manage_orders(request):
    orders = Order.objects.all().order_by('-id')  # Show latest orders first
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        payment_status = request.POST.get('payment_status')
        
        order = get_object_or_404(Order, id=order_id)

        if status:
            order.status = status
        if payment_status:
            order.payment_status = payment_status  # Admin can set to Paid
        order.save()

        messages.success(request, 'Order updated successfully.')
        return redirect('manage_orders')

    return render(request, 'ordering/manage_orders.html', {'orders': orders})

@login_required
def order_list(request):
    # Ensure the user is an admin
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")

    # Get the date from the query parameters (e.g., ?date=2023-10-01)
    date_str = request.GET.get('date')
    
    # Initialize selected_date
    selected_date = None

    if date_str:
        try:
            # Parse the date string to a date object
            selected_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = None  # If parsing fails, keep it as None

    # Fetch orders for the selected date if provided
    if selected_date:
        orders = Order.objects.filter(date_time__date=selected_date).order_by('-id')  # Adjusted to use 'date_time'
    else:
        orders = Order.objects.all().order_by('-id')  # If no date is specified, show all orders

    return render(request, 'ordering/order_list.html', {'orders': orders, 'selected_date': selected_date})

@login_required
def delete_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.delete()
    return redirect('manage_orders')  # Replace with your actual order management view name

# ==============================
# RESERVATION MANAGEMENT (ADMIN ONLY)
# ==============================

def manage_single_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'custom_admin/manage_reservation.html', {'reservation': reservation})

@login_required
def manage_reservation(request):
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')

        if not reservation_id:
            messages.error(request, "Reservation ID is missing.")
            return redirect('reservation_package_manage')

        reservation = get_object_or_404(Reservation, id=reservation_id)

        delivery_option = request.POST.get('delivery_option', '').strip()
        status = request.POST.get('status', '').strip()
        payment_status = request.POST.get('payment_status', '').strip()
        price = request.POST.get('price', '').strip()

        if not all([delivery_option, status, payment_status, price]):
            messages.warning(request, "Please fill in all fields before submitting.")
            return redirect('reservation_package_manage')

        try:
            price = float(price)
        except ValueError:
            messages.error(request, "Invalid price value. Please enter a valid number.")
            return redirect('reservation_package_manage')

        try:
            reservation.delivery_option = delivery_option
            reservation.status = status
            reservation.payment_status = payment_status
            reservation.price = price

            # Automatically update remarks if payment is marked as 'paid'
            if payment_status.lower() == 'paid':
                reservation.remarks = 'Paid'

            reservation.save()

            messages.success(request, f"Reservation #{reservation.id} updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to update reservation #{reservation.id}. Error: {e}")

        return redirect('reservation_package_manage')

    reservations = Reservation.objects.all().order_by('-reserved_at')
    return render(request, 'ordering/reservation_package_manage.html', {'reservations': reservations})

def delete_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    reservation.delete()
    messages.success(request, "Reservation deleted successfully.")
    return redirect('reservation_package_manage')  # Redirect back to reservations page after deletion

@login_required
def reservation_list(request):
    """
    View to display a list of reservations, optionally filtered by a specific date.
    Only accessible to staff users.
    """
    # Ensure the user is an admin
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")
    
    # Get the date from query parameters (e.g., ?date=2023-10-01)
    date_str = request.GET.get('date')
    selected_date = None
    
    if date_str:
        try:
            # Parse the date string into a date object
            selected_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            # Filter reservations by the selected date
            reservations = Reservation.objects.filter(delivery_date=selected_date).order_by('-id')
        except ValueError:
            # Handle invalid date format gracefully
            selected_date = None
            reservations = Reservation.objects.all().order_by('-id')
    else:
        # Show all reservations if no date is specified
        reservations = Reservation.objects.all().order_by('-id')
    
    return render(request, 'ordering/reservation_list.html', {
        'reservations': reservations,
        'selected_date': selected_date,
    })

# ==============================
# USER MANAGEMENT (ADMIN ONLY)
# ==============================

@login_required
@admin_required
def user_list(request):
    """View for listing all users (admin only)"""
    # Get search query from request
    search_query = request.GET.get('search', '')
    
    # Base queryset that excludes admin users (staff and superusers)
    base_queryset = User.objects.filter(is_staff=False, is_superuser=False).select_related('profile')
    
    # Count regular users and admin users separately
    regular_user_count = base_queryset.count()
    admin_count = User.objects.filter(is_staff=True).count()
    
    # Filter users based on search query
    if search_query:
        users = base_queryset.filter(
            username__icontains=search_query
        ) | base_queryset.filter(
            profile__full_name__icontains=search_query
        ) | base_queryset.filter(
            profile__email_address__icontains=search_query
        )
    else:
        users = base_queryset
    
    # Order users
    users = users.order_by('id')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    
    # Pass both counts to the template
    context = {
        'users': users,
        'user_count': regular_user_count,
        'admin_count': admin_count
    }
    
    return render(request, 'ordering/user_list.html', context)


@login_required
@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Try to get or create the user's profile
    try:
        profile = user.profile
    except:
        from .models import Profile
        profile = Profile(user=user)
        profile.save()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        landmark = request.POST.get('landmark')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        
        # Validation
        if not username or not email:
            messages.error(request, 'Username and email are required.')
            return render(request, 'ordering/user_edit.html', {'user': user, 'profile': profile})
        
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'ordering/user_edit.html', {'user': user, 'profile': profile})
        
        try:
            # Update user
            user.username = username
            user.email = email
            user.is_staff = is_staff
            
            if password and password.strip():
                user.set_password(password)
                
            user.save()
            
            # Update profile
            profile.full_name = full_name
            profile.phone_number = phone_number
            profile.address = address
            profile.landmark = landmark
            profile.email_address = email  # Keep email synced
            profile.save()
            
            # Instead of showing a success message, just redirect to the user list
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    context = {
        'user': user,
        'profile': profile
    }
    
    return render(request, 'ordering/user_edit.html', context)

@login_required
@admin_required
def delete_user(request, user_id):
    """View for deleting a user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_list')
    
    if request.method == 'POST':
        # Delete the user
        try:
            user.delete()
            messages.success(request, 'User deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
        return redirect('user_list')
    
    # Make sure this line specifies the correct template path
    return render(request, 'ordering/user_delete.html', {'user': user})

# ==============================
# MISCELLANEOUS VIEWS
# ==============================

def all_remarks_gallery(request):
    """
    View function to display all GCash screenshots from both reservations and orders
    in a combined gallery format.
    """
    # Fetch all reservations that have GCash screenshots
    reservations = Reservation.objects.filter(gcash_screenshot__isnull=False).order_by('-date_time')
    
    # Fetch all orders that have GCash screenshots
    orders = Order.objects.filter(gcash_screenshot__isnull=False).order_by('-date_time')
    
    context = {
        'reservations': reservations,
        'orders': orders,
        'page_title': 'All Remarks Gallery'
    }
    
    return render(request, 'ordering/all_remarks_gallery.html', context)

@login_required
def my_payment_proofs(request):
    user = request.user
    user_orders = Order.objects.filter(customer=user)
    user_reservations = Reservation.objects.filter(customer=user)
    return render(request, 'ordering/my_payment_proofs.html', {
        'user_orders': user_orders,
        'user_reservations': user_reservations,
    })

def landing_page(request):
    return render(request, 'ordering/landing_page.html')

def about_us(request):
    return render(request, 'ordering/about_us.html')

def contact_us(request):
    return render(request, 'ordering/contact_us.html')
   

        # Redirect after successful submission