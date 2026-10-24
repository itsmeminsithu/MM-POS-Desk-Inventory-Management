from django.contrib import admin
from .models import Business,Membership,Warehouse,Product,Stock,Contact,Sale,SaleLine,Movement,Purchase,InventoryOperation
class PlatformAdmin(admin.ModelAdmin):
    def has_module_permission(self,r):return r.user.is_superuser
    def has_view_permission(self,r,obj=None):return r.user.is_superuser
    def has_add_permission(self,r):return False
    def has_change_permission(self,r,obj=None):return False
    def has_delete_permission(self,r,obj=None):return False
@admin.register(Business)
class BusinessAdmin(PlatformAdmin):
    list_display=('name','currency','active','created')
    readonly_fields=('name','slug','currency','address','phone','receipt_note','created')
    def has_change_permission(self,r,obj=None):return r.user.is_superuser
for model in [Membership,Warehouse,Product,Stock,Contact,Sale,SaleLine,Movement,Purchase,InventoryOperation]:admin.site.register(model,PlatformAdmin)
