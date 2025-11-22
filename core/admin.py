from django.contrib import admin
from .models import (
    Category, UnitOfMeasure, Partner,
    Product, Warehouse, Location,
    InventoryOperation, OperationLine,
    StockLevel, StockLedgerEntry
)

# ================================
# BASIC MODELS (Simple Admin)
# ================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(UnitOfMeasure)
class UOMAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_type", "phone", "email")
    list_filter = ("partner_type",)
    search_fields = ("name", "phone", "email")


# ================================
# PRODUCT
# ================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "uom", "min_stock", "cost", "is_active")
    list_filter = ("category", "uom", "is_active")
    search_fields = ("sku", "name")
    list_editable = ("is_active", "min_stock")


# ================================
# WAREHOUSE + LOCATIONS
# ================================

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "address")
    search_fields = ("name", "code")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "warehouse")
    list_filter = ("warehouse",)
    search_fields = ("name",)


# ================================
# INLINE for Operation Lines
# ================================

class OperationLineInline(admin.TabularInline):
    model = OperationLine
    extra = 1
    autocomplete_fields = ("product",)


# ================================
# INVENTORY OPERATION
# ================================

@admin.register(InventoryOperation)
class InventoryOperationAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "type", "status",
        "source_location", "destination_location",
        "partner", "created_by",
        "scheduled_date", "created_at"
    )
    list_filter = (
        "type", "status",
        "source_location__warehouse",
        "destination_location__warehouse",
        "created_at", "scheduled_date"
    )
    search_fields = (
        "reference",
        "partner__name",
        "source_location__name",
        "destination_location__name",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [OperationLineInline]
    autocomplete_fields = ("partner", "source_location", "destination_location", "created_by")


# ================================
# STOCK LEVEL (Live Stock)
# ================================

@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity")
    list_filter = ("location__warehouse", "location", "product")
    search_fields = ("product__name", "product__sku", "location__name")
    ordering = ("product", "location")


# ================================
# STOCK LEDGER (Full Move History)
# ================================

@admin.register(StockLedgerEntry)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "operation",
        "quantity_change",
        "source_location",
        "destination_location",
        "created_at"
    )
    list_filter = (
        "product",
        "source_location__warehouse",
        "destination_location__warehouse",
        "operation__type",
        "created_at"
    )
    search_fields = (
        "product__sku",
        "product__name",
        "operation__reference",
        "source_location__name",
        "destination_location__name",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    autocomplete_fields = ("product", "operation", "line")

# Register OperationLine so autocomplete_fields can use it
@admin.register(OperationLine)
class OperationLineAdmin(admin.ModelAdmin):
    list_display = ("operation", "product", "quantity")
    search_fields = ("operation__reference", "product__name", "product__sku")
    autocomplete_fields = ("operation", "product")
