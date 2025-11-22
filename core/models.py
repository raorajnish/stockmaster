from django.db import models
from django.conf import settings
from django.utils import timezone


# ==========================
# BASIC MASTER TABLES
# ==========================

class Category(models.Model):
    """Product category (e.g. Raw Material, Finished Goods, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UnitOfMeasure(models.Model):
    """Unit of measure: Piece, Kg, Box, etc."""
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.abbreviation


class Partner(models.Model):
    """
    Supplier / Customer. Used on Receipts, Deliveries etc.
    """
    PARTNER_TYPES = (
        ("supplier", "Supplier"),
        ("customer", "Customer"),
        ("both", "Both"),
    )

    name = models.CharField(max_length=200)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.partner_type})"


# ==========================
# PRODUCT
# ==========================

class Product(models.Model):
    """
    Master product. Does NOT store movement refs.
    """
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.SET_NULL, null=True, blank=True)

    min_stock = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Product cost per unit")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"


# ==========================
# WAREHOUSES & LOCATIONS
# ==========================

class Warehouse(models.Model):
    """
    Warehouse/store.
    """
    name = models.CharField(max_length=150)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code used in references, e.g. WH1",
    )
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Location(models.Model):
    """
    Individual location inside a warehouse.
    """
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.warehouse.code} - {self.name}"


# ==========================
# INVENTORY OPERATIONS (UPDATED)
# ==========================

class InventoryOperation(models.Model):
    OPERATION_TYPES = (
        ("RECEIPT", "Receipt"),
        ("DELIVERY", "Delivery"),
        ("INTERNAL", "Internal Transfer"),
        ("ADJUST", "Stock Adjustment"),
    )

    STATUS_TYPES = (
        ("DRAFT", "Draft"),
        ("WAITING", "Waiting"),
        ("READY", "Ready"),
        ("DONE", "Done"),
        ("CANCEL", "Canceled"),
    )

    reference = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Document number, e.g. WH1/IN/2025/0001",
    )

    type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default="DRAFT")

    partner = models.ForeignKey(
        Partner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operations",
        help_text="Supplier or customer.",
    )

    source_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operations_as_source"
    )
    destination_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operations_as_dest"
    )

    scheduled_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_inventory_operations"
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference or '(no ref)'} ({self.type})"

    # -----------------------------------------
    # Clean operation code generator (IN/OUT/MOVE/ADJ)
    # -----------------------------------------
    def _get_operation_code(self):
        return {
            "RECEIPT": "IN",
            "DELIVERY": "OUT",
            "INTERNAL": "MOVE",
            "ADJUST": "ADJ",
        }.get(self.type, "UNK")

    # ------------------------------------------------
    # Warehouse deciding logic
    # ------------------------------------------------
    def _get_warehouse_for_reference(self):
        if self.type == "RECEIPT":
            loc = self.destination_location
        elif self.type == "DELIVERY":
            loc = self.source_location
        elif self.type == "INTERNAL":
            loc = self.source_location  # fixed rule
        else:  # ADJUST
            loc = self.source_location or self.destination_location

        return loc.warehouse if loc else None

    # ------------------------------------------------
    # Auto-generation logic
    # ------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.reference:
            op_code = self._get_operation_code()
            warehouse = self._get_warehouse_for_reference()

            wh_code = warehouse.code if warehouse else "WH"
            year = timezone.now().year

            qs = InventoryOperation.objects.filter(
                type=self.type,
                created_at__year=year,
            )

            if warehouse:
                qs = qs.filter(
                    models.Q(source_location__warehouse=warehouse) |
                    models.Q(destination_location__warehouse=warehouse)
                )

            last_number = 0
            if qs.exists():
                last_ref = qs.order_by("-id").first().reference
                try:
                    last_number = int(last_ref.split("/")[-1])
                except:
                    last_number = qs.last().id

            next_number = last_number + 1
            num_str = str(next_number).zfill(4)

            self.reference = f"{wh_code}/{op_code}/{year}/{num_str}"

        super().save(*args, **kwargs)


# ==========================
# OPERATION LINE ITEMS
# ==========================

class OperationLine(models.Model):
    operation = models.ForeignKey(InventoryOperation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.operation.reference} - {self.product.sku} ({self.quantity})"


# ==========================
# STOCK STATE
# ==========================

class StockLevel(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_levels")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="stock_levels")
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ("product", "location")

    def __str__(self):
        return f"{self.product.sku} @ {self.location}: {self.quantity}"


# ==========================
# STOCK LEDGER (MOVE HISTORY)
# ==========================

class StockLedgerEntry(models.Model):
    operation = models.ForeignKey(InventoryOperation, on_delete=models.CASCADE, related_name="ledger_entries")
    line = models.ForeignKey(OperationLine, on_delete=models.CASCADE, related_name="ledger_entries")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ledger_entries")

    source_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries_as_source"
    )
    destination_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_entries_as_dest"
    )

    quantity_change = models.IntegerField(help_text="Positive=incoming, Negative=outgoing")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.product.sku}: {self.quantity_change} "
            f"({self.source_location} -> {self.destination_location})"
        )
