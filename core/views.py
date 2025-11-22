from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):
    # Dummy data for dashboard
    context = {
        'total_products': 1250,
        'low_stock_items': 15,
        'out_of_stock_items': 8,
        'pending_receipts': 12,
        'pending_deliveries': 18,
        'internal_transfers': 5,
        'recent_operations': [
            {
                'reference': 'WH1/IN/2025/0001',
                'type': 'Receipt',
                'source': '-',
                'destination': 'Main Warehouse - Receiving',
                'status': 'Done',
                'scheduled_date': '2025-01-15',
                'last_updated': '2025-01-15 10:30 AM'
            },
            {
                'reference': 'WH1/OUT/2025/0002',
                'type': 'Delivery',
                'source': 'Main Warehouse - Shipping',
                'destination': '-',
                'status': 'Ready',
                'scheduled_date': '2025-01-16',
                'last_updated': '2025-01-15 02:15 PM'
            },
            {
                'reference': 'WH1/MOVE/2025/0003',
                'type': 'Internal Transfer',
                'source': 'Main Warehouse - Rack A',
                'destination': 'Main Warehouse - Rack B',
                'status': 'Done',
                'scheduled_date': '2025-01-14',
                'last_updated': '2025-01-14 11:20 AM'
            },
        ]
    }
    return render(request, 'core/dashboard.html', context)
