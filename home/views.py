from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from decimal import Decimal
from .models import UserProfile, Stock, Feedstock, Farmer, ChickRequest
from .forms import UserCreation, StockForm, FeedstockForm, FarmerForm, ChickRequestForm
from django.contrib.auth.forms import AuthenticationForm
from typing import Optional
import json

# Authentication Views
def index(request: HttpRequest) -> HttpResponse:
    """Home/Index page view"""
    if request.user.is_authenticated:
        # Redirect authenticated users to their appropriate dashboard
        user_profile: UserProfile = request.user  # type: ignore
        if hasattr(user_profile, 'is_manager') and user_profile.is_manager:
            return redirect('manager_dashboard')
        elif hasattr(user_profile, 'is_salesagent') and user_profile.is_salesagent:
            return redirect('sales_dashboard')
        else:
            return redirect('/admin')
    
    # Show index page for non-authenticated users
    return render(request, 'index.html', {
        'title': 'YOUNG4CHICKS',
        'description': 'Empowering Young Farmers'
    })

def signup(request: HttpRequest) -> HttpResponse:
    """User registration view"""
    if request.method == "POST":
        form_data = UserCreation(request.POST)
        # Set role values based on form submission
        is_manager = request.POST.get('is_manager') == 'True'
        is_salesagent = request.POST.get('is_salesagent') == 'True'
        
        # Update the form data with role values
        form_data.data = form_data.data.copy()  # Make the QueryDict mutable
        form_data.data['is_manager'] = is_manager
        form_data.data['is_salesagent'] = is_salesagent
        
        if form_data.is_valid():
            user = form_data.save()
            username = form_data.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('/login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form_data = UserCreation()
    return render(request, "signup.html", {"form_data": form_data})

def loginpage(request: HttpRequest) -> HttpResponse:
    """User login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Cast to UserProfile to access custom attributes
            user_profile: UserProfile = user  # type: ignore
            if hasattr(user_profile, 'is_salesagent') and user_profile.is_salesagent:
                login(request, user)  
                return redirect('sales_dashboard')
            elif hasattr(user_profile, 'is_manager') and user_profile.is_manager:
                login(request, user)
                return redirect('manager_dashboard')
            else:
                login(request, user)
                return redirect('/admin')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
        
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'title': 'Login'})

def logout_view(request: HttpRequest) -> HttpResponse:
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('/login')

# Dashboard Views
@login_required
def manager_dashboard(request: HttpRequest) -> HttpResponse:
    """Manager dashboard with comprehensive statistics"""
    # Get statistics
    total_stock = Stock.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_feedstock = Feedstock.objects.aggregate(total=Sum('quantity_of_feeds'))['total'] or 0
    total_farmers = Farmer.objects.count()
    pending_requests = ChickRequest.objects.filter(status='pending').count()
    approved_requests = ChickRequest.objects.filter(status='approved').count()
    
    # Recent stock additions
    recent_stocks = Stock.objects.order_by('-date_added')[:5]
    
    # Recent chick requests
    recent_requests = ChickRequest.objects.order_by('-date_time')[:5]
    
    # Stock by type
    stock_by_type = Stock.objects.values('chick_type').annotate(
        total_quantity=Sum('quantity')
    ).order_by('chick_type')
    
    context = {
        'total_stock': total_stock,
        'total_feedstock': total_feedstock,
        'total_farmers': total_farmers,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'recent_stocks': recent_stocks,
        'recent_requests': recent_requests,
        'stock_by_type': stock_by_type,
        'stock_count': total_stock,
        'feedstock_count': total_feedstock,
        'farmer_count': total_farmers,
    }
    return render(request, 'managerdashbord.html', context)

@login_required
def sales_dashboard(request: HttpRequest) -> HttpResponse:
    """Sales agent dashboard"""
    # Get statistics relevant to sales
    total_farmers = Farmer.objects.count()
    approved_farmers = Farmer.objects.filter(status='approved').count()
    pending_requests = ChickRequest.objects.filter(status='pending').count()
    approved_requests = ChickRequest.objects.filter(status='approved').count()
    sold_requests = ChickRequest.objects.filter(status='sold').count()
    total_requests = ChickRequest.objects.count()
    
    # Sales authorized by this user
    my_sales = 0
    if request.user.is_authenticated and getattr(request.user, 'is_salesagent', False):
        my_sales = ChickRequest.objects.filter(
            sales_authorized_by=request.user
        ).count()
    
    # Recent farmers
    recent_farmers = Farmer.objects.order_by('-date_registered')[:5]
    
    # Recent requests
    recent_requests = ChickRequest.objects.order_by('-date_time')[:5]
    
    context = {
        'total_farmers': total_farmers,
        'approved_farmers': approved_farmers,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'sold_requests': sold_requests,
        'total_requests': total_requests,
        'my_sales': my_sales,
        'recent_farmers': recent_farmers,
        'recent_requests': recent_requests,
    }
    return render(request, 'salesdashbord.html', context)

# Stock Management Views
@login_required
def stock_list(request):
    """List all stocks with search and pagination"""
    stocks = Stock.objects.all().order_by('-date_added')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        stocks = stocks.filter(
            Q(stock_name__icontains=search_query) |
            Q(chick_type__icontains=search_query) |
            Q(chick_breed__icontains=search_query) |
            Q(manager_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stock/stock_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

@login_required
def stock_create(request):
    """Create new stock entry"""
    if request.method == 'POST':
        stock_name = request.POST.get('stock_name')
        quantity = request.POST.get('quantity')
        chick_type = request.POST.get('chick_type')
        chick_breed = request.POST.get('chick_breed')
        price = request.POST.get('price')
        manager_name = request.POST.get('manager_name')
        chicks_period = request.POST.get('chicks_period')
        
        try:
            stock = Stock.objects.create(
                stock_name=stock_name,
                quantity=int(quantity),
                chick_type=chick_type,
                chick_breed=chick_breed,
                price=int(price),
                manager_name=manager_name,
                chicks_period=int(chicks_period)
            )
            messages.success(request, f'Stock "{stock_name}" added successfully!')
            return redirect('stock_list')
        except Exception as e:
            messages.error(request, f'Error adding stock: {str(e)}')
    
    return render(request, 'stock/stock_form.html', {
        'title': 'Add New Stock',
        'chick_types': Stock.CHICK_TYPE_CHOICES,
        'chick_breeds': Stock.CHICK_BREED_CHOICES
    })

@login_required
def stock_detail(request, pk):
    """Stock detail view"""
    stock = get_object_or_404(Stock, pk=pk)
    
    # Calculate total value (quantity * price per chick)
    total_value = stock.quantity * stock.price
    
    return render(request, 'stock/stock_detail.html', {
        'stock': stock,
        'total_value': total_value
    })

@login_required
def stock_update(request, pk):
    """Update stock entry"""
    stock = get_object_or_404(Stock, pk=pk)
    
    if request.method == 'POST':
        stock.stock_name = request.POST.get('stock_name')
        stock.quantity = int(request.POST.get('quantity'))
        stock.chick_type = request.POST.get('chick_type')
        stock.chick_breed = request.POST.get('chick_breed')
        stock.manager_name = request.POST.get('manager_name')
        stock.chicks_period = int(request.POST.get('chicks_period'))
        
        try:
            stock.save()
            messages.success(request, f'Stock "{stock.stock_name}" updated successfully!')
            return redirect('stock_detail', pk=stock.pk)
        except Exception as e:
            messages.error(request, f'Error updating stock: {str(e)}')
    
    return render(request, 'stock/stock_form.html', {
        'stock': stock,
        'title': 'Update Stock',
        'chick_types': Stock.CHICK_TYPE_CHOICES,
        'chick_breeds': Stock.CHICK_BREED_CHOICES
    })

@login_required
def stock_delete(request, pk):
    """Delete stock entry"""
    stock = get_object_or_404(Stock, pk=pk)
    
    if request.method == 'POST':
        stock_name = stock.stock_name
        stock.delete()
        messages.success(request, f'Stock "{stock_name}" deleted successfully!')
        return redirect('stock_list')
    
    return render(request, 'stock/confirm_delete.html', {'stock': stock})

# Feedstock Management Views
@login_required
def feedstock_list(request):
    """List all feedstocks"""
    feedstocks = Feedstock.objects.all().order_by('-date')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        feedstocks = feedstocks.filter(
            Q(name_of_feeds__icontains=search_query) |
            Q(brand_of_feeds__icontains=search_query) |
            Q(type_of_feeds__icontains=search_query) |
            Q(supplier_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(feedstocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'feedstock/feedstock_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

@login_required
def feedstock_create(request):
    """Create new feedstock entry"""
    if request.method == 'POST':
        try:
            feedstock = Feedstock.objects.create(
                name_of_feeds=request.POST.get('name_of_feeds'),
                quantity_of_feeds=int(request.POST.get('quantity_of_feeds')),
                unit_price=Decimal(request.POST.get('unit_price')),
                unit_cost=Decimal(request.POST.get('unit_cost')),
                type_of_feeds=request.POST.get('type_of_feeds'),
                brand_of_feeds=request.POST.get('brand_of_feeds'),
                supplier_name=request.POST.get('supplier_name'),
                supplier_contact=request.POST.get('supplier_contact'),
                selling_price=Decimal(request.POST.get('selling_price')),
                buying_price=Decimal(request.POST.get('buying_price'))
            )
            messages.success(request, f'Feedstock "{feedstock.name_of_feeds}" added successfully!')
            return redirect('feedstock_list')
        except Exception as e:
            messages.error(request, f'Error adding feedstock: {str(e)}')
    
    return render(request, 'feedstock/feedstock_form.html', {'title': 'Add New Feedstock'})

@login_required
def feedstock_detail(request, pk):
    """Feedstock detail view"""
    feedstock = get_object_or_404(Feedstock, pk=pk)
    
    # Calculate total value and profit
    total_cost = feedstock.quantity_of_feeds * float(feedstock.buying_price)
    total_selling_value = feedstock.quantity_of_feeds * float(feedstock.selling_price)
    potential_profit = total_selling_value - total_cost
    
    return render(request, 'feedstock/feedstock_detail.html', {
        'feedstock': feedstock,
        'total_cost': total_cost,
        'total_selling_value': total_selling_value,
        'potential_profit': potential_profit
    })

@login_required
def feedstock_update(request, pk):
    """Update feedstock entry"""
    feedstock = get_object_or_404(Feedstock, pk=pk)
    
    if request.method == 'POST':
        try:
            feedstock.name_of_feeds = request.POST.get('name_of_feeds')
            feedstock.quantity_of_feeds = int(request.POST.get('quantity_of_feeds'))
            feedstock.unit_price = Decimal(request.POST.get('unit_price'))
            feedstock.unit_cost = Decimal(request.POST.get('unit_cost'))
            feedstock.type_of_feeds = request.POST.get('type_of_feeds')
            feedstock.brand_of_feeds = request.POST.get('brand_of_feeds')
            feedstock.supplier_name = request.POST.get('supplier_name')
            feedstock.supplier_contact = request.POST.get('supplier_contact')
            feedstock.selling_price = Decimal(request.POST.get('selling_price'))
            feedstock.buying_price = Decimal(request.POST.get('buying_price'))
            
            feedstock.save()
            messages.success(request, f'Feedstock "{feedstock.name_of_feeds}" updated successfully!')
            return redirect('feedstock_detail', pk=feedstock.pk)
        except Exception as e:
            messages.error(request, f'Error updating feedstock: {str(e)}')
    
    return render(request, 'feedstock/feedstock_form.html', {
        'feedstock': feedstock,
        'title': 'Update Feedstock'
    })

@login_required
def feedstock_delete(request, pk):
    """Delete feedstock entry"""
    feedstock = get_object_or_404(Feedstock, pk=pk)
    
    if request.method == 'POST':
        feedstock_name = feedstock.name_of_feeds
        feedstock.delete()
        messages.success(request, f'Feedstock "{feedstock_name}" deleted successfully!')
        return redirect('feedstock_list')
    
    return render(request, 'feedstock/feedstock_confirm_delete.html', {'feedstock': feedstock})

# Farmer Management Views
@login_required
def farmer_list(request):
    """List all farmers"""
    farmers = Farmer.objects.all().order_by('farmer_name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        farmers = farmers.filter(
            Q(farmer_name__icontains=search_query) |
            Q(nin__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(recommender_name__icontains=search_query)
        )
    
    # Filter by type
    farmer_type = request.GET.get('type')
    if farmer_type:
        farmers = farmers.filter(type_of_farmer=farmer_type)
    
    # Pagination
    paginator = Paginator(farmers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'farmer/farmer_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'farmer_type': farmer_type,
        'farmer_types': Farmer.FARMER_TYPE_CHOICES
    })

@login_required
def farmer_create(request):
    """Create new farmer (Sales Agent only)"""
    # Only sales agents can register farmers
    if not getattr(request.user, 'is_salesagent', False):
        messages.error(request, 'Only Sales Agents can register farmers.')
        return redirect('farmer_list')
    
    if request.method == 'POST':
        try:
            farmer = Farmer.objects.create(
                farmer_name=request.POST.get('farmer_name'),
                farmer_gender=request.POST.get('farmer_gender'),
                nin=request.POST.get('nin'),
                recommender_name=request.POST.get('recommender_name'),
                recommender_nin=request.POST.get('recommender_nin'),
                phone_number=request.POST.get('phone_number'),
                farmer_age=int(request.POST.get('farmer_age')),
                type_of_farmer=request.POST.get('type_of_farmer'),
                status='pending'  # Ensure status is pending
            )
            messages.success(request, f'Farmer "{farmer.farmer_name}" registered successfully and is pending approval!')
            return redirect('farmer_list')
        except Exception as e:
            messages.error(request, f'Error registering farmer: {str(e)}')
    
    return render(request, 'farmer/farmer_form.html', {
        'title': 'Register New Farmer',
        'gender_choices': Farmer.GENDER_CHOICES,
        'farmer_types': Farmer.FARMER_TYPE_CHOICES
    })

@login_required
def farmer_detail(request, pk):
    """Farmer detail view with their requests"""
    farmer = get_object_or_404(Farmer, pk=pk)
    requests = ChickRequest.objects.filter(farmer_name=farmer).order_by('-date_time')
    
    return render(request, 'farmer/farmer_detail.html', {
        'farmer': farmer,
        'requests': requests
    })

@login_required
def approve_farmer(request, pk):
    """Approve a farmer (Manager only)"""
    if not getattr(request.user, 'is_manager', False):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            farmer = get_object_or_404(Farmer, pk=pk)
            farmer.status = 'approved'
            farmer.save()
            messages.success(request, f'Farmer "{farmer.farmer_name}" approved successfully!')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def reject_farmer(request, pk):
    """Reject a farmer (Manager only)"""
    if not getattr(request.user, 'is_manager', False):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            farmer = get_object_or_404(Farmer, pk=pk)
            farmer.status = 'rejected'
            farmer.save()
            messages.success(request, f'Farmer "{farmer.farmer_name}" rejected.')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def authorize_sale(request, pk):
    """Authorize sale of approved request (Sales Agent only)"""
    if not getattr(request.user, 'is_salesagent', False):
        return JsonResponse({'success': False, 'error': 'Unauthorized - Only Sales Agents can authorize sales'}, status=403)
    
    if request.method == 'POST':
        try:
            chick_request = get_object_or_404(ChickRequest, pk=pk)
            
            # Only approve requests that are in 'approved' status
            if chick_request.status != 'approved':
                return JsonResponse({'success': False, 'error': 'Can only authorize sales for approved requests'})
            
            # Update request to sold status with sales authorization
            chick_request.status = 'sold'
            chick_request.sales_authorized = True
            chick_request.sales_authorized_by = request.user
            chick_request.sales_authorized_date = timezone.now()
            chick_request.save()
            
            messages.success(request, f'Sale authorized for request #{chick_request.pk} - {chick_request.farmer_name.farmer_name}')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Chick Request Management Views
@login_required
def request_list(request):
    """List all chick requests"""
    requests = ChickRequest.objects.all().order_by('-date_time')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        requests = requests.filter(
            Q(farmer_name__farmer_name__icontains=search_query) |
            Q(chicks_type__icontains=search_query) |
            Q(chicks_breed__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'request/request_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status': status,
        'status_choices': ChickRequest.STATUS_CHOICES
    })

@login_required
def request_create(request):
    """Create new chick request (Only for approved farmers)"""
    if request.method == 'POST':
        try:
            farmer = get_object_or_404(Farmer, pk=request.POST.get('farmer_id'))
            
            # Ensure farmer is approved before creating request
            if farmer.status != 'approved':
                messages.error(request, f'Cannot create request: Farmer "{farmer.farmer_name}" is not approved yet.')
                return redirect('request_create')
            
            chick_request = ChickRequest.objects.create(
                farmer_name=farmer,
                chicks_type=request.POST.get('chicks_type'),
                chicks_breed=request.POST.get('chicks_breed'),
                quantity=int(request.POST.get('quantity')),
                feeds_needed=request.POST.get('feeds_needed'),
                chicks_period=int(request.POST.get('chicks_period'))
            )
            messages.success(request, f'Chick request for {farmer.farmer_name} created successfully!')
            return redirect('request_list')
        except Exception as e:
            messages.error(request, f'Error creating request: {str(e)}')
    
    # Only show approved farmers
    farmers = Farmer.objects.filter(status='approved').order_by('farmer_name')
    
    # Check if there are any approved farmers
    if not farmers.exists():
        messages.warning(request, 'No approved farmers available. Please wait for farmers to be approved by a manager.')
        return redirect('farmer_list')
    
    return render(request, 'request/request_form.html', {
        'title': 'Create New Request',
        'farmers': farmers,
        'chick_types': ChickRequest.CHICK_TYPE_CHOICES,
        'chick_breeds': ChickRequest.CHICK_BREED_CHOICES,
        'yes_no_choices': ChickRequest.YES_NO_CHOICES
    })

@login_required
def request_update_status(request, pk):
    """Update request status (approve/reject)"""
    chick_request = get_object_or_404(ChickRequest, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['approved', 'rejected']:
            chick_request.status = new_status
            chick_request.save()
            messages.success(request, f'Request status updated to {new_status}!')
        else:
            messages.error(request, 'Invalid status!')
    
    return redirect('request_list')

@login_required
def request_detail(request, pk):
    """Request detail view"""
    chick_request = get_object_or_404(ChickRequest, pk=pk)
    
    # Calculate total cost (price per chick * quantity)
    price_per_chick = 1650  # UGX per chick
    total_cost = chick_request.quantity * price_per_chick
    
    return render(request, 'request/request_detail.html', {
        'request': chick_request,
        'price_per_chick': price_per_chick,
        'total_cost': total_cost
    })

# API Views for AJAX requests
@login_required
def get_farmer_data(request: HttpRequest, farmer_id: int) -> JsonResponse:
    """Get farmer data for AJAX requests"""
    try:
        farmer = get_object_or_404(Farmer, pk=farmer_id)
        data = {
            'farmer_name': farmer.farmer_name,
            'phone_number': farmer.phone_number,
            'type_of_farmer': farmer.type_of_farmer,
            'farmer_age': farmer.farmer_age
        }
        return JsonResponse(data)
    except Exception:
        return JsonResponse({'error': 'Farmer not found'}, status=404)

def check_farmer_status(request: HttpRequest) -> JsonResponse:
    """Check farmer registration status by NIN and phone number"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nin = data.get('nin', '').strip()
            phone = data.get('phone', '').strip()
            
            if not nin or not phone:
                return JsonResponse({
                    'success': False, 
                    'error': 'Both NIN and phone number are required'
                }, status=400)
            
            # Search for farmer by NIN and phone
            try:
                farmer = Farmer.objects.get(nin=nin, phone_number=phone)
                
                # Get farmer's request count
                total_requests = ChickRequest.objects.filter(farmer_name=farmer).count()
                approved_requests = ChickRequest.objects.filter(farmer_name=farmer, status='approved').count()
                pending_requests = ChickRequest.objects.filter(farmer_name=farmer, status='pending').count()
                sold_requests = ChickRequest.objects.filter(farmer_name=farmer, status='sold').count()
                
                # Calculate status badge color
                status_colors = {
                    'pending': 'warning',
                    'approved': 'success', 
                    'rejected': 'danger'
                }
                
                # Get display values manually
                gender_display = 'Male' if farmer.farmer_gender == 'M' else 'Female'
                type_display = 'Starter' if farmer.type_of_farmer == 'starter' else 'Returning'
                status_display = farmer.status.title()
                
                return JsonResponse({
                    'success': True,
                    'farmer': {
                        'name': farmer.farmer_name,
                        'nin': farmer.nin,
                        'phone': farmer.phone_number,
                        'age': farmer.farmer_age,
                        'gender': gender_display,
                        'type': type_display,
                        'status': farmer.status,
                        'status_display': status_display,
                        'status_color': status_colors.get(farmer.status, 'secondary'),
                        'date_registered': farmer.date_registered.strftime('%B %d, %Y'),
                        'recommender_name': farmer.recommender_name,
                        'total_requests': total_requests,
                        'approved_requests': approved_requests,
                        'pending_requests': pending_requests,
                        'sold_requests': sold_requests
                    }
                })
                
            except Farmer.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No farmer found with the provided NIN and phone number combination. Please verify your details or contact our office for registration.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid request format'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while checking registration status'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

# Dashboard Statistics API
@login_required
def dashboard_stats_api(request: HttpRequest) -> JsonResponse:
    """API endpoint for dashboard statistics"""
    stats = {
        'total_stock': Stock.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'total_feedstock': Feedstock.objects.aggregate(total=Sum('quantity_of_feeds'))['total'] or 0,
        'total_farmers': Farmer.objects.count(),
        'pending_requests': ChickRequest.objects.filter(status='pending').count(),
        'approved_requests': ChickRequest.objects.filter(status='approved').count(),
        'rejected_requests': ChickRequest.objects.filter(status='rejected').count(),
    }
    return JsonResponse(stats)

@login_required
def sales_report(request: HttpRequest) -> HttpResponse:
    """Generate comprehensive sales report (Manager only)"""
    if not getattr(request.user, 'is_manager', False):
        messages.error(request, 'Only Managers can access sales reports.')
        return redirect('manager_dashboard')
    
    # Get date range from request (default to last 30 days)
    from datetime import datetime, timedelta
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    start_date_str = request.GET.get('start_date')
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    end_date_str = request.GET.get('end_date')
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Ensure start_date is not after end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    # Get all sales within date range
    sales_in_range = ChickRequest.objects.filter(
        status='sold',
        sales_authorized_date__date__gte=start_date,
        sales_authorized_date__date__lte=end_date,
        sales_authorized_date__isnull=False
    )
    
    # Sales by representative
    sales_by_rep = {}
    total_sales_value = 0
    total_chicks_sold = 0
    
    for sale in sales_in_range:
        if not sale.sales_authorized_date:
            continue
            
        rep_name = sale.sales_authorized_by.username if sale.sales_authorized_by else 'Unknown'
        rep_full_name = f"{sale.sales_authorized_by.first_name} {sale.sales_authorized_by.last_name}".strip() if sale.sales_authorized_by and (sale.sales_authorized_by.first_name or sale.sales_authorized_by.last_name) else rep_name
        
        if rep_name not in sales_by_rep:
            sales_by_rep[rep_name] = {
                'rep_name': rep_full_name,
                'username': rep_name,
                'total_sales': 0,
                'total_chicks': 0,
                'total_value': 0,
                'farmers_served': set(),
                'sales_details': []
            }
        
        sale_value = sale.quantity * 1650  # UGX 1650 per chick
        sales_by_rep[rep_name]['total_sales'] += 1
        sales_by_rep[rep_name]['total_chicks'] += sale.quantity
        sales_by_rep[rep_name]['total_value'] += sale_value
        sales_by_rep[rep_name]['farmers_served'].add(sale.farmer_name.farmer_name)
        sales_by_rep[rep_name]['sales_details'].append({
            'date': sale.sales_authorized_date,
            'farmer': sale.farmer_name.farmer_name,
            'chick_type': sale.chicks_type,
            'chick_breed': sale.chicks_breed,
            'quantity': sale.quantity,
            'value': sale_value,
            'request_id': sale.pk
        })
        
        total_sales_value += sale_value
        total_chicks_sold += sale.quantity
    
    # Convert farmers_served sets to counts
    for rep_data in sales_by_rep.values():
        rep_data['unique_farmers'] = len(rep_data['farmers_served'])
        rep_data['farmers_served'] = list(rep_data['farmers_served'])
    
    # Sort sales details by date (most recent first)
    for rep_data in sales_by_rep.values():
        rep_data['sales_details'].sort(key=lambda x: x['date'], reverse=True)
    
    # Overall statistics
    total_sales_count = sales_in_range.count()
    active_sales_reps = len(sales_by_rep)
    
    # Top performing sales rep
    top_rep = None
    if sales_by_rep:
        top_rep = max(sales_by_rep.values(), key=lambda x: x['total_value'])
    
    # Daily sales breakdown
    daily_sales = {}
    for sale in sales_in_range:
        if not sale.sales_authorized_date:
            continue
            
        date_str = sale.sales_authorized_date.strftime('%Y-%m-%d')
        if date_str not in daily_sales:
            daily_sales[date_str] = {
                'date': sale.sales_authorized_date.date(),
                'sales_count': 0,
                'chicks_sold': 0,
                'total_value': 0
            }
        daily_sales[date_str]['sales_count'] += 1
        daily_sales[date_str]['chicks_sold'] += sale.quantity
        daily_sales[date_str]['total_value'] += sale.quantity * 1650
    
    # Convert to sorted list
    daily_sales_list = sorted(daily_sales.values(), key=lambda x: x['date'], reverse=True)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'sales_by_rep': sales_by_rep,
        'total_sales_count': total_sales_count,
        'total_chicks_sold': total_chicks_sold,
        'total_sales_value': total_sales_value,
        'active_sales_reps': active_sales_reps,
        'top_rep': top_rep,
        'daily_sales': daily_sales_list,
        'average_sale_value': total_sales_value / total_sales_count if total_sales_count > 0 else 0,
        'average_chicks_per_sale': total_chicks_sold / total_sales_count if total_sales_count > 0 else 0,
    }
    
    return render(request, 'reports/sales_report.html', context)
