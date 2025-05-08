from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.products, name='products'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('inventory/', views.inventory, name='inventory'),
    path('product/<int:product_id>/', views.get_product, name='get_product'),
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/update-stock/', views.update_product_stock, name='update_product_stock'),
    path('stock-requests/', views.stock_requests, name='stock_requests'),
    path('stock-delivery-progress/', views.stock_delivery_progress, name='stock_delivery_progress'),
    path('stock-request/<int:request_id>/', views.get_stock_request, name='get_stock_request'),
    path('stock-request/<int:request_id>/cancel/', views.cancel_stock_request, name='cancel_stock_request'),
    path('transactions/', views.transactions, name='transactions'),
    path('transaction/<int:transaction_id>/details/', views.get_transaction_details, name='get_transaction_details'),
    path('payments/', views.payments, name='payments'),
    path('supply-status/', views.supply_status, name='supply_status'),
    path('audit/', views.audit, name='audit'),
    path('users/', views.user_management, name='user_management'),
    path('users/toggle/<int:user_id>/', views.toggle_user, name='toggle_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/create-staff/', views.create_staff, name='create_staff'),
    path('users/update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('store-settings/', views.store_settings, name='store_settings'),
    
    # Cart and checkout URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/<int:transaction_id>/', views.checkout_page, name='checkout_page'),
    path('checkout/<int:transaction_id>/complete/', views.complete_checkout, name='complete_checkout'),
    
    # Order tracking URLs
    path('orders/', views.order_tracking, name='order_tracking'),
    path('order/<int:order_id>/details/', views.get_order_details, name='get_order_details'),
    path('order/<int:order_id>/received/', views.mark_order_received, name='mark_order_received'),
    
    # Supplier URLs
    path('supplier/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),
    path('supplier/admin-stock-requests/', views.admin_stock_requests, name='admin_stock_requests'),
    path('supplier/delivery-progression/', views.delivery_progression, name='delivery_progression'),
    path('supplier/request/<str:action>/<int:request_id>/', views.handle_stock_request, name='handle_stock_request'),
]
