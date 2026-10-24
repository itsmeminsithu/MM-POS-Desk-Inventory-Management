"""Atomic inventory changes and server-calculated checkout. Min SiThu, MIT."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import uuid
from django.db import transaction
from django.db.models import F
from .models import Stock, Product, Warehouse, Contact, Sale, SaleLine, Movement

class StockError(ValueError):pass

def money(value,maximum=Decimal('9999999999.99')):
    try:
        n=Decimal(str(value))
        if not n.is_finite() or n<0 or n>maximum or n!=n.quantize(Decimal('.01')):raise ValueError
        return n.quantize(Decimal('.01'))
    except (InvalidOperation,ValueError,TypeError):raise StockError('Enter a non-negative amount with at most two decimal places.')

def quantity(value):
    if isinstance(value,bool) or str(value).strip()!=str(int(value)):raise StockError('Quantity must be a whole number.')
    n=int(value)
    if not 1<=n<=1000000:raise StockError('Quantity must be between 1 and 1,000,000.')
    return n

def scoped(model,business,pk,**extra):
    try:return model.objects.get(business=business,pk=pk,**extra)
    except (model.DoesNotExist,ValueError,TypeError):raise StockError('The selected record is unavailable in this business.')

def move(business,product,warehouse,delta,actor,kind,note,sale=None):
    if product.business_id!=business.pk or warehouse.business_id!=business.pk:raise StockError('Invalid inventory location.')
    stock,_=Stock.objects.get_or_create(product=product,warehouse=warehouse)
    qs=Stock.objects.filter(pk=stock.pk)
    if delta<0:qs=qs.filter(quantity__gte=-delta)
    if not qs.update(quantity=F('quantity')+delta):raise StockError(f'Not enough stock for {product.name}.')
    Movement.objects.create(business=business,product=product,warehouse=warehouse,delta=delta,actor=actor,kind=kind,note=note,sale=sale)

@transaction.atomic
def checkout(business,user,payload):
    try:key=uuid.UUID(str(payload.get('request_key','')))
    except (ValueError,TypeError):raise StockError('Invalid checkout request. Reload the POS.')
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    existing=Sale.objects.filter(business=business,request_key=key).first()
    if existing:
        if existing.request_hash!=digest:raise StockError('This checkout key was already used for a different basket.')
        return existing
    warehouse=scoped(Warehouse,business,payload.get('warehouse'))
    customer=scoped(Contact,business,payload['customer'],kind='customer') if payload.get('customer') else None
    items=payload.get('items',[])
    if not isinstance(items,list) or not 1<=len(items)<=100:raise StockError('Add between 1 and 100 products.')
    lines=[];seen=set();subtotal=Decimal('0')
    for item in items:
        if not isinstance(item,dict):raise StockError('Invalid item.')
        product=scoped(Product,business,item.get('id'),active=True)
        if product.pk in seen:raise StockError('Duplicate product lines are not allowed.')
        seen.add(product.pk)
        if 'expected_price' in item and money(item['expected_price'])!=product.price:raise StockError('Product price changed. Reload the POS before collecting payment.')
        try:qty=quantity(item.get('quantity'))
        except (ValueError,TypeError,OverflowError):raise StockError('Use a positive whole-number quantity.')
        amount=product.price*qty;subtotal+=amount;lines.append((product,qty,amount))
    discount=money(payload.get('discount',0));rate=money(payload.get('tax_rate',0),Decimal('100'))
    if discount>subtotal:raise StockError('Discount cannot exceed the subtotal.')
    tax=((subtotal-discount)*rate/100).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    total=subtotal-discount+tax
    if total>Decimal('9999999999.99'):raise StockError('Sale amount exceeds the supported limit.')
    method=payload.get('method')
    if method not in ['cash','card','kpay','wavepay','bank','mmqr']:raise StockError('Choose a payment method.')
    reference=str(payload.get('reference','')).strip()[:120]
    if method!='cash' and not reference:raise StockError('Enter the reference for the payment already collected externally.')
    tendered=money(payload.get('tendered',0)) if method=='cash' else total
    if tendered<total:raise StockError('Cash received is less than the total.')
    sale=Sale.objects.create(business=business,warehouse=warehouse,cashier=user,customer=customer,
        customer_name=customer.name if customer else 'Walk-in customer',business_name=business.name,business_address=business.address,
        receipt_note=business.receipt_note,currency=business.currency,subtotal=subtotal,discount=discount,tax_rate=rate,tax=tax,total=total,
        tendered=tendered,change=tendered-total,method=method,reference=reference,request_key=key,request_hash=digest)
    for product,qty,amount in lines:
        move(business,product,warehouse,-qty,user,'sale','POS sale',sale)
        SaleLine.objects.create(sale=sale,product=product,name=product.name,sku=product.sku,quantity=qty,price=product.price,cost=product.cost,total=amount)
    return sale

@transaction.atomic
def void_sale(business,sale_id,user,reason):
    if not reason.strip():raise StockError('A return reason is required.')
    sale=Sale.objects.filter(pk=sale_id,business=business).first()
    if not sale:raise StockError('Sale not found.')
    if not Sale.objects.filter(pk=sale.pk,voided=False).update(voided=True,void_reason=reason[:250],voided_by=user):return sale
    for line in sale.lines.select_related('product'):
        move(business,line.product,sale.warehouse,line.quantity,user,'return',reason[:250],sale)
    return sale
