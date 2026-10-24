import json
import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase,Client
from django.urls import reverse
from .models import Business,Membership,Product,Warehouse,Stock,Sale,SaleLine,Contact,Movement,Purchase,InventoryOperation
from .services import checkout,StockError,void_sale

class DeskTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('owner',password='Example-long-129!')
        self.cashier=User.objects.create_user('cashier',password='Example-long-129!')
        self.other=User.objects.create_user('other',password='Example-long-129!')
        self.business=Business.objects.create(name='My shop',slug='my-shop')
        self.foreign=Business.objects.create(name='Other shop',slug='other-shop')
        Membership.objects.create(business=self.business,user=self.owner,role='owner')
        Membership.objects.create(business=self.business,user=self.cashier,role='cashier')
        Membership.objects.create(business=self.foreign,user=self.other,role='owner')
        self.warehouse=Warehouse.objects.create(business=self.business,name='Main')
        self.fw=Warehouse.objects.create(business=self.foreign,name='Other')
        self.product=Product.objects.create(business=self.business,name='Notebook',sku='NOTE',price='12.50',cost='5.00')
        self.fp=Product.objects.create(business=self.foreign,name='Other product',sku='NOTE',price='99.00')
        Stock.objects.create(product=self.product,warehouse=self.warehouse,quantity=10)
        Stock.objects.create(product=self.fp,warehouse=self.fw,quantity=20)
        self.client.force_login(self.owner)
    def payload(self,**changes):
        data={'request_key':str(uuid.uuid4()),'warehouse':self.warehouse.pk,'items':[{'id':self.product.pk,'quantity':2}],'discount':'0','tax_rate':'0','method':'cash','tendered':'30'}
        data.update(changes);return data
    def post_sale(self,data):return self.client.post(reverse('sale_create'),json.dumps(data),content_type='application/json')
    def test_all_pages_render(self):
        for name in ['dashboard','products','inventory','inventory_edit','warehouse_add','purchases','pos','sales','reports','settings','product_new','new_business','team_add']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200,name)
        for kind in ['customer','supplier']:
            for name in ['contacts','contact_new']:self.assertEqual(self.client.get(reverse(name,args=[kind])).status_code,200)
        self.client.logout()
        for name in ['login','register']:self.assertEqual(self.client.get(reverse(name)).status_code,200)
    def test_register_business_and_no_privilege_escalation(self):
        self.client.logout()
        self.client.post(reverse('register'),{'username':'newowner','email':'owner@example.com','business_name':'New desk','password1':'Another-long-pass-351!','password2':'Another-long-pass-351!','is_staff':'1','is_superuser':'1'})
        user=User.objects.get(username='newowner')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(Membership.objects.get(user=user).role,'owner')
        self.assertTrue(Warehouse.objects.filter(business__name='New desk').exists())
    def test_sale_server_totals_change_and_stock(self):
        payload=self.payload(discount='2',tax_rate='10',total='0.01',items=[{'id':self.product.pk,'quantity':2,'price':'0.01'}])
        self.assertEqual(self.post_sale(payload).status_code,200)
        sale=Sale.objects.get();self.assertEqual(sale.subtotal,Decimal('25'));self.assertEqual(sale.tax,Decimal('2.30'))
        self.assertEqual(sale.total,Decimal('25.30'));self.assertEqual(sale.change,Decimal('4.70'))
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,8)
        self.assertEqual(Movement.objects.get().delta,-2)
        self.assertEqual(self.client.get(reverse('receipt',args=[sale.pk])).status_code,200)
    def test_replay_is_idempotent_and_changed_replay_rejected(self):
        data=self.payload();self.post_sale(data);self.post_sale(data)
        self.assertEqual(Sale.objects.count(),1);self.assertEqual(Movement.objects.count(),1)
        data['discount']='1';self.assertEqual(self.post_sale(data).status_code,400)
    def test_insufficient_stock_rolls_back_entire_sale(self):
        second=Product.objects.create(business=self.business,name='Empty',sku='EMPTY',price=1)
        Stock.objects.create(product=second,warehouse=self.warehouse,quantity=0)
        data=self.payload(items=[{'id':self.product.pk,'quantity':1},{'id':second.pk,'quantity':1}])
        self.assertEqual(self.post_sale(data).status_code,400)
        self.assertFalse(Sale.objects.exists());self.assertFalse(Movement.objects.exists())
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,10)
    def test_tenant_product_warehouse_and_customer_boundaries(self):
        contact=Contact.objects.create(business=self.foreign,name='Private',kind='customer')
        for override in [{'warehouse':self.fw.pk},{'items':[{'id':self.fp.pk,'quantity':1}]},{'customer':contact.pk}]:
            self.assertEqual(self.post_sale(self.payload(**override)).status_code,400)
        self.assertFalse(Sale.objects.exists())
        self.assertEqual(self.client.get(reverse('product_edit',args=[self.fp.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('switch'),{'business':self.foreign.pk}).status_code,404)
        self.assertNotContains(self.client.get(reverse('products')),'Other product')
    def test_receipt_is_tenant_private(self):
        self.post_sale(self.payload());sale=Sale.objects.get()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('receipt',args=[sale.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('sale_void',args=[sale.pk]),{'reason':'Return'}).status_code,302)
        sale.refresh_from_db();self.assertFalse(sale.voided)
    def test_cashier_permissions(self):
        self.client.force_login(self.cashier)
        for name in ['settings','product_new','inventory_edit','reports','purchases','team_add','warehouse_add']:
            self.assertEqual(self.client.get(reverse(name)).status_code,403,name)
        self.assertEqual(self.post_sale(self.payload()).status_code,200)
        sale=Sale.objects.get()
        self.assertEqual(self.client.post(reverse('sale_void',args=[sale.pk]),{'reason':'Return'}).status_code,403)
    def test_csrf_and_post_only(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.post(reverse('sale_create'),json.dumps(self.payload()),content_type='application/json').status_code,403)
        self.assertEqual(self.client.get(reverse('sale_create')).status_code,405)
        self.assertEqual(self.client.get(reverse('sample')).status_code,405)
    def test_invalid_amounts_and_quantities(self):
        overrides=[{'discount':'NaN'},{'tax_rate':'101'},{'discount':'26'},{'tendered':'0'},{'discount':'-1'},{'tax_rate':'0.001'},
            {'items':[{'id':self.product.pk,'quantity':-1}]},{'items':[{'id':self.product.pk,'quantity':1.5}]},{'items':[{'id':self.product.pk,'quantity':True}]},
            {'items':[{'id':self.product.pk,'quantity':1},{'id':self.product.pk,'quantity':1}]},{'items':[]},{'method':'anything'}]
        for data in overrides:self.assertEqual(self.post_sale(self.payload(**data)).status_code,400,str(data))
        self.assertFalse(Sale.objects.exists())
    def test_electronic_payment_requires_reference(self):
        self.assertEqual(self.post_sale(self.payload(method='kpay',reference='')).status_code,400)
        self.assertEqual(self.post_sale(self.payload(method='kpay',reference='BANK-123',tendered='')).status_code,200)
        sale=Sale.objects.get();self.assertEqual(sale.tendered,sale.total)
    def test_price_change_requires_reload(self):
        self.assertEqual(self.post_sale(self.payload(items=[{'id':self.product.pk,'quantity':1,'expected_price':'1.00'}])).status_code,400)
    def test_full_return_once_restores_stock(self):
        self.post_sale(self.payload());sale=Sale.objects.get()
        for _ in range(2):self.client.post(reverse('sale_void',args=[sale.pk]),{'reason':'Returned goods'})
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,10)
        self.assertEqual(Movement.objects.filter(kind='return').count(),1)
        sale.refresh_from_db();self.assertTrue(sale.voided)
        response=self.client.get(reverse('reports'));self.assertEqual(response.context['count'],0)
    def inventory_data(self,**changes):
        response=self.client.get(reverse('inventory_edit'));key=response.context['form'].initial['request_key']
        data={'product':self.product.pk,'warehouse':self.warehouse.pk,'quantity':3,'action':'receive','unit_cost':'4.25','reference':'PO-1','request_key':key}
        data.update(changes);return data
    def test_purchase_receive_and_duplicate_submission(self):
        data=self.inventory_data();self.client.post(reverse('inventory_edit'),data);self.client.post(reverse('inventory_edit'),data)
        self.assertEqual(Purchase.objects.count(),1);self.assertEqual(InventoryOperation.objects.count(),1)
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,13)
    def test_transfer_atomic_and_tenant_scoped(self):
        target=Warehouse.objects.create(business=self.business,name='Back room')
        data=self.inventory_data(action='transfer',destination=target.pk,quantity=4)
        self.client.post(reverse('inventory_edit'),data)
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,6)
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=target).quantity,4)
        self.client.post(reverse('inventory_edit'),self.inventory_data(action='transfer',destination=self.fw.pk))
        self.assertEqual(Movement.objects.count(),2)
    def test_adjustment_cannot_go_negative(self):
        self.client.post(reverse('inventory_edit'),self.inventory_data(action='remove',quantity=99))
        self.assertEqual(Stock.objects.get(product=self.product,warehouse=self.warehouse).quantity,10)
        self.assertFalse(InventoryOperation.objects.exists())
    def test_receipt_snapshots_and_csv_formula_escaping(self):
        customer=Contact.objects.create(business=self.business,kind='customer',name='=2+2')
        self.post_sale(self.payload(customer=customer.pk))
        sale=Sale.objects.get();self.product.name='Changed';self.product.save();self.business.name='Renamed';self.business.save()
        self.assertEqual(sale.business_name,'My shop');self.assertEqual(sale.lines.get().name,'Notebook')
        response=self.client.get(reverse('reports'),{'export':'csv'})
        self.assertIn("'=2+2",response.content.decode())
    def test_inactive_business_not_accessible(self):
        self.business.active=False;self.business.save()
        self.assertRedirects(self.client.get(reverse('dashboard')),reverse('new_business'))
    def test_cashier_membership_revocation(self):
        member=Membership.objects.get(user=self.cashier)
        self.client.post(reverse('team_remove',args=[member.pk]));self.client.force_login(self.cashier)
        self.assertRedirects(self.client.get(reverse('dashboard')),reverse('new_business'))
    def test_sample_does_not_overwrite(self):
        self.client.post(reverse('sample'))
        self.assertEqual(Product.objects.filter(business=self.business).count(),1)
