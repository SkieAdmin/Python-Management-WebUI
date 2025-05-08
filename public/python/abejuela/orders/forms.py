
from django import forms  
from .models import Order, OrderItem, PaymentTransaction  

class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = Order  
        fields = ['notes'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class OrderItemForm(forms.ModelForm):
   
    class Meta:
       
        model = OrderItem  
        fields = ['item', 'quantity'] 

    def __init__(self, *args, **kwargs):
       
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        self.fields['item'].queryset = self.fields['item'].queryset.filter(is_available=True)


class PaymentForm(forms.ModelForm):
  
    class Meta:
       
        model = PaymentTransaction  
        fields = [
            'amount',          
            'payment_method',  
            'reference_number', 
            'receipt_image',   
            'notes'             
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),  
        }
        
    def __init__(self, *args, **kwargs):
        
        self.order = kwargs.pop('order', None)  
        super().__init__(*args, **kwargs)
       
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        
     
        if self.order:
            self.fields['amount'].initial = self.order.total_amount
            self.fields['amount'].widget.attrs['readonly'] = True


class OrderStatusForm(forms.ModelForm):
    class Meta:

        model = Order  
        fields = ['status']  
        
    def __init__(self, *args, **kwargs):
    
        super().__init__(*args, **kwargs)
        
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class PaymentStatusForm(forms.ModelForm):

    class Meta:
       
        model = Order  
        fields = ['payment_status']  
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
