from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Business, Product, Contact, Warehouse

class RegisterForm(UserCreationForm):
    business_name=forms.CharField(max_length=100,label='Business name')
    email=forms.EmailField()
    class Meta:
        model=User
        fields=['username','email','password1','password2','business_name']

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=['name','sku','barcode','category','price','cost','reorder_level','active']

class ContactForm(forms.ModelForm):
    class Meta:
        model=Contact
        fields=['name','phone','email','address']
        widgets={'address':forms.Textarea(attrs={'rows':3})}

class BusinessForm(forms.ModelForm):
    class Meta:
        model=Business
        fields=['name','address','phone','receipt_note']
        widgets={'address':forms.Textarea(attrs={'rows':3})}

class NewBusinessForm(forms.ModelForm):
    class Meta:
        model=Business
        fields=['name','currency']

class WarehouseForm(forms.ModelForm):
    class Meta:
        model=Warehouse
        fields=['name']

class InventoryForm(forms.Form):
    product=forms.ModelChoiceField(queryset=Product.objects.none())
    warehouse=forms.ModelChoiceField(queryset=Warehouse.objects.none())
    quantity=forms.IntegerField(min_value=1,max_value=1000000)
    action=forms.ChoiceField(choices=[('receive','Receive purchase'),('add','Stock increase'),('remove','Stock decrease'),('transfer','Transfer stock')])
    destination=forms.ModelChoiceField(queryset=Warehouse.objects.none(),required=False)
    supplier=forms.ModelChoiceField(queryset=Contact.objects.none(),required=False)
    unit_cost=forms.DecimalField(max_digits=12,decimal_places=2,min_value=0,required=False)
    reference=forms.CharField(max_length=120,label='Reference / reason')
    request_key=forms.UUIDField(widget=forms.HiddenInput)
    def __init__(self,*args,business,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['product'].queryset=Product.objects.filter(business=business,active=True)
        for field in ['warehouse','destination']:self.fields[field].queryset=Warehouse.objects.filter(business=business)
        self.fields['supplier'].queryset=Contact.objects.filter(business=business,kind='supplier')
    def clean(self):
        data=super().clean()
        if data.get('action')=='receive' and data.get('unit_cost') is None:self.add_error('unit_cost','Enter the purchase unit cost.')
        if data.get('action')=='transfer' and (not data.get('destination') or data.get('destination')==data.get('warehouse')):
            self.add_error('destination','Choose a different destination warehouse.')
        return data
