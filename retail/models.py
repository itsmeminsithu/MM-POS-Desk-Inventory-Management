"""Copyright (c) 2026 Min SiThu (itsmeminsithu). SPDX-License-Identifier: MIT."""
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

class Business(models.Model):
    name=models.CharField(max_length=100)
    slug=models.SlugField(unique=True)
    currency=models.CharField(max_length=3,choices=[('MMK','MMK'),('THB','THB'),('USD','USD')],default='MMK')
    address=models.TextField(blank=True)
    phone=models.CharField(max_length=60,blank=True)
    receipt_note=models.CharField(max_length=200,default='Thank you for shopping with us.')
    active=models.BooleanField(default=True)
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.name

class Membership(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    role=models.CharField(max_length=10,choices=[('owner','Owner'),('cashier','Cashier')],default='cashier')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['business','user'],name='member_once')]

class Warehouse(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE)
    name=models.CharField(max_length=80)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['business','name'],name='warehouse_name')]
    def __str__(self):return self.name

class Product(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE)
    name=models.CharField(max_length=150)
    sku=models.CharField(max_length=60)
    barcode=models.CharField(max_length=80,blank=True)
    category=models.CharField(max_length=80,default='General')
    price=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(0)])
    cost=models.DecimalField(max_digits=12,decimal_places=2,default=0,validators=[MinValueValidator(0)])
    reorder_level=models.PositiveIntegerField(default=5)
    active=models.BooleanField(default=True)
    class Meta:
        ordering=['name']
        constraints=[models.UniqueConstraint(fields=['business','sku'],name='business_sku')]
    def __str__(self):return f'{self.name} · {self.sku}'

class Stock(models.Model):
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['product','warehouse'],name='stock_location')]

class Contact(models.Model):
    business=models.ForeignKey(Business,on_delete=models.CASCADE)
    kind=models.CharField(max_length=10,choices=[('customer','Customer'),('supplier','Supplier')])
    name=models.CharField(max_length=120)
    phone=models.CharField(max_length=60,blank=True)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    class Meta:ordering=['name']
    def __str__(self):return self.name

class Sale(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    business=models.ForeignKey(Business,on_delete=models.PROTECT)
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT)
    cashier=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    customer=models.ForeignKey(Contact,null=True,blank=True,on_delete=models.PROTECT)
    customer_name=models.CharField(max_length=120,default='Walk-in customer')
    business_name=models.CharField(max_length=100)
    business_address=models.TextField(blank=True)
    receipt_note=models.CharField(max_length=200,blank=True)
    currency=models.CharField(max_length=3)
    subtotal=models.DecimalField(max_digits=16,decimal_places=2)
    discount=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    tax_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    tax=models.DecimalField(max_digits=16,decimal_places=2)
    total=models.DecimalField(max_digits=16,decimal_places=2)
    tendered=models.DecimalField(max_digits=16,decimal_places=2)
    change=models.DecimalField(max_digits=16,decimal_places=2)
    method=models.CharField(max_length=20)
    reference=models.CharField(max_length=120,blank=True)
    request_key=models.UUIDField()
    request_hash=models.CharField(max_length=64)
    voided=models.BooleanField(default=False)
    void_reason=models.CharField(max_length=250,blank=True)
    voided_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.PROTECT,related_name='voided_sales')
    created=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created']
        constraints=[models.UniqueConstraint(fields=['business','request_key'],name='sale_request_once')]
    @property
    def number(self):return str(self.id).upper()[:8]

class SaleLine(models.Model):
    sale=models.ForeignKey(Sale,on_delete=models.CASCADE,related_name='lines')
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    name=models.CharField(max_length=150)
    sku=models.CharField(max_length=60)
    quantity=models.PositiveIntegerField()
    price=models.DecimalField(max_digits=12,decimal_places=2)
    cost=models.DecimalField(max_digits=12,decimal_places=2)
    total=models.DecimalField(max_digits=16,decimal_places=2)

class Movement(models.Model):
    business=models.ForeignKey(Business,on_delete=models.PROTECT)
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT)
    delta=models.IntegerField()
    kind=models.CharField(max_length=20)
    note=models.CharField(max_length=250)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    sale=models.ForeignKey(Sale,null=True,blank=True,on_delete=models.PROTECT)
    created=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['-created','-id']

class Purchase(models.Model):
    business=models.ForeignKey(Business,on_delete=models.PROTECT)
    product=models.ForeignKey(Product,on_delete=models.PROTECT)
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT)
    supplier=models.ForeignKey(Contact,null=True,blank=True,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField()
    unit_cost=models.DecimalField(max_digits=12,decimal_places=2)
    reference=models.CharField(max_length=120)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    request_key=models.UUIDField()
    created=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-created']
        constraints=[models.UniqueConstraint(fields=['business','request_key'],name='purchase_request_once')]
    @property
    def total(self):return self.quantity*self.unit_cost

class InventoryOperation(models.Model):
    business=models.ForeignKey(Business,on_delete=models.PROTECT)
    key=models.UUIDField()
    created=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['business','key'],name='inventory_operation_once')]
