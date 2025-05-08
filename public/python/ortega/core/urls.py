from django.urls import path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [

    path('profile/', views.profile_view, name='profile'),
    
    # Landing Page
    path('', views.landing_page, name='home'),

    # Informational Pages
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),

    # Unified Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('admin/register/', views.admin_register_view, name='admin_register'),
    path('logout/', views.logout_view, name='logout'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Dashboards
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/products/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('staff/customers/', views.customer_management, name='customer_management'),
    path('staff/settings/', views.settings_dashboard, name='settings_dashboard'),

    # Product Detail Page
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Sidebar Menu Product Pages
    path('products/cement/', views.cement_page, name='cement'),
    path('products/nails/', views.nails_page, name='nails'),
    path('products/lumber/', views.lumber_page, name='lumber'),
    path('products/tools/', views.tools_page, name='tools'),

    # Product edit/delete
    path('product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    
    # Cart and Checkout
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/add/<int:pk>/', views.add_to_cart_menu, name='add_to_cart_menu'),
    path('cart/add_ajax/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/all/', views.all_orders, name='all_orders'),
    path('orders/pending/', views.pending_orders, name='pending_orders'),
    path('orders/completed/', views.completed_orders, name='completed_orders'),
    path('order/complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # Redirects for built-in Django paths
    path('accounts/login/',    RedirectView.as_view(url='/login/',   permanent=False)),
    path('accounts/profile/',  RedirectView.as_view(url='/profile/', permanent=False)),
]

# In dev only: serve uploaded media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
