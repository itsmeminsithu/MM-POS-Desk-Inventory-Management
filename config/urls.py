from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path,include
admin.site.site_header='MM POS Desk · Platform administration'
admin.site.site_title='MM POS Desk'
admin.site.index_title='Platform records'
urlpatterns=[path('admin/',admin.site.urls),path('accounts/login/',auth.LoginView.as_view(),name='login'),
 path('accounts/logout/',auth.LogoutView.as_view(),name='logout'),path('',include('retail.urls'))]
