from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('view/<int:pk>/', views.view_report, name='view_report'),
    path('generate/sales/', views.generate_sales_report, name='generate_sales_report'),
    path('generate/inventory/', views.generate_inventory_report, name='generate_inventory_report'),
    path('generate/payment/', views.generate_payment_report, name='generate_payment_report'),
]
