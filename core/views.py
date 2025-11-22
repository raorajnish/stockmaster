from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, F, Value, IntegerField, Case, When
from django.utils import timezone
from django.contrib import messages
from .models import (
    Product, StockLevel, InventoryOperation, 
    Warehouse, Location, Category, UnitOfMeasure, Partner, OperationLine, StockLedgerEntry
)
from .forms import (
    ProductForm, ReceiptForm, OperationLineForm, PartnerForm, 
    CategoryForm, UnitOfMeasureForm, DeliveryForm, 
    InternalTransferForm, StockAdjustmentForm, WarehouseForm, LocationForm
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
    low_stock_products_count = Product.objects.filter(
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
    
    # Get actual low stock products list with details
    low_stock_products_queryset = Product.objects.filter(
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
    ).select_related('category', 'uom').distinct().order_by('name')
    
    # Prepare low stock products with calculated difference
    low_stock_products = []
    for product in low_stock_products_queryset:
        current_stock = product.total_stock if product.total_stock else 0
        min_stock = product.min_stock if product.min_stock else 0
        difference = min_stock - current_stock
        low_stock_products.append({
            'product': product,
            'current_stock': current_stock,
            'min_stock': min_stock,
            'difference': difference,
        })
    
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
    ).all().order_by('-created_at')
    
    # Apply filters BEFORE slicing
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
    
    # Now slice after all filters are applied
    operations = operations[:50]
    
    # Prepare operations for template
    recent_operations = []
    for op in operations[:20]:  # Limit to 20 most recent for display
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
        'low_stock_items': low_stock_products_count,
        'low_stock_products': low_stock_products,
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

@login_required
def products_list(request):
    """List all products with search and filter capabilities"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    products = Product.objects.select_related('category', 'uom').annotate(
        total_stock=Case(
            When(stock_levels__quantity__isnull=True, then=Value(0)),
            default=Sum('stock_levels__quantity'),
            output_field=IntegerField()
        )
    ).distinct()
    
    # Apply filters
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    if category_filter:
        products = products.filter(category_id=category_filter)
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    
    products = products.order_by('-id')
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'current_filters': {
            'search': search_query,
            'category': category_filter,
            'status': status_filter,
        }
    }
    return render(request, 'core/products_list.html', context)

@login_required
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('core:products_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Create Product'
    }
    return render(request, 'core/product_form.html', context)

@login_required
def product_edit(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('core:products_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Edit Product'
    }
    return render(request, 'core/product_form.html', context)

@login_required
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'category_id': category.id,
                    'category_name': str(category)
                })
            return redirect('core:products_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = CategoryForm()
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('core/category_form_modal.html', {'form': form}, request=request)
        from django.http import JsonResponse
        return JsonResponse({'html': html})
    
    context = {
        'form': form,
        'title': 'Add Category'
    }
    return render(request, 'core/category_form.html', context)

@login_required
def uom_create(request):
    """Create a new unit of measure"""
    if request.method == 'POST':
        form = UnitOfMeasureForm(request.POST)
        if form.is_valid():
            uom = form.save()
            messages.success(request, f'Unit of Measure "{uom.name}" created successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'uom_id': uom.id,
                    'uom_name': str(uom)
                })
            return redirect('core:products_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = UnitOfMeasureForm()
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('core/uom_form_modal.html', {'form': form}, request=request)
        from django.http import JsonResponse
        return JsonResponse({'html': html})
    
    context = {
        'form': form,
        'title': 'Add Unit of Measure'
    }
    return render(request, 'core/uom_form.html', context)

@login_required
def receipts_list(request):
    """List all receipts with search and filter capabilities"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    warehouse_filter = request.GET.get('warehouse', '')
    
    receipts = InventoryOperation.objects.filter(
        type='RECEIPT'
    ).select_related(
        'partner', 'destination_location__warehouse', 'created_by'
    ).prefetch_related('lines__product').order_by('-created_at')
    
    # Apply filters
    if search_query:
        receipts = receipts.filter(
            Q(reference__icontains=search_query) |
            Q(lines__product__sku__icontains=search_query) |
            Q(lines__product__name__icontains=search_query)
        ).distinct()
    if status_filter:
        receipts = receipts.filter(status=status_filter)
    if supplier_filter:
        receipts = receipts.filter(partner_id=supplier_filter)
    if warehouse_filter:
        receipts = receipts.filter(destination_location__warehouse_id=warehouse_filter)
    
    suppliers = Partner.objects.filter(
        Q(partner_type='supplier') | Q(partner_type='both')
    )
    warehouses = Warehouse.objects.all()
    
    context = {
        'receipts': receipts,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'status_types': InventoryOperation.STATUS_TYPES,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
            'supplier': supplier_filter,
            'warehouse': warehouse_filter,
        }
    }
    return render(request, 'core/receipts_list.html', context)

@login_required
def receipt_create(request):
    """Create a new receipt"""
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.type = 'RECEIPT'
            receipt.status = 'DRAFT'
            receipt.created_by = request.user
            receipt.save()
            
            # Handle line items
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantities')
            
            lines_created = False
            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity and int(quantity) > 0:
                    try:
                        product = Product.objects.get(pk=product_id)
                        OperationLine.objects.create(
                            operation=receipt,
                            product=product,
                            quantity=int(quantity)
                        )
                        lines_created = True
                    except (Product.DoesNotExist, ValueError):
                        pass
            
            if not lines_created:
                messages.error(request, 'Please add at least one product with quantity.')
                products = Product.objects.filter(is_active=True).select_related('category', 'uom')
                context = {
                    'form': form,
                    'products': products,
                    'title': 'Create Receipt'
                }
                return render(request, 'core/receipt_form.html', context)
            
            messages.success(request, f'Receipt "{receipt.reference}" created successfully!')
            return redirect('core:receipts_list')
    else:
        form = ReceiptForm()
    
    products = Product.objects.filter(is_active=True).select_related('category', 'uom')
    
    context = {
        'form': form,
        'products': products,
        'title': 'Create Receipt'
    }
    return render(request, 'core/receipt_form.html', context)

@login_required
def receipt_validate(request, pk):
    """Validate a receipt - increases stock"""
    receipt = get_object_or_404(InventoryOperation, pk=pk, type='RECEIPT')
    
    if receipt.status == 'DONE':
        messages.warning(request, 'This receipt has already been validated.')
        return redirect('core:receipts_list')
    
    if not receipt.lines.exists():
        messages.error(request, 'Cannot validate receipt without line items.')
        return redirect('core:receipts_list')
    
    # Update stock levels
    for line in receipt.lines.all():
        stock_level, created = StockLevel.objects.get_or_create(
            product=line.product,
            location=receipt.destination_location,
            defaults={'quantity': 0}
        )
        stock_level.quantity += line.quantity
        stock_level.save()
    
    # Update receipt status
    receipt.status = 'DONE'
    receipt.save()
    
    messages.success(request, f'Receipt "{receipt.reference}" validated successfully! Stock updated.')
    return redirect('core:receipts_list')

@login_required
def partner_create(request):
    """Create a new partner (supplier/customer)"""
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            partner = form.save()
            messages.success(request, f'Partner "{partner.name}" created successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'partner_id': partner.id,
                    'partner_name': str(partner)
                })
            return redirect('core:receipts_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = PartnerForm()
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('core/partner_form_modal.html', {'form': form}, request=request)
        from django.http import JsonResponse
        return JsonResponse({'html': html})
    
    context = {
        'form': form,
        'title': 'Add Partner'
    }
    return render(request, 'core/partner_form.html', context)

# ==========================
# DELIVERY ORDERS
# ==========================

@login_required
def deliveries_list(request):
    """List all delivery orders with search and filter capabilities"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    warehouse_filter = request.GET.get('warehouse', '')
    
    deliveries = InventoryOperation.objects.filter(
        type='DELIVERY'
    ).select_related(
        'partner', 'source_location__warehouse', 'created_by'
    ).prefetch_related('lines__product').order_by('-created_at')
    
    # Apply filters
    if search_query:
        deliveries = deliveries.filter(
            Q(reference__icontains=search_query) |
            Q(lines__product__sku__icontains=search_query) |
            Q(lines__product__name__icontains=search_query)
        ).distinct()
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)
    if customer_filter:
        deliveries = deliveries.filter(partner_id=customer_filter)
    if warehouse_filter:
        deliveries = deliveries.filter(source_location__warehouse_id=warehouse_filter)
    
    customers = Partner.objects.filter(
        Q(partner_type='customer') | Q(partner_type='both')
    )
    warehouses = Warehouse.objects.all()
    
    context = {
        'deliveries': deliveries,
        'customers': customers,
        'warehouses': warehouses,
        'status_types': InventoryOperation.STATUS_TYPES,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
            'customer': customer_filter,
            'warehouse': warehouse_filter,
        }
    }
    return render(request, 'core/deliveries_list.html', context)

@login_required
def delivery_create(request):
    """Create a new delivery order"""
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.type = 'DELIVERY'
            delivery.status = 'DRAFT'
            delivery.created_by = request.user
            delivery.save()
            
            # Handle line items
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantities')
            
            lines_created = False
            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity and int(quantity) > 0:
                    try:
                        product = Product.objects.get(pk=product_id)
                        OperationLine.objects.create(
                            operation=delivery,
                            product=product,
                            quantity=int(quantity)
                        )
                        lines_created = True
                    except (Product.DoesNotExist, ValueError):
                        pass
            
            if not lines_created:
                messages.error(request, 'Please add at least one product with quantity.')
                products = Product.objects.filter(is_active=True).select_related('category', 'uom')
                context = {
                    'form': form,
                    'products': products,
                    'title': 'Create Delivery Order'
                }
                return render(request, 'core/delivery_form.html', context)
            
            messages.success(request, f'Delivery Order "{delivery.reference}" created successfully!')
            return redirect('core:deliveries_list')
    else:
        form = DeliveryForm()
    
    products = Product.objects.filter(is_active=True).select_related('category', 'uom')
    
    context = {
        'form': form,
        'products': products,
        'title': 'Create Delivery Order'
    }
    return render(request, 'core/delivery_form.html', context)

@login_required
def delivery_validate(request, pk):
    """Validate a delivery - decreases stock"""
    delivery = get_object_or_404(InventoryOperation, pk=pk, type='DELIVERY')
    
    if delivery.status == 'DONE':
        messages.warning(request, 'This delivery has already been validated.')
        return redirect('core:deliveries_list')
    
    if not delivery.lines.exists():
        messages.error(request, 'Cannot validate delivery without line items.')
        return redirect('core:deliveries_list')
    
    # Check stock availability
    for line in delivery.lines.all():
        stock_level = StockLevel.objects.filter(
            product=line.product,
            location=delivery.source_location
        ).first()
        
        if not stock_level or stock_level.quantity < line.quantity:
            messages.error(
                request, 
                f'Insufficient stock for {line.product.sku}. Available: {stock_level.quantity if stock_level else 0}, Required: {line.quantity}'
            )
            return redirect('core:deliveries_list')
    
    # Update stock levels
    for line in delivery.lines.all():
        stock_level = StockLevel.objects.get(
            product=line.product,
            location=delivery.source_location
        )
        stock_level.quantity -= line.quantity
        stock_level.save()
    
    # Update delivery status
    delivery.status = 'DONE'
    delivery.save()
    
    messages.success(request, f'Delivery Order "{delivery.reference}" validated successfully! Stock updated.')
    return redirect('core:deliveries_list')

# ==========================
# INTERNAL TRANSFERS
# ==========================

@login_required
def internal_transfers_list(request):
    """List all internal transfers with search and filter capabilities"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    warehouse_filter = request.GET.get('warehouse', '')
    
    transfers = InventoryOperation.objects.filter(
        type='INTERNAL'
    ).select_related(
        'source_location__warehouse', 'destination_location__warehouse', 'created_by'
    ).prefetch_related('lines__product').order_by('-created_at')
    
    # Apply filters
    if search_query:
        transfers = transfers.filter(
            Q(reference__icontains=search_query) |
            Q(lines__product__sku__icontains=search_query) |
            Q(lines__product__name__icontains=search_query)
        ).distinct()
    if status_filter:
        transfers = transfers.filter(status=status_filter)
    if warehouse_filter:
        transfers = transfers.filter(
            Q(source_location__warehouse_id=warehouse_filter) |
            Q(destination_location__warehouse_id=warehouse_filter)
        )
    
    warehouses = Warehouse.objects.all()
    
    context = {
        'transfers': transfers,
        'warehouses': warehouses,
        'status_types': InventoryOperation.STATUS_TYPES,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
            'warehouse': warehouse_filter,
        }
    }
    return render(request, 'core/internal_transfers_list.html', context)

@login_required
def internal_transfer_create(request):
    """Create a new internal transfer"""
    if request.method == 'POST':
        form = InternalTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.type = 'INTERNAL'
            transfer.status = 'DRAFT'
            transfer.created_by = request.user
            transfer.save()
            
            # Handle line items
            product_ids = request.POST.getlist('products')
            quantities = request.POST.getlist('quantities')
            
            lines_created = False
            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity and int(quantity) > 0:
                    try:
                        product = Product.objects.get(pk=product_id)
                        OperationLine.objects.create(
                            operation=transfer,
                            product=product,
                            quantity=int(quantity)
                        )
                        lines_created = True
                    except (Product.DoesNotExist, ValueError):
                        pass
            
            if not lines_created:
                messages.error(request, 'Please add at least one product with quantity.')
                products = Product.objects.filter(is_active=True).select_related('category', 'uom')
                locations = Location.objects.all()
                context = {
                    'form': form,
                    'products': products,
                    'locations': locations,
                    'title': 'Create Internal Transfer'
                }
                return render(request, 'core/internal_transfer_form.html', context)
            
            messages.success(request, f'Internal Transfer "{transfer.reference}" created successfully!')
            return redirect('core:internal_transfers_list')
    else:
        form = InternalTransferForm()
    
    products = Product.objects.filter(is_active=True).select_related('category', 'uom')
    locations = Location.objects.all()
    
    context = {
        'form': form,
        'products': products,
        'locations': locations,
        'title': 'Create Internal Transfer'
    }
    return render(request, 'core/internal_transfer_form.html', context)

@login_required
def internal_transfer_validate(request, pk):
    """Validate an internal transfer - moves stock"""
    transfer = get_object_or_404(InventoryOperation, pk=pk, type='INTERNAL')
    
    if transfer.status == 'DONE':
        messages.warning(request, 'This transfer has already been validated.')
        return redirect('core:internal_transfers_list')
    
    if not transfer.lines.exists():
        messages.error(request, 'Cannot validate transfer without line items.')
        return redirect('core:internal_transfers_list')
    
    if not transfer.source_location or not transfer.destination_location:
        messages.error(request, 'Source and destination locations are required.')
        return redirect('core:internal_transfers_list')
    
    # Check stock availability at source
    for line in transfer.lines.all():
        stock_level = StockLevel.objects.filter(
            product=line.product,
            location=transfer.source_location
        ).first()
        
        if not stock_level or stock_level.quantity < line.quantity:
            messages.error(
                request, 
                f'Insufficient stock for {line.product.sku} at source location. Available: {stock_level.quantity if stock_level else 0}, Required: {line.quantity}'
            )
            return redirect('core:internal_transfers_list')
    
    # Update stock levels - decrease at source, increase at destination
    for line in transfer.lines.all():
        # Decrease at source
        source_stock, created = StockLevel.objects.get_or_create(
            product=line.product,
            location=transfer.source_location,
            defaults={'quantity': 0}
        )
        source_stock.quantity -= line.quantity
        source_stock.save()
        
        # Increase at destination
        dest_stock, created = StockLevel.objects.get_or_create(
            product=line.product,
            location=transfer.destination_location,
            defaults={'quantity': 0}
        )
        dest_stock.quantity += line.quantity
        dest_stock.save()
    
    # Update transfer status
    transfer.status = 'DONE'
    transfer.save()
    
    messages.success(request, f'Internal Transfer "{transfer.reference}" validated successfully! Stock moved.')
    return redirect('core:internal_transfers_list')

# ==========================
# STOCK ADJUSTMENTS
# ==========================

@login_required
def stock_adjustments_list(request):
    """List all stock adjustments with search and filter capabilities"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    warehouse_filter = request.GET.get('warehouse', '')
    product_filter = request.GET.get('product', '')
    
    adjustments = InventoryOperation.objects.filter(
        type='ADJUST'
    ).select_related(
        'source_location__warehouse', 'created_by'
    ).prefetch_related('lines__product').order_by('-created_at')
    
    # Apply filters
    if search_query:
        adjustments = adjustments.filter(
            Q(reference__icontains=search_query) |
            Q(lines__product__sku__icontains=search_query) |
            Q(lines__product__name__icontains=search_query)
        ).distinct()
    if status_filter:
        adjustments = adjustments.filter(status=status_filter)
    if warehouse_filter:
        adjustments = adjustments.filter(source_location__warehouse_id=warehouse_filter)
    if product_filter:
        adjustments = adjustments.filter(lines__product_id=product_filter).distinct()
    
    warehouses = Warehouse.objects.all()
    products = Product.objects.filter(is_active=True)
    
    context = {
        'adjustments': adjustments,
        'warehouses': warehouses,
        'products': products,
        'status_types': InventoryOperation.STATUS_TYPES,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
            'warehouse': warehouse_filter,
            'product': product_filter,
        }
    }
    return render(request, 'core/stock_adjustments_list.html', context)

@login_required
def stock_adjustment_create(request):
    """Create a new stock adjustment"""
    location_id = request.GET.get('location')
    product_filter = request.GET.get('product', '')
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.type = 'ADJUST'
            adjustment.status = 'DRAFT'
            adjustment.destination_location = adjustment.source_location  # For adjustments, both are same
            adjustment.created_by = request.user
            adjustment.save()
            
            # Handle adjustment lines - product, system_qty, physical_qty
            product_ids = request.POST.getlist('products')
            system_quantities = request.POST.getlist('system_quantities')
            physical_quantities = request.POST.getlist('physical_quantities')
            
            lines_created = False
            for product_id, sys_qty, phys_qty in zip(product_ids, system_quantities, physical_quantities):
                if product_id and phys_qty:
                    try:
                        product = Product.objects.get(pk=product_id)
                        physical_qty = int(phys_qty)
                        system_qty = int(sys_qty) if sys_qty else 0
                        difference = physical_qty - system_qty
                        
                        if difference != 0:  # Only create line if there's a difference
                            OperationLine.objects.create(
                                operation=adjustment,
                                product=product,
                                quantity=difference  # Store actual difference (can be + or -)
                            )
                            lines_created = True
                    except (Product.DoesNotExist, ValueError):
                        pass
            
            if not lines_created:
                messages.error(request, 'Please add at least one product with a quantity difference.')
                location = adjustment.source_location if adjustment.source_location else None
                products = Product.objects.filter(is_active=True).select_related('category', 'uom')
                if location:
                    # Get products with stock at this location and annotate with stock quantity
                    products_with_stock = StockLevel.objects.filter(location=location).select_related('product')
                    product_stock_map = {sl.product_id: sl.quantity for sl in products_with_stock}
                    products = products.filter(id__in=product_stock_map.keys())
                    # Annotate products with stock
                    for product in products:
                        product.current_stock = product_stock_map.get(product.id, 0)
                if product_filter:
                    products = products.filter(id=product_filter)
                
                context = {
                    'form': form,
                    'products': products,
                    'location': location,
                    'title': 'Create Stock Adjustment'
                }
                return render(request, 'core/stock_adjustment_form.html', context)
            
            messages.success(request, f'Stock Adjustment "{adjustment.reference}" created successfully!')
            return redirect('core:stock_adjustments_list')
    else:
        form = StockAdjustmentForm()
        if location_id:
            try:
                location = Location.objects.get(pk=location_id)
                form.fields['source_location'].initial = location
            except Location.DoesNotExist:
                pass
    
    location = Location.objects.get(pk=location_id) if location_id else None
    products = Product.objects.filter(is_active=True).select_related('category', 'uom')
    product_stock_map = {}
    
    if location:
        # Get products with stock at this location and annotate with stock quantity
        products_with_stock = StockLevel.objects.filter(location=location).select_related('product')
        product_stock_map = {sl.product_id: sl.quantity for sl in products_with_stock}
        products = products.filter(id__in=product_stock_map.keys())
        # Annotate products with stock
        for product in products:
            product.current_stock = product_stock_map.get(product.id, 0)
    if product_filter:
        products = products.filter(id=product_filter)
    
    context = {
        'form': form,
        'products': products,
        'location': location,
        'product_stock_map': product_stock_map,
        'title': 'Create Stock Adjustment'
    }
    return render(request, 'core/stock_adjustment_form.html', context)

@login_required
def stock_adjustment_validate(request, pk):
    """Validate a stock adjustment - updates stock to physical count"""
    adjustment = get_object_or_404(InventoryOperation, pk=pk, type='ADJUST')
    
    if adjustment.status == 'DONE':
        messages.warning(request, 'This adjustment has already been validated.')
        return redirect('core:stock_adjustments_list')
    
    if not adjustment.lines.exists():
        messages.error(request, 'Cannot validate adjustment without line items.')
        return redirect('core:stock_adjustments_list')
    
    if not adjustment.source_location:
        messages.error(request, 'Location is required.')
        return redirect('core:stock_adjustments_list')
    
    # Update stock levels based on adjustment lines
    # The line.quantity represents the absolute difference
    # We need to determine if it's an increase or decrease
    # Since we stored the absolute difference, we'll need to check the current stock
    # and apply the adjustment accordingly
    # Note: This is a simplified approach - ideally store both system_qty and physical_qty
    
    for line in adjustment.lines.all():
        stock_level, created = StockLevel.objects.get_or_create(
            product=line.product,
            location=adjustment.source_location,
            defaults={'quantity': 0}
        )
        
        # The line.quantity is the absolute difference
        # We need to determine direction - for now, we'll assume it's stored correctly
        # In a real system, you'd have a separate field for increase/decrease
        # For this implementation, we'll use the difference stored in the line
        # and apply it as an adjustment (could be positive or negative)
        
        # Since we only store absolute difference, we'll need to infer direction
        # This is a limitation - ideally store both values
        # For now, we'll apply the adjustment as stored
        # The physical quantity would be: system_qty + difference (if positive) or system_qty - difference (if negative)
        
        # Apply the difference (can be positive or negative)
        # Positive difference = increase stock, Negative difference = decrease stock
        current_stock = stock_level.quantity
        new_stock = max(0, current_stock + line.quantity)  # Apply difference (can be + or -)
        stock_level.quantity = new_stock
        stock_level.save()
    
    # Update adjustment status
    adjustment.status = 'DONE'
    adjustment.save()
    
    messages.success(request, f'Stock Adjustment "{adjustment.reference}" validated successfully! Stock updated.')
    return redirect('core:stock_adjustments_list')

# ==========================
# MOVE HISTORY (STOCK LEDGER)
# ==========================

@login_required
def move_history(request):
    """View-only history of all stock movements"""
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    product_filter = request.GET.get('product', '')
    warehouse_filter = request.GET.get('warehouse', '')
    location_filter = request.GET.get('location', '')
    doc_type_filter = request.GET.get('doc_type', '')
    
    # Build query from InventoryOperation and OperationLine
    # Since StockLedgerEntry might not be populated, we'll use operations
    operations = InventoryOperation.objects.filter(
        status='DONE'  # Only show completed operations
    ).select_related(
        'source_location__warehouse',
        'destination_location__warehouse',
        'created_by'
    ).prefetch_related('lines__product').order_by('-created_at')
    
    # Apply filters
    if date_from:
        operations = operations.filter(created_at__gte=date_from)
    if date_to:
        operations = operations.filter(created_at__lte=date_to)
    if product_filter:
        operations = operations.filter(lines__product_id=product_filter).distinct()
    if warehouse_filter:
        operations = operations.filter(
            Q(source_location__warehouse_id=warehouse_filter) |
            Q(destination_location__warehouse_id=warehouse_filter)
        )
    if location_filter:
        operations = operations.filter(
            Q(source_location_id=location_filter) |
            Q(destination_location_id=location_filter)
        )
    if doc_type_filter:
        operations = operations.filter(type=doc_type_filter)
    
    # Build move history entries from operations
    move_history_entries = []
    for operation in operations:
        for line in operation.lines.all():
            # Determine quantity change direction based on operation type
            if operation.type == 'RECEIPT':
                qty_change = line.quantity  # Positive (incoming)
                from_loc = None
                to_loc = operation.destination_location
            elif operation.type == 'DELIVERY':
                qty_change = -line.quantity  # Negative (outgoing)
                from_loc = operation.source_location
                to_loc = None
            elif operation.type == 'INTERNAL':
                qty_change = line.quantity  # Positive at destination
                from_loc = operation.source_location
                to_loc = operation.destination_location
            else:  # ADJUST
                qty_change = line.quantity  # Can be positive or negative
                from_loc = operation.source_location
                to_loc = operation.source_location  # Same location for adjustments
            
            move_history_entries.append({
                'date_time': operation.created_at,
                'product': line.product,
                'from_location': from_loc,
                'to_location': to_loc,
                'quantity_change': qty_change,
                'document_type': operation.get_type_display(),
                'document_type_code': operation.type,
                'document_reference': operation.reference or '(no ref)',
                'performed_by': operation.created_by,
            })
    
    # Sort by date (most recent first)
    move_history_entries.sort(key=lambda x: x['date_time'], reverse=True)
    
    # Get filter options
    products = Product.objects.filter(is_active=True).order_by('name')
    warehouses = Warehouse.objects.all()
    locations = Location.objects.all()
    
    context = {
        'move_history_entries': move_history_entries,
        'products': products,
        'warehouses': warehouses,
        'locations': locations,
        'operation_types': InventoryOperation.OPERATION_TYPES,
        'current_filters': {
            'date_from': date_from,
            'date_to': date_to,
            'product': product_filter,
            'warehouse': warehouse_filter,
            'location': location_filter,
            'doc_type': doc_type_filter,
        }
    }
    return render(request, 'core/move_history.html', context)

# ==========================
# WAREHOUSES
# ==========================

@login_required
def warehouses_list(request):
    """List all warehouses with statistics"""
    warehouses = Warehouse.objects.annotate(
        location_count=Count('locations', distinct=True),
        product_count=Count('locations__stock_levels__product', distinct=True)
    ).order_by('code')
    
    context = {
        'warehouses': warehouses,
    }
    return render(request, 'core/warehouses_list.html', context)

@login_required
def warehouse_detail(request, pk):
    """Detail view of a warehouse with locations"""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    
    # Get all locations for this warehouse
    locations = Location.objects.filter(warehouse=warehouse).annotate(
        product_count=Count('stock_levels__product', distinct=True),
        total_stock=Sum('stock_levels__quantity')
    ).order_by('name')
    
    # Get statistics
    total_locations = locations.count()
    total_products = StockLevel.objects.filter(
        location__warehouse=warehouse
    ).values('product').distinct().count()
    total_quantity = StockLevel.objects.filter(
        location__warehouse=warehouse
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'warehouse': warehouse,
        'locations': locations,
        'total_locations': total_locations,
        'total_products': total_products,
        'total_quantity': total_quantity,
    }
    return render(request, 'core/warehouse_detail.html', context)

@login_required
def warehouse_create(request):
    """Create a new warehouse"""
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save()
            messages.success(request, f'Warehouse "{warehouse.name}" created successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'warehouse_id': warehouse.id,
                    'warehouse_name': str(warehouse)
                })
            return redirect('core:warehouses_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = WarehouseForm()
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('core/warehouse_form_modal.html', {'form': form}, request=request)
        from django.http import JsonResponse
        return JsonResponse({'html': html})
    
    context = {
        'form': form,
        'title': 'Add Warehouse'
    }
    return render(request, 'core/warehouse_form.html', context)

@login_required
def location_create(request):
    """Create a new location"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" created successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'location_id': location.id,
                    'location_name': str(location)
                })
            return redirect('core:warehouses_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = LocationForm()
    
    # If AJAX request, return form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('core/location_form_modal.html', {'form': form}, request=request)
        from django.http import JsonResponse
        return JsonResponse({'html': html})
    
    context = {
        'form': form,
        'title': 'Add Location'
    }
    return render(request, 'core/location_form.html', context)

# ==========================
# MY PROFILE
# ==========================

@login_required
def my_profile(request):
    """User profile page"""
    user = request.user
    
    # Get user statistics
    receipts_created = InventoryOperation.objects.filter(
        type='RECEIPT',
        created_by=user
    ).count()
    
    deliveries_created = InventoryOperation.objects.filter(
        type='DELIVERY',
        created_by=user
    ).count()
    
    transfers_created = InventoryOperation.objects.filter(
        type='INTERNAL',
        created_by=user
    ).count()
    
    adjustments_created = InventoryOperation.objects.filter(
        type='ADJUST',
        created_by=user
    ).count()
    
    context = {
        'user': user,
        'receipts_created': receipts_created,
        'deliveries_created': deliveries_created,
        'transfers_created': transfers_created,
        'adjustments_created': adjustments_created,
    }
    return render(request, 'core/my_profile.html', context)
