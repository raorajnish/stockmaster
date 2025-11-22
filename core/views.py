from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, F, Value, IntegerField, Case, When
from django.utils import timezone
from .models import (
    Product, StockLevel, InventoryOperation, 
    Warehouse, Location, Category
)

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    # Get filter parameters
    operation_type = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    warehouse_filter = request.GET.get('warehouse', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Calculate KPIs
    
    # Total Products in Stock: Count of active products with stock > 0 across all locations
    products_with_stock = Product.objects.filter(
        is_active=True,
        stock_levels__quantity__gt=0
    ).distinct().count()
    
    # Low Stock Items: Products below min_qty (handle NULL stock as 0)
    low_stock_products = Product.objects.filter(
        is_active=True
    ).annotate(
        total_stock=Case(
            When(stock_levels__quantity__isnull=True, then=Value(0)),
            default=Sum('stock_levels__quantity'),
            output_field=IntegerField()
        )
    ).filter(
        total_stock__lt=F('min_stock'),
        total_stock__gte=0
    ).distinct().count()
    
    # Out of Stock Items: Products with available quantity = 0
    out_of_stock_products = Product.objects.filter(
        is_active=True
    ).annotate(
        total_stock=Case(
            When(stock_levels__quantity__isnull=True, then=Value(0)),
            default=Sum('stock_levels__quantity'),
            output_field=IntegerField()
        )
    ).filter(
        total_stock=0
    ).distinct().count()
    
    # Pending Receipts: RECEIPT operations with status WAITING or READY
    pending_receipts = InventoryOperation.objects.filter(
        type='RECEIPT',
        status__in=['WAITING', 'READY']
    ).count()
    
    # Pending Deliveries: DELIVERY operations with status WAITING or READY
    pending_deliveries = InventoryOperation.objects.filter(
        type='DELIVERY',
        status__in=['WAITING', 'READY']
    ).count()
    
    # Internal Transfers Scheduled: INTERNAL operations not DONE or CANCELED
    internal_transfers = InventoryOperation.objects.filter(
        type='INTERNAL'
    ).exclude(
        status__in=['DONE', 'CANCEL']
    ).count()
    
    # Recent Operations with filters
    operations = InventoryOperation.objects.select_related(
        'source_location__warehouse',
        'destination_location__warehouse',
        'partner'
    ).all().order_by('-created_at')[:50]
    
    # Apply filters
    if operation_type:
        operations = operations.filter(type=operation_type)
    if status_filter:
        operations = operations.filter(status=status_filter)
    if warehouse_filter:
        operations = operations.filter(
            Q(source_location__warehouse_id=warehouse_filter) |
            Q(destination_location__warehouse_id=warehouse_filter)
        )
    if category_filter:
        operations = operations.filter(lines__product__category_id=category_filter).distinct()
    if search_query:
        operations = operations.filter(
            Q(reference__icontains=search_query) |
            Q(lines__product__sku__icontains=search_query) |
            Q(lines__product__name__icontains=search_query)
        ).distinct()
    
    # Prepare operations for template
    recent_operations = []
    for op in operations[:20]:  # Limit to 20 most recent
        recent_operations.append({
            'reference': op.reference or '(no ref)',
            'type': op.get_type_display(),
            'type_code': op.type,
            'source': str(op.source_location) if op.source_location else '-',
            'destination': str(op.destination_location) if op.destination_location else '-',
            'status': op.get_status_display(),
            'status_code': op.status,
            'scheduled_date': op.scheduled_date.strftime('%Y-%m-%d') if op.scheduled_date else '-',
            'last_updated': op.created_at.strftime('%Y-%m-%d %I:%M %p') if op.created_at else '-',
        })
    
    # Get filter options
    warehouses = Warehouse.objects.all()
    categories = Category.objects.all()
    
    context = {
        'total_products': products_with_stock,
        'low_stock_items': low_stock_products,
        'out_of_stock_items': out_of_stock_products,
        'pending_receipts': pending_receipts,
        'pending_deliveries': pending_deliveries,
        'internal_transfers': internal_transfers,
        'recent_operations': recent_operations,
        'warehouses': warehouses,
        'categories': categories,
        'operation_types': InventoryOperation.OPERATION_TYPES,
        'status_types': InventoryOperation.STATUS_TYPES,
        'current_filters': {
            'type': operation_type,
            'status': status_filter,
            'warehouse': warehouse_filter,
            'category': category_filter,
            'search': search_query,
        }
    }
    return render(request, 'core/dashboard.html', context)
