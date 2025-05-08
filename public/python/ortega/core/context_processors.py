from .models import Cart

def cart_processor(request):
    """
    Context processor that adds cart information to all templates
    """
    cart_items_count = 0
    cart_items = []
    cart_total_price = 0
    
    # Only process for authenticated users who are customers
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'Customer':
        try:
            # Get the user's active cart
            cart = Cart.objects.filter(customer=request.user, is_active=True).first()
            
            if cart:
                # Get the cart items count
                cart_items_count = cart.get_total_items()
                
                # Get the cart items
                cart_items = cart.cartitem_set.all()
                
                # Get the cart total price
                cart_total_price = cart.get_total_price()
        except Exception as e:
            # If there's any error, just return empty values
            print(f'Error in cart_processor: {str(e)}')
            pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_items': cart_items,
        'cart_total_price': cart_total_price
    }
