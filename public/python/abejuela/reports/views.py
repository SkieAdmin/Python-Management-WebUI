from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Report
from orders.models import Order, OrderItem
from inventory.models import Inventory
import datetime

@login_required
def report_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    reports = Report.objects.all().order_by('-generated_at')
    return render(request, 'reports/report_list.html', {'reports': reports})

@login_required
def generate_sales_report(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not all([start_date, end_date, title]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('generate_sales_report')
        
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        

        report = Report.objects.create(
            report_type='sales',
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            generated_by=request.user
        )
        
        messages.success(request, 'Sales report generated successfully!')
        return redirect('view_report', pk=report.id)
    
    return render(request, 'reports/generate_sales_report.html')

@login_required
def generate_inventory_report(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not title:
            messages.error(request, 'Please provide a title for the report.')
            return redirect('generate_inventory_report')
        

        today = timezone.now().date()
        report = Report.objects.create(
            report_type='inventory',
            title=title,
            description=description,
            start_date=today,
            end_date=today,
            generated_by=request.user
        )
        
        messages.success(request, 'Inventory report generated successfully!')
        return redirect('view_report', pk=report.id)
    
    return render(request, 'reports/generate_inventory_report.html')

@login_required
def generate_payment_report(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if not all([start_date, end_date, title]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('generate_payment_report')
        
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
      
        report = Report.objects.create(
            report_type='payment',
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            generated_by=request.user
        )
        
        messages.success(request, 'Payment report generated successfully!')
        return redirect('view_report', pk=report.id)
    
    return render(request, 'reports/generate_payment_report.html')

@login_required
def view_report(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    report = get_object_or_404(Report, pk=pk)
    context = {'report': report}
    

    if report.report_type == 'sales':
 
        orders = Order.objects.filter(
            order_date__date__gte=report.start_date,
            order_date__date__lte=report.end_date
        )
        

        total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        

        from django.db.models import F
        top_items = OrderItem.objects.filter(
            order__order_date__date__gte=report.start_date,
            order__order_date__date__lte=report.end_date
        ).values('item__name').annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum(F('price_at_order') * F('quantity'))
        ).order_by('-total_quantity')[:5]
        
        context.update({
            'orders': orders,
            'total_sales': total_sales,
            'top_items': top_items,
            'order_count': orders.count(),
        })
    
    elif report.report_type == 'inventory':

        inventory = Inventory.objects.all()
        

        low_stock = inventory.filter(quantity__lte=50)
        
        context.update({
            'inventory': inventory,
            'low_stock': low_stock,
            'total_items': inventory.count(),
            'low_stock_count': low_stock.count(),
        })
    
    elif report.report_type == 'payment':

        orders = Order.objects.filter(
            payments__transaction_date__date__gte=report.start_date,
            payments__transaction_date__date__lte=report.end_date
        ).distinct()
        
        payment_methods = Order.objects.filter(
            payments__transaction_date__date__gte=report.start_date,
            payments__transaction_date__date__lte=report.end_date
        ).values('payments__payment_method').annotate(
            count=Count('id'),
            total=Sum('payments__amount')
        )
        
        context.update({
            'orders': orders,
            'payment_methods': payment_methods,
            'order_count': orders.count(),
        })
    
    return render(request, 'reports/view_report.html', context)
