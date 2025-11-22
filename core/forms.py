from django import forms
from django.db.models import Q
from .models import Product, Category, UnitOfMeasure, InventoryOperation, OperationLine, Partner, Location, Warehouse

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'abbreviation']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'maxlength': '10'}),
        }

class DeliveryForm(forms.ModelForm):
    class Meta:
        model = InventoryOperation
        fields = ['partner', 'source_location', 'scheduled_date', 'notes']
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'source_location': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter partners to only customers
        self.fields['partner'].queryset = Partner.objects.filter(
            Q(partner_type='customer') | Q(partner_type='both')
        )
        self.fields['partner'].label = 'Customer'

class InternalTransferForm(forms.ModelForm):
    class Meta:
        model = InventoryOperation
        fields = ['source_location', 'destination_location', 'scheduled_date', 'notes']
        widgets = {
            'source_location': forms.Select(attrs={'class': 'form-select'}),
            'destination_location': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = InventoryOperation
        fields = ['source_location', 'scheduled_date', 'notes']
        widgets = {
            'source_location': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'uom', 'min_stock', 'cost', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = InventoryOperation
        fields = ['partner', 'destination_location', 'scheduled_date', 'notes']
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'destination_location': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter partners to only suppliers
        self.fields['partner'].queryset = Partner.objects.filter(
            Q(partner_type='supplier') | Q(partner_type='both')
        )
        self.fields['partner'].label = 'Supplier'

class OperationLineForm(forms.ModelForm):
    class Meta:
        model = OperationLine
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ['name', 'partner_type', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'partner_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

