from django.urls import path
from . import views

urlpatterns = [
    # Landing & public auth
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.landing_page, name='landing_page'),

    # Public Products & Orders
    path('products/',         views.products_view,  name='products'),
    path('products/create/',  views.create_order,   name='create_order'),
    path('products/add/',     views.add_product,    name='add_product'),
    path('orders/',           views.orders_view,    name='orders'),
    path('orders/payment/',   views.make_payment,   name='make_payment'),
    path('orders/list/',      views.orders_list,    name='orders_list'),
    path('orders/confirm/<int:order_id>/', views.confirm_order, name='confirm_order'),

    # Admin auth
    path('admin-panel/login/',  views.admin_login,      name='admin_login'),
    path('admin-panel/logout/', views.admin_logout,     name='admin_logout'),

    # Admin panel
    path('admin-panel/',                      views.admin_dashboard,       name='admin_dashboard'),
    path('admin-panel/products/',             views.admin_products,        name='admin_products'),
    path('admin-panel/products/new/',         views.admin_product_create,  name='admin_product_create'),
    path('admin-panel/products/<int:pk>/edit/',   views.admin_product_edit,   name='admin_product_edit'),
    path('admin-panel/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/orders/',                   views.admin_orders,          name='admin_orders'),
    path('admin-panel/orders/<int:pk>/',          views.admin_order_detail,    name='admin_order_detail'),
    path('admin-panel/orders/<int:pk>/delete/',   views.admin_order_delete,    name='admin_order_delete'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/orders/<int:order_id>/invoice/', views.order_invoice_view, name='admin_order_invoice'),
   

]
