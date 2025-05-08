# shop/adminpanel/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'shop_admin'

urlpatterns = [
    path('login/',  auth_views.LoginView.as_view(
                      template_name='shop/adminpanel/login.html'),
                     name='login'),
    path('logout/', views.logout_view,            name='logout'),
    path('',        views.dashboard,              name='dashboard'),

    # Products
    path('products/',               views.product_list,      name='product_list'),
    path('products/add-modal/',     views.product_form,      name='product_add_modal'),
    path('products/<int:pk>/edit-modal/', views.product_form,      name='product_edit_modal'),
    path('products/<int:pk>/delete/',     views.product_delete,   name='product_delete'),

    # Orders
    path('orders/',               views.order_list,        name='order_list'),
    path('orders/add-modal/',     views.order_form,        name='order_add_modal'),
    path('orders/<int:pk>/edit-modal/', views.order_form,      name='order_edit_modal'),
    path('orders/<int:pk>/delete/',     views.order_delete,     name='order_delete'),

    # Payments
    path('payments/',               views.payment_list,    name='payment_list'),
    path('payments/add-modal/',     views.payment_form,    name='payment_add_modal'),
    path('payments/<int:pk>/edit-modal/', views.payment_form,    name='payment_edit_modal'),
    path('payments/<int:pk>/delete/',     views.payment_delete, name='payment_delete'),
]
