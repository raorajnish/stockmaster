from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Products
    path('products/', views.products_list, name='products_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    # Categories
    path('categories/create/', views.category_create, name='category_create'),
    # Unit of Measure
    path('uom/create/', views.uom_create, name='uom_create'),
    # Receipts
    path('receipts/', views.receipts_list, name='receipts_list'),
    path('receipts/create/', views.receipt_create, name='receipt_create'),
    path('receipts/<int:pk>/validate/', views.receipt_validate, name='receipt_validate'),
    # Partners
    path('partners/create/', views.partner_create, name='partner_create'),
    
    # Delivery Orders
    path('deliveries/', views.deliveries_list, name='deliveries_list'),
    path('deliveries/create/', views.delivery_create, name='delivery_create'),
    path('deliveries/<int:pk>/validate/', views.delivery_validate, name='delivery_validate'),
    
    # Internal Transfers
    path('internal-transfers/', views.internal_transfers_list, name='internal_transfers_list'),
    path('internal-transfers/create/', views.internal_transfer_create, name='internal_transfer_create'),
    path('internal-transfers/<int:pk>/validate/', views.internal_transfer_validate, name='internal_transfer_validate'),
    
    # Stock Adjustments
    path('stock-adjustments/', views.stock_adjustments_list, name='stock_adjustments_list'),
    path('stock-adjustments/create/', views.stock_adjustment_create, name='stock_adjustment_create'),
    path('stock-adjustments/<int:pk>/validate/', views.stock_adjustment_validate, name='stock_adjustment_validate'),
]

