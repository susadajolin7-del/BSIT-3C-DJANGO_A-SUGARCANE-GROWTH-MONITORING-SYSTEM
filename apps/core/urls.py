from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('farmers/', views.farmers_list, name='farmers'),
    path('fields/', views.fields_list, name='fields'),
    path('crop-cycles/', views.crop_cycles_list, name='crop_cycles'),
    path('growth-records/', views.growth_records_list, name='growth_records'),
    path('harvest-records/', views.harvest_records_list, name='harvest_records'),
]

