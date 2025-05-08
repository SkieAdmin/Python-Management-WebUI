from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Order, Reservation, Profile, MenuItem

# USER REGISTRATION FORM
class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, help_text="Enter your full name.")
    address = forms.CharField(widget=forms.Textarea, required=True, help_text="Enter your address.")
    phone_number = forms.CharField(max_length=15, required=True, help_text="Enter your phone number.")
    email_address = forms.EmailField(required=True, help_text="Enter a valid email address.")
    landmark = forms.CharField(max_length=255, required=False, help_text="Optional landmark for your address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()

        Profile.objects.create(
            user=user,
            full_name=self.cleaned_data['full_name'],
            address=self.cleaned_data['address'],
            phone_number=self.cleaned_data['phone_number'],
            email_address=self.cleaned_data['email_address'],
            landmark=self.cleaned_data['landmark']
        )

        return user

# PROFILE EDIT FORM
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'address', 'phone_number', 'email_address', 'landmark']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# ORDER FORM
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['item', 'quantity']

# ORDER PAYMENT FORM
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['gcash_reference','gcash_screenshot']

# RESERVATION PAYMENT FORM (For customers to upload proof of payment)
class ReservationPaymentForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['gcash_reference', 'gcash_screenshot']

# RESERVATION FORM (Customer form)
class ReservationForm(forms.ModelForm):
    kilos = forms.ChoiceField(choices=[(20, '20 kg'), (30, '30 kg'), (40, '40 kg'), 
                                        (50, '50 kg'), (60, '60 kg'), (70, '70 kg')])
    delivery_date = forms.DateField(widget=forms.SelectDateWidget())

    class Meta:
        model = Reservation
        fields = ['kilos', 'delivery_date', 'package_deal', 'delivery_option']

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data.get('delivery_date')
        today = timezone.now().date()
        
        if delivery_date and delivery_date < today:
            raise forms.ValidationError("You cannot select a past date for delivery. Please choose today or a future date.")
            
        return delivery_date

# MENU ITEM FORM (Admin)
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# RESERVATION UPDATE FORM (Admin form)
class ReservationUpdateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['status', 'payment_status', 'delivery_option', 'price', 'delivery_date', 'package_deal']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget = forms.Select(choices=Reservation.STATUS_CHOICES)
        self.fields['payment_status'].widget = forms.Select(choices=Reservation.PAYMENT_STATUS_CHOICES)
        self.fields['delivery_option'].widget = forms.Select(choices=Reservation.DELIVERY_OPTION_CHOICES)
        self.fields['package_deal'].widget = forms.Select(choices=Reservation.PACKAGE_DEAL_CHOICES)