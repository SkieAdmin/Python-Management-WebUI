from django.urls import path
from . import views

urlpatterns = [
    # Home & Products
    path('',                         views.home,           name='home'),
    path('products/',                views.products,       name='products'),
    path('order/<int:product_id>/',  views.order_product,  name='order_product'),
    path('submit_order/',            views.submit_order,   name='submit_order'),

    # Authentication
    path('login/',                   views.login_view,     name='login'),
    path('signup/',                  views.signup_view,    name='signup'),
    path('logout/',                  views.logout_view,    name='logout'),

    # Orders (Unified page)
    path('orders/',                  views.orders,         name='orders'),

    # Payment
    path('submit-payment/',          views.submit_payment, name='submit_payment'),
]
