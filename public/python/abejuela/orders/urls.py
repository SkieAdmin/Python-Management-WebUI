from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.menu, name='menu'),
    path('create/', views.create_order, name='create_order'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('detail/<int:pk>/', views.order_detail, name='order_detail'),
    path('list/', views.order_list, name='order_list'),
    path('my-orders/', views.customer_orders, name='customer_orders'),
    path('update-status/<int:pk>/', views.update_order_status, name='update_order_status'),
    path('update-payment-status/<int:pk>/', views.update_payment_status, name='update_payment_status'),
    path('make-payment/<int:pk>/', views.make_payment, name='make_payment'),
]
