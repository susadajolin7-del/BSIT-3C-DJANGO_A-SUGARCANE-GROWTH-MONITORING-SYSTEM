from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('farmers/', views.farmers_list, name='farmers'),
    path('farmers/add/', views.farmer_add, name='farmer_add'),
    path('farmers/edit/<int:farmer_id>/', views.farmer_edit, name='farmer_edit'),
    path('farmers/delete/<int:farmer_id>/', views.farmer_delete, name='farmer_delete'),
    path('fields/', views.fields_list, name='fields'),
    path('fields/add/', views.field_add, name='field_add'),
path('fields/edit/<int:field_id>/', views.field_edit, name='field_edit'),
path('fields/delete/<int:field_id>/', views.field_delete, name='field_delete'),
    path('crop-cycles/', views.crop_cycles_list, name='crop_cycles'),
    path('crop-cycles/add/', views.crop_cycle_add, name='crop_cycle_add'),
    path('crop-cycles/edit/<int:crop_id>/', views.crop_cycle_edit, name='crop_cycle_edit'),
    path('crop-cycles/delete/<int:crop_id>/', views.crop_cycle_delete, name='crop_cycle_delete'),
    path('growth-records/', views.growth_records_list, name='growth_records'),
    path('growth-records/add/', views.growth_record_add, name='growth_record_add'),
    path('growth-records/edit/<int:record_id>/', views.growth_record_edit, name='growth_record_edit'),
    path('growth-records/delete/<int:record_id>/', views.growth_record_delete, name='growth_record_delete'),
    path('harvest-records/', views.harvest_records_list, name='harvest_records'),
    path('harvest-records/add/', views.harvest_record_add, name='harvest_record_add'),
    path('harvest-records/edit/<int:harvest_id>/', views.harvest_record_edit, name='harvest_record_edit'),
    path('harvest-records/delete/<int:harvest_id>/', views.harvest_record_delete, name='harvest_record_delete'),
    
]