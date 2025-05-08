from django import forms
from django.contrib.auth.models import User
from .models import Employee, Product, Category, Inventory

# User Registration Form
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=Employee.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'role']

# Product Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'description','image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# Inventory Form
class InventoryForm(forms.ModelForm):
    adjustment = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter quantity to add/remove'
        })
    )
    
    adjustment_type = forms.ChoiceField(
        choices=[
            ('add', 'Add to Stock'),
            ('remove', 'Remove from Stock'),
            ('set', 'Set Exact Amount')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Inventory
        fields = ['quantity_in_stock', 'adjustment', 'adjustment_type']
        widgets = {
            'quantity_in_stock': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'readonly': 'readonly'
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        adjustment = cleaned_data.get('adjustment')
        adjustment_type = cleaned_data.get('adjustment_type')
        current_stock = self.instance.quantity_in_stock

        if adjustment is not None:
            if adjustment_type == 'add':
                cleaned_data['quantity_in_stock'] = current_stock + adjustment
            elif adjustment_type == 'remove':
                new_stock = current_stock - adjustment
                if new_stock < 0:
                    raise forms.ValidationError("Cannot remove more items than in stock.")
                cleaned_data['quantity_in_stock'] = new_stock
            elif adjustment_type == 'set':
                if adjustment < 0:
                    raise forms.ValidationError("Stock cannot be negative.")
                cleaned_data['quantity_in_stock'] = adjustment

        return cleaned_data

# Alternative User Registration Form with Manager PIN
from django import forms
from django.contrib.auth.models import User

ROLE_CHOICES = (
    ('manager', 'Manager'),
    ('cashier', 'Cashier'),
)

class UserRegisterForm(forms.ModelForm):
    manager_pin = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.PasswordInput,
        help_text='Required if selecting role "Manager".',
        label='Manager PIN',
    )
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password', 'role', 'manager_pin']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        manager_pin = cleaned_data.get("manager_pin")

        if role == "manager":
            if not manager_pin:
                self.add_error('manager_pin', "PIN is required for managers.")
            elif manager_pin != "123456":
                self.add_error('manager_pin', "Invalid Manager PIN.")
        return cleaned_data