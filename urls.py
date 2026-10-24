from django.urls import path
from . import views as v
urlpatterns=[
 path('',v.home,name='home'),path('register/',v.register,name='register'),path('business/new/',v.new_business,name='new_business'),path('business/switch/',v.switch,name='switch'),
 path('dashboard/',v.dashboard,name='dashboard'),path('products/',v.products,name='products'),path('products/new/',v.product_edit,name='product_new'),path('products/<int:pk>/',v.product_edit,name='product_edit'),
 path('inventory/',v.inventory,name='inventory'),path('inventory/move/',v.inventory_edit,name='inventory_edit'),path('inventory/warehouse/',v.warehouse_add,name='warehouse_add'),path('purchases/',v.purchases,name='purchases'),
 path('contacts/<str:kind>/',v.contacts,name='contacts'),path('contacts/<str:kind>/new/',v.contact_edit,name='contact_new'),path('contacts/<str:kind>/<int:pk>/',v.contact_edit,name='contact_edit'),
 path('pos/',v.pos,name='pos'),path('api/checkout/',v.sale_create,name='sale_create'),path('sales/',v.sales,name='sales'),path('sales/<uuid:pk>/',v.receipt,name='receipt'),path('sales/<uuid:pk>/return/',v.sale_void,name='sale_void'),
 path('reports/',v.reports,name='reports'),path('settings/',v.settings_view,name='settings'),path('settings/sample/',v.sample,name='sample'),path('settings/team/new/',v.team_add,name='team_add'),path('settings/team/<int:pk>/remove/',v.team_remove,name='team_remove')]
