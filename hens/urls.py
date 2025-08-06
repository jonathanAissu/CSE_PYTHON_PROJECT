"""
URL configuration for hens project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # Authentication URLs
    path("", views.index, name="home"),
    path("login/", views.loginpage, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Dashboard URLs
    path("manager/", views.manager_dashboard, name="manager_dashboard"),
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path("salesagent/", views.sales_dashboard, name="sales_dashboard_alt"),
    
    # Stock Management URLs
    path("stock/", views.stock_list, name="stock_list"),
    path("stock/create/", views.stock_create, name="stock_create"),
    path("stock/<int:pk>/", views.stock_detail, name="stock_detail"),
    path("stock/<int:pk>/edit/", views.stock_update, name="stock_update"),
    path("stock/<int:pk>/delete/", views.stock_delete, name="stock_delete"),
    
    # Feedstock Management URLs
    path("feedstock/", views.feedstock_list, name="feedstock_list"),
    path("feedstock/create/", views.feedstock_create, name="feedstock_create"),
    
    # Farmer Management URLs
    path("farmers/", views.farmer_list, name="farmer_list"),
    path("farmers/create/", views.farmer_create, name="farmer_create"),
    path("farmers/<int:pk>/", views.farmer_detail, name="farmer_detail"),
    path("farmer/<int:pk>/approve/", views.approve_farmer, name="approve_farmer"),
    path("farmer/<int:pk>/reject/", views.reject_farmer, name="reject_farmer"),
    
    # Chick Request Management URLs
    path("requests/", views.request_list, name="request_list"),
    path("requests/create/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/update-status/", views.request_update_status, name="request_update_status"),
    path("requests/<int:pk>/authorize-sale/", views.authorize_sale, name="authorize_sale"),
    
    # API URLs
    path("api/farmer/<int:farmer_id>/", views.get_farmer_data, name="api_farmer_data"),
    path("api/dashboard-stats/", views.dashboard_stats_api, name="api_dashboard_stats"),
]