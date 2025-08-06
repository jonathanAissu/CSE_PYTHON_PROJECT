from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import UserProfile, Stock, Feedstock, Farmer, ChickRequest


# Custom User Admin
@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role_display', 'phone', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_salesagent', 'is_manager', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('YOUNG4CHICKS Roles', {
            'fields': ('is_salesagent', 'is_manager', 'phone', 'title'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('YOUNG4CHICKS Roles', {
            'fields': ('is_salesagent', 'is_manager', 'phone', 'title'),
        }),
    )
    
    def role_display(self, obj):
        roles = []
        if obj.is_superuser:
            roles.append('<span style="color: red;">Superuser</span>')
        if obj.is_manager:
            roles.append('<span style="color: blue;">Manager</span>')
        if obj.is_salesagent:
            roles.append('<span style="color: green;">Sales Agent</span>')
        if obj.is_staff and not any([obj.is_superuser, obj.is_manager, obj.is_salesagent]):
            roles.append('<span style="color: orange;">Staff</span>')
        return format_html(' | '.join(roles)) if roles else 'Regular User'
    
    role_display.short_description = 'Role'  # type: ignore


# Stock Admin
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('stock_name', 'chick_type', 'chick_breed', 'quantity', 'chicks_period', 'price', 'manager_name', 'date_added')
    list_filter = ('chick_type', 'chick_breed', 'date_added', 'manager_name')
    search_fields = ('stock_name', 'manager_name')
    ordering = ('-date_added',)
    readonly_fields = ('date_added',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('stock_name', 'quantity', 'chicks_period', 'manager_name')
        }),
        ('Chick Details', {
            'fields': ('chick_type', 'chick_breed', 'price')
        }),
        ('Timestamps', {
            'fields': ('date_added',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


# Feedstock Admin
@admin.register(Feedstock)
class FeedstockAdmin(admin.ModelAdmin):
    list_display = ('name_of_feeds', 'brand_of_feeds', 'quantity_of_feeds', 'type_of_feeds', 'selling_price', 'supplier_name', 'date')
    list_filter = ('type_of_feeds', 'brand_of_feeds', 'date', 'supplier_name')
    search_fields = ('name_of_feeds', 'brand_of_feeds', 'supplier_name')
    ordering = ('-date',)
    readonly_fields = ('date',)
    
    fieldsets = (
        ('Feed Information', {
            'fields': ('name_of_feeds', 'type_of_feeds', 'brand_of_feeds', 'quantity_of_feeds')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'unit_cost', 'selling_price', 'buying_price')
        }),
        ('Supplier Details', {
            'fields': ('supplier_name', 'supplier_contact')
        }),
        ('Timestamps', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )


# Farmer Admin
@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('farmer_name', 'farmer_gender', 'farmer_age', 'type_of_farmer', 'phone_number', 'status_display', 'date_registered', 'nin_display')
    list_filter = ('farmer_gender', 'type_of_farmer', 'farmer_age', 'status', 'date_registered')
    search_fields = ('farmer_name', 'nin', 'phone_number', 'recommender_name')
    ordering = ('-date_registered',)
    readonly_fields = ('date_registered',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('farmer_name', 'farmer_gender', 'farmer_age', 'phone_number')
        }),
        ('Identification', {
            'fields': ('nin', 'type_of_farmer')
        }),
        ('Recommender Details', {
            'fields': ('recommender_name', 'recommender_nin'),
            'classes': ('collapse',)
        }),
        ('Status & Registration', {
            'fields': ('status', 'date_registered'),
        }),
    )
    
    actions = ['approve_farmers', 'reject_farmers', 'mark_pending']
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    status_display.short_description = 'Status'  # type: ignore
    
    def approve_farmers(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} farmers were approved.')
    
    approve_farmers.short_description = "Approve selected farmers"  # type: ignore
    
    def reject_farmers(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} farmers were rejected.')
    
    reject_farmers.short_description = "Reject selected farmers"  # type: ignore
    
    def mark_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} farmers were marked as pending.')
    
    mark_pending.short_description = "Mark as pending review"  # type: ignore
    
    def nin_display(self, obj):
        if obj.nin:
            return f"{obj.nin[:4]}****{obj.nin[-4:]}"
        return "N/A"
    
    nin_display.short_description = 'NIN (Masked)'  # type: ignore


# ChickRequest Admin
@admin.register(ChickRequest)
class ChickRequestAdmin(admin.ModelAdmin):
    list_display = ('farmer_name', 'chicks_type', 'chicks_breed', 'quantity', 'status_display', 'sales_authorized', 'feeds_needed', 'delivered', 'date_time')
    list_filter = ('status', 'chicks_type', 'chicks_breed', 'feeds_needed', 'delivered', 'sales_authorized', 'date_time')
    search_fields = ('farmer_name__farmer_name', 'chicks_type', 'sales_authorized_by__username')
    ordering = ('-date_time',)
    readonly_fields = ('date_time', 'sales_authorized_date')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('farmer_name', 'chicks_type', 'chicks_breed', 'quantity', 'chicks_period')
        }),
        ('Request Status', {
            'fields': ('status', 'feeds_needed', 'delivered')
        }),
        ('Sales Authorization', {
            'fields': ('sales_authorized', 'sales_authorized_by', 'sales_authorized_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_time',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'sold': 'blue'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    status_display.short_description = 'Status'  # type: ignore
    
    actions = ['approve_requests', 'reject_requests', 'mark_delivered', 'authorize_sales']
    
    def approve_requests(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} requests were approved.')
    
    approve_requests.short_description = "Approve selected requests"  # type: ignore
    
    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} requests were rejected.')
    
    reject_requests.short_description = "Reject selected requests"  # type: ignore
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(delivered='Y')
        self.message_user(request, f'{updated} requests were marked as delivered.')
    
    mark_delivered.short_description = "Mark as delivered"  # type: ignore
    
    def authorize_sales(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='approved').update(
            status='sold',
            sales_authorized=True,
            sales_authorized_by=request.user,
            sales_authorized_date=timezone.now()
        )
        self.message_user(request, f'{updated} sales were authorized.')
    
    authorize_sales.short_description = "Authorize sales for approved requests"  # type: ignore


# Customize Admin Site Header and Title
admin.site.site_header = "YOUNG4CHICKS Administration"
admin.site.site_title = "YOUNG4CHICKS Admin"
admin.site.index_title = "Urban Brooder Management System"
