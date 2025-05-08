from django.urls import path
from . import views
from .views import order_list  # Import the view


urlpatterns = [
    # Add the landing page route at the top (root URL)
    path('', views.landing_page, name='landing_page'),
    
    # ------------------ User Authentication ------------------
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ------------------ Profile ------------------
    path('profile/', views.profile_view, name='profile'),  # Profile page
    path('profile/view/', views.view_profile, name='view_profile'),  # View profile page
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # ------------------ Menu and Order ------------------
    path('menu/', views.menu_view, name='menu'),
    path('order/<int:item_id>/', views.order_view, name='order'),
    path('history/', views.order_history, name='order_history'),
    path('pay/<int:order_id>/', views.pay_order, name='pay'),
    
    # ------------------ Reservation ------------------
    path('reservation/package/', views.reservation_package, name='reservation_package'),
    path('pay/reservation/<int:reservation_id>/', views.pay_reservation, name='pay_reservation'),
    path('reservation/cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    
    # ------------------ Cancel Orders ------------------
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    
    # ------------------ Custom Admin Auth ------------------
    path('custom-admin/register/', views.custom_admin_register, name='custom_admin_register'),
    path('custom-admin/login/', views.custom_admin_login, name='custom_admin_login'),
    path('custom-admin/dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    
    # ------------------ Admin Menu Management (CRUD) ------------------
    path('custom-admin/menu/', views.menu_list, name='menu_list'),
    path('custom-admin/menu/add/', views.menu_add, name='add_menu_item'),
    path('custom-admin/menu/edit/<int:item_id>/', views.menu_edit, name='edit_menu_item'),
    path('custom-admin/menu/delete/<int:item_id>/', views.menu_delete, name='delete_menu_item'),
    
    # ------------------ Admin Order & Reservation Management ------------------
    path('custom-admin/manage-orders/', views.manage_orders, name='manage_orders'),
    path('admin/reservation/<int:reservation_id>/', views.manage_single_reservation, name='manage_reservation'),
    path('custom-admin/reservation/manage/', views.manage_reservation, name='reservation_package_manage'),
    path('delete/reservation/<int:pk>/', views.delete_reservation, name='delete_reservation'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    
    # ------------------ Admin User Management ------------------
    path('custom-admin/users/', views.user_list, name='user_list'),
    path('custom-admin/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('custom-admin/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # Optional: Enable Django Admin site
    # path('admin/', admin.site.urls),
    
    path('orders/', order_list, name='order_list'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('all-remarks-gallery/', views.all_remarks_gallery, name='all_remarks_gallery'),
    path('my-payment-proofs/', views.my_payment_proofs, name='my_payment_proofs'),
     path('about/', views.about_us, name='about_us'),
      path('contact/', views.contact_us, name='contact_us'),
path('toggle-menu-availability/<int:item_id>/', views.toggle_menu_availability, name='toggle_menu_availability'),
    ]