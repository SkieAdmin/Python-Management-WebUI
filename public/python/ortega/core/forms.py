from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser, Product


class CustomRegisterForm(UserCreationForm):
    """
    Registration form extending Django's built-in UserCreationForm,
    customized for our CustomUser model.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class CustomLoginForm(forms.Form):
    """
    Simple login form with username and password fields.
    """
    username = forms.CharField(label='Username')
    password = forms.CharField(widget=forms.PasswordInput)


class AddProductForm(forms.ModelForm):
    """
    Form for admins to add new products, based on the Product model.
    """
    CATEGORY_CHOICES = [
        ('cement', 'Cement'),
        ('nails', 'Nails'),
        ('lumber', 'Lumber'),
        ('tools', 'Tools'),
        ('other', 'Other')
    ]
    
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))
    
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'unit',
            'category',
            'price',
            'stock_quantity',
            'reorder_level',
            'image',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter product description', 'rows': 3}),
            'unit': forms.TextInput(attrs={'placeholder': 'Enter unit (e.g., kg, pcs)'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Enter product price', 'min': '0', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'placeholder': 'Enter quantity', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'placeholder': 'Enter reorder level', 'min': '0'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make admin field not required in the form as we'll set it in the view
        if 'admin' in self.fields:
            self.fields['admin'].required = False
        
        # Remove last_restock_date from required fields as we'll set it automatically
        if 'last_restock_date' in self.fields:
            self.fields['last_restock_date'].required = False


class AdminLoginForm(forms.Form):
    """
    Simple login form for admins with email and password.
    """
    email = forms.EmailField(
        label='Email',
        max_length=100,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter admin email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter admin password'})
    )


class UsernameForm(forms.ModelForm):
    """
    Form for users to update their username on the profile page.
    """
    class Meta:
        model = CustomUser
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'space-mono-input',
                'placeholder': 'Enter new username…'
            })
        }
