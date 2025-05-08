from django import forms
from .models import Inventory, Supplies


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory 
        fields = [
            'name',             
            'description',        
            'quantity',          
            'price',              
            'image',              
            'is_available',       
            'low_stock_threshold' 
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class SuppliesForm(forms.ModelForm):
    class Meta:
        model = Supplies
        fields = [
            'inventory',      
            'supplier_name',     
            'quantity_supplied', 
            'supply_date',      
            'cost'              
        ]
        widgets = {
            'supply_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
