from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.landing, name='landing'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('orders/new/', views.create_order, name='create_order'),
    path('sales/', views.sales_report, name='sales_report'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('receipt/<int:order_id>/', views.view_receipt, name='view_receipt'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    #path('receipt/<int:receipt_id>/', views.view_receipt, name='view_receipt'),
    
    path('receipt/<int:receipt_id>/', views.view_receipt, name='view_receipt'),
    path('receipt/<int:order_id>/', views.view_receipt, name='view_receipt'),
    path('receipt/<int:receipt_id>/', views.view_receipt, name='view_receipt'),
    path('sales-report/', views.sales_report, name='sales_report'),

    path('dashboard/manager/', views.dashboard_manager, name='dashboard_manager'),
    path('dashboard/cashier/', views.dashboard_cashier, name='dashboard_cashier'),


    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/inventory/<int:product_id>/', views.update_inventory, name='update_inventory'),

    
]
