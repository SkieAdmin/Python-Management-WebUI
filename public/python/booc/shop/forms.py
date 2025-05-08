from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['full_name', 'email', 'address', 'contact', 'receipt']
        widgets = {
            'address': forms.Textarea(attrs={'rows':3}),
        }
