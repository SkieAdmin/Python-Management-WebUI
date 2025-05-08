# main/forms.py
from decimal import Decimal
from django import forms
from .models import Order, Product

class OrderForm(forms.ModelForm):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'modalNote',
            'rows': 2,
            'placeholder': 'e.g. Leave at front desk',
        })
    )

    class Meta:
        model = Order
        fields = ['product', 'quantity', 'note']
        widgets = {
            'product': forms.HiddenInput(attrs={'id': 'modalProductId'}),
            'quantity': forms.NumberInput(attrs={
                'id': 'modalQuantity',
                'min': 1,
                'value': 1,
            }),
        }

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return qty

    def save(self, commit=True):
        order = super().save(commit=False)
        # calculate total price
        order.total_price = (order.product.price * Decimal(order.quantity)).quantize(Decimal('0.01'))
        if commit:
            order.save()
        return order

class PaymentForm(forms.Form):
    order_id = forms.IntegerField(widget=forms.HiddenInput)
    receipt  = forms.ImageField()
    note     = forms.CharField(widget=forms.Textarea, required=False)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'note']
        widgets = {
            'status': forms.Select(),
            'note': forms.Textarea(attrs={'rows':2}),
        }