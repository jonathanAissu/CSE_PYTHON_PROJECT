from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserProfile, Stock, Feedstock, Farmer, ChickRequest
from django.forms import ModelForm
from django.core.exceptions import ValidationError

class UserCreation(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    is_manager = forms.BooleanField(required=False, widget=forms.HiddenInput())
    is_salesagent = forms.BooleanField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password1', 'password2', 'is_manager', 'is_salesagent')
        
    def __init__(self, *args, **kwargs):
        super(UserCreation, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to the form fields
        for field_name in ('username', 'password1', 'password2'):
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
            
    def clean(self):
        cleaned_data = super().clean()
        is_manager = cleaned_data.get('is_manager')
        is_salesagent = cleaned_data.get('is_salesagent')
        
        # Ensure at least one role is selected
        if not (is_manager or is_salesagent):
            raise ValidationError("Please select a role (Manager or Sales Agent)")
            
        return cleaned_data

    def save(self, commit=True):
        user = super(UserCreation, self).save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.is_manager = self.cleaned_data.get('is_manager', False)
        user.is_salesagent = self.cleaned_data.get('is_salesagent', False)
        
        if commit:
            user.is_active = True
            user.is_staff = True
            user.save()
        return user

class StockForm(ModelForm):
    class Meta:
        model = Stock
        fields = '__all__'
        widgets = {
            'stock_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'chick_type': forms.Select(attrs={'class': 'form-control'}),
            'chick_breed': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control'}),
            'chicks_period': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FeedstockForm(ModelForm):
    class Meta:
        model = Feedstock
        fields = '__all__'
        widgets = {
            'name_of_feeds': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_of_feeds': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_of_feeds': forms.TextInput(attrs={'class': 'form-control'}),
            'brand_of_feeds': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'buying_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class FarmerForm(ModelForm):
    class Meta:
        model = Farmer
        exclude = ['status', 'date_registered']  # Exclude status and date fields
        widgets = {
            'farmer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'farmer_gender': forms.Select(attrs={'class': 'form-control'}),
            'nin': forms.TextInput(attrs={'class': 'form-control'}),
            'recommender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recommender_nin': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'farmer_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'type_of_farmer': forms.Select(attrs={'class': 'form-control'}),
        }

class ChickRequestForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show approved farmers
        self.fields['farmer_name'].queryset = Farmer.objects.filter(status='approved')
    
    class Meta:
        model = ChickRequest
        exclude = ['status', 'delivered']  # Exclude these fields - they should be set automatically
        widgets = {
            'farmer_name': forms.Select(attrs={'class': 'form-control'}),
            'chicks_type': forms.Select(attrs={'class': 'form-control'}),
            'chicks_breed': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'feeds_needed': forms.Select(attrs={'class': 'form-control'}),
            'chicks_period': forms.NumberInput(attrs={'class': 'form-control'}),
        }
