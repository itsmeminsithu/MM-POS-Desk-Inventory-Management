import csv
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError, OperationalError
from django.db.models import Sum, F, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import Business, Membership, Product, Warehouse, Stock, Contact, Sale, Movement, Purchase, InventoryOperation
from .forms import RegisterForm,ProductForm,ContactForm,BusinessForm,NewBusinessForm,WarehouseForm,InventoryForm
from .services import checkout,void_sale,move,StockError


def tenant(owner=False):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request,*args,**kwargs):
            members=Membership.objects.filter(user=request.user,business__active=True).select_related('business')
            member=members.filter(business_id=request.session.get('business_id')).first() or members.first()
            if not member:return redirect('new_business')
            request.business=member.business;request.role=member.role
            if owner and member.role!='owner':raise PermissionDenied('Owner access is required.')
            request.session['business_id']=member.business_id
            return view(request,*args,**kwargs)
        return wrapped
    return decorator

def context(request):
    return {'business':getattr(request,'business',None),'role':getattr(request,'role',None),
        'businesses':Membership.objects.filter(user=request.user,business__active=True).select_related('business') if request.user.is_authenticated else []}

def create_business(user,name,currency='MMK'):
    business=Business.objects.create(name=name,slug=(slugify(name)[:30] or 'store')+'-'+uuid.uuid4().hex[:8],currency=currency)
    Membership.objects.create(user=user,business=business,role='owner')
    Warehouse.objects.create(business=business,name='Main store')
    return business

def home(request):
    return redirect('dashboard' if request.user.is_authenticated else 'login')

def register(request):
    if request.user.is_authenticated:return redirect('dashboard')
    form=RegisterForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            user=form.save();business=create_business(user,form.cleaned_data['business_name'])
        login(request,user);request.session['business_id']=business.pk
        messages.success(request,'Your business is ready. Add products or load the sample catalog from Settings.')
        return redirect('dashboard')
    return render(request,'registration/register.html',{'form':form})

@login_required
def new_business(request):
    form=NewBusinessForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():business=create_business(request.user,form.cleaned_data['name'],form.cleaned_data['currency'])
        request.session['business_id']=business.pk;return redirect('dashboard')
    return render(request,'retail/form.html',{'form':form,'title':'Create a business','subtitle':'A separate workspace for your products, inventory and sales.'})

@login_required
@require_POST
def switch(request):
    member=get_object_or_404(Membership,user=request.user,business_id=request.POST.get('business'),business__active=True)
    request.session['business_id']=member.business_id;return redirect('dashboard')

@tenant()
def dashboard(request):
    b=request.business;today=timezone.localdate()
    sales=Sale.objects.filter(business=b,voided=False)
    stocks=Stock.objects.filter(product__business=b,warehouse__business=b).select_related('product','warehouse')
    revenue=sales.filter(created__date=today).aggregate(n=Sum('total'))['n'] or 0
    low=stocks.filter(quantity__lte=F('product__reorder_level'),product__active=True)
    days=[]
    for offset in range(6,-1,-1):
        day=today-timedelta(days=offset);amount=sales.filter(created__date=day).aggregate(n=Sum('total'))['n'] or 0
        days.append({'label':day.strftime('%a'),'amount':amount})
    maximum=max([d['amount'] for d in days]) or 1
    for d in days:d['height']=max(2,float(d['amount']/maximum)*100)
    return render(request,'retail/dashboard.html',{'revenue':revenue,'today_count':sales.filter(created__date=today).count(),
        'units':stocks.aggregate(n=Sum('quantity'))['n'] or 0,'low_count':low.count(),'low':low[:8],
        'recent':Sale.objects.filter(business=b)[:6],'days':days,'product_count':Product.objects.filter(business=b,active=True).count()})

@tenant()
def products(request):
    query=request.GET.get('q','').strip()[:100]
    items=Product.objects.filter(business=request.business)
    if query:items=items.filter(Q(name__icontains=query)|Q(sku__icontains=query)|Q(barcode=query))
    items=items.annotate(units=Sum('stock__quantity'))
    return render(request,'retail/products.html',{'products':items,'query':query})

@tenant(owner=True)
def product_edit(request,pk=None):
    product=get_object_or_404(Product,business=request.business,pk=pk) if pk else None
    form=ProductForm(request.POST or None,instance=product)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False);item.business=request.business
        try:
            with transaction.atomic():
                item.save()
                for w in Warehouse.objects.filter(business=request.business):Stock.objects.get_or_create(product=item,warehouse=w)
            messages.success(request,'Product saved. Use Inventory to receive or adjust stock.')
            return redirect('products')
        except IntegrityError:form.add_error('sku','This SKU already exists in your business.')
    return render(request,'retail/form.html',{'form':form,'title':'Edit product' if product else 'Add product','subtitle':'Prices are per whole unit. Stock changes are recorded separately.'})

@tenant()
def inventory(request):
    return render(request,'retail/inventory.html',{'stocks':Stock.objects.filter(product__business=request.business,warehouse__business=request.business).select_related('product','warehouse'),
        'movements':Movement.objects.filter(business=request.business).select_related('product','warehouse','actor')[:100]})

@tenant(owner=True)
def inventory_edit(request):
    form=InventoryForm(request.POST or None,business=request.business,initial={'request_key':uuid.uuid4()})
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data;b=request.business
        try:
            with transaction.atomic():
                # Every inventory form submission has a one-time server-issued session token.
                tokens=request.session.get('inventory_tokens',[])
                key=str(d['request_key'])
                if key not in tokens:raise StockError('This form was already submitted or expired. Open a new inventory form.')
                InventoryOperation.objects.create(business=b,key=d['request_key'])
                p,w,q=d['product'],d['warehouse'],d['quantity']
                if d['action']=='receive':
                    if Purchase.objects.filter(business=b,request_key=d['request_key']).exists():raise StockError('Purchase already received.')
                    Purchase.objects.create(business=b,product=p,warehouse=w,supplier=d['supplier'],quantity=q,unit_cost=d['unit_cost'],reference=d['reference'],actor=request.user,request_key=d['request_key'])
                    move(b,p,w,q,request.user,'purchase',d['reference'])
                elif d['action']=='transfer':
                    move(b,p,w,-q,request.user,'transfer out',d['reference'])
                    move(b,p,d['destination'],q,request.user,'transfer in',d['reference'])
                else:move(b,p,w,q if d['action']=='add' else -q,request.user,'adjustment',d['reference'])
            request.session['inventory_tokens']=[t for t in tokens if t!=key]
            messages.success(request,'Inventory updated. Movement history recorded.');return redirect('inventory')
        except (StockError,IntegrityError) as e:form.add_error(None,str(e) if isinstance(e,StockError) else 'This operation was already recorded.')
    if request.method!='POST':
        request.session['inventory_tokens']=(request.session.get('inventory_tokens',[])+[str(form.initial['request_key'])])[-20:]
    return render(request,'retail/form.html',{'form':form,'title':'Move inventory','subtitle':'Receive purchases, record adjustments or transfer between warehouses. Purchases do not automatically change the product’s reference cost.'})

@tenant(owner=True)
def warehouse_add(request):
    form=WarehouseForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                item=form.save(commit=False);item.business=request.business;item.save()
                for p in Product.objects.filter(business=request.business):Stock.objects.get_or_create(product=p,warehouse=item)
            return redirect('inventory')
        except IntegrityError:form.add_error('name','Warehouse name already exists.')
    return render(request,'retail/form.html',{'form':form,'title':'Add warehouse'})

@tenant(owner=True)
def purchases(request):
    return render(request,'retail/purchases.html',{'purchases':Purchase.objects.filter(business=request.business).select_related('product','warehouse','supplier')})

@tenant()
def contacts(request,kind):
    if kind not in ['customer','supplier']:raise PermissionDenied
    if kind=='supplier' and request.role!='owner':raise PermissionDenied
    return render(request,'retail/contacts.html',{'contacts':Contact.objects.filter(business=request.business,kind=kind),'kind':kind})

@tenant(owner=True)
def contact_edit(request,kind,pk=None):
    if kind not in ['customer','supplier']:raise PermissionDenied
    item=get_object_or_404(Contact,business=request.business,kind=kind,pk=pk) if pk else None
    form=ContactForm(request.POST or None,instance=item)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False);item.business=request.business;item.kind=kind;item.save();return redirect('contacts',kind=kind)
    return render(request,'retail/form.html',{'form':form,'title':('Edit ' if pk else 'Add ')+kind})

@tenant()
def pos(request):
    b=request.business
    products=list(Product.objects.filter(business=b,active=True).values('id','name','sku','barcode','category','price'))
    stocks=list(Stock.objects.filter(product__business=b,warehouse__business=b).values('product_id','warehouse_id','quantity'))
    return render(request,'retail/pos.html',{'catalog':products,'stocks':stocks,'warehouses':Warehouse.objects.filter(business=b),'customers':Contact.objects.filter(business=b,kind='customer')})

@require_POST
@tenant()
def sale_create(request):
    try:
        payload=json.loads(request.body)
        if not isinstance(payload,dict):raise StockError('Invalid checkout payload.')
        sale=checkout(request.business,request.user,payload)
        return JsonResponse({'receipt':reverse('receipt',args=[sale.pk])})
    except (StockError,ValueError,TypeError) as e:return JsonResponse({'error':str(e)},status=400)
    except (OperationalError,IntegrityError):return JsonResponse({'error':'Inventory is busy. Retry this same checkout in a moment.'},status=409)

@tenant()
def sales(request):return render(request,'retail/sales.html',{'sales':Sale.objects.filter(business=request.business).select_related('cashier')})

@tenant()
def receipt(request,pk):
    return render(request,'retail/receipt.html',{'sale':get_object_or_404(Sale,business=request.business,pk=pk)})

@tenant(owner=True)
@require_POST
def sale_void(request,pk):
    try:void_sale(request.business,pk,request.user,request.POST.get('reason',''))
    except StockError as e:messages.error(request,str(e))
    else:messages.success(request,'Full return recorded and inventory restored. Any money refund must be completed separately.')
    return redirect('receipt',pk=pk)

@tenant(owner=True)
def reports(request):
    sales=Sale.objects.filter(business=request.business,voided=False)
    start=request.GET.get('start','');end=request.GET.get('end','')
    from datetime import date
    try:
        if start:sales=sales.filter(created__date__gte=date.fromisoformat(start))
        if end:sales=sales.filter(created__date__lte=date.fromisoformat(end))
        if start and end and start>end:raise ValueError
    except ValueError:
        messages.error(request,'Choose a valid date range.');return redirect('reports')
    if request.GET.get('export')=='csv':
        response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="mm-pos-sales.csv"'
        writer=csv.writer(response);writer.writerow(['Receipt','Date','Customer','Subtotal','Discount','Tax','Total','Currency','Method'])
        def safe(value):
            value=str(value)
            return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value
        for s in sales:writer.writerow([safe(v) for v in [str(s.pk),s.created.isoformat(),s.customer_name,s.subtotal,s.discount,s.tax,s.total,s.currency,s.method]])
        return response
    totals=sales.aggregate(revenue=Sum('total'),tax=Sum('tax'),discount=Sum('discount'))
    cost=sum(line.quantity*line.cost for sale in sales.prefetch_related('lines') for line in sale.lines.all())
    margin=(totals['revenue'] or 0)-(totals['tax'] or 0)-cost
    return render(request,'retail/reports.html',{'totals':totals,'count':sales.count(),'margin':margin,'start':start,'end':end,'methods':sales.values('method').annotate(amount=Sum('total'))})

@tenant(owner=True)
def settings_view(request):
    form=BusinessForm(request.POST or None,instance=request.business)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Business settings saved.');return redirect('settings')
    return render(request,'retail/settings.html',{'form':form,'members':Membership.objects.filter(business=request.business).select_related('user')})

@tenant(owner=True)
@require_POST
def sample(request):
    b=request.business
    with transaction.atomic():
        if Product.objects.filter(business=b).exists():
            messages.error(request,'Sample catalog is available only for an empty business.');return redirect('settings')
        w=Warehouse.objects.filter(business=b).first()
        for i,(name,category,price,cost,qty) in enumerate([
            ('Everyday notebook','Stationery',4500,2500,32),('Ceramic cup','Home',12000,7000,18),('Canvas tote','Accessories',16000,9500,24),
            ('Desk pen set','Stationery',6000,3000,4),('Travel bottle','Accessories',22000,14000,12),('Cotton hand towel','Home',8500,4500,7)],1):
            # Sample prices are nominal amounts in this workspace currency, not converted prices.
            p=Product.objects.create(business=b,name=name,sku=f'MM-{i:03}',barcode=f'88000000000{i}',category=category,price=price,cost=cost)
            for warehouse in Warehouse.objects.filter(business=b):Stock.objects.get_or_create(product=p,warehouse=warehouse)
            move(b,p,w,qty,request.user,'opening','Sample opening stock')
        Contact.objects.create(business=b,kind='supplier',name='Sample Supply Co.')
    messages.success(request,'Sample inventory added. Prices are examples; update them before real sales.')
    return redirect('products')


@tenant(owner=True)
def team_add(request):
    from django.contrib.auth.forms import UserCreationForm
    form=UserCreationForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            user=form.save()
            Membership.objects.create(business=request.business,user=user,role='cashier')
        messages.success(request,'Cashier account created. Share the credentials privately.');return redirect('settings')
    return render(request,'retail/form.html',{'form':form,'title':'Create cashier account','subtitle':'Cashiers can use POS, view inventory, customers and receipts. They cannot change stock, costs, settings or record returns.'})

@tenant(owner=True)
@require_POST
def team_remove(request,pk):
    member=get_object_or_404(Membership,pk=pk,business=request.business,role='cashier')
    member.delete();messages.success(request,'Cashier access removed from this business.');return redirect('settings')
