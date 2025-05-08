from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Inventory, Supplies
from .forms import InventoryForm, SuppliesForm

@login_required
def inventory_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    inventory = Inventory.objects.all().order_by('name')
    low_stock = Inventory.objects.filter(quantity__lte=50).count()
    
    context = {
        'inventory': inventory,
        'low_stock': low_stock,
    }
    
    return render(request, 'inventory/inventory_list.html', context)

@login_required
def add_inventory(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item added successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryForm()
    
    return render(request, 'inventory/add_inventory.html', {'form': form})

@login_required
def edit_inventory(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, request.FILES, instance=inventory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryForm(instance=inventory)
    
    return render(request, 'inventory/edit_inventory.html', {'form': form, 'inventory': inventory})

@login_required
def delete_inventory(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        inventory.delete()
        messages.success(request, 'Inventory item deleted successfully!')
        return redirect('inventory_list')
    
    return render(request, 'inventory/delete_inventory.html', {'inventory': inventory})

@login_required
def supplies_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    supplies = Supplies.objects.all().order_by('-supply_date')
    return render(request, 'inventory/supplies_list.html', {'supplies': supplies})

@login_required
def add_supplies(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('menu')
    
    if request.method == 'POST':
        form = SuppliesForm(request.POST)
        if form.is_valid():
            supplies = form.save(commit=False)
            supplies.created_by = request.user
            supplies.save()
            messages.success(request, 'Supplies added successfully!')
            return redirect('supplies_list')
    else:
        form = SuppliesForm()
    
    return render(request, 'inventory/add_supplies.html', {'form': form})
