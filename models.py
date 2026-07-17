from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'item'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    last_cost = db.Column(db.Float, default=0.0)
    avg_cost = db.Column(db.Float, default=0.0)
    excl_price = db.Column(db.Float, default=0.0)
    incl_price = db.Column(db.Float, default=0.0)
    qty_on_hand = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reorder_point = db.Column(db.Float, default=0.0)  # flag for replenishment when qty_on_hand <= this
    reorder_qty = db.Column(db.Float, default=0.0)  # suggested qty for "Create PO from shortfall"
    max_level = db.Column(db.Float, default=0.0)  # target max stock level; 0 means "not set" (same convention as reorder_point)
    is_stocked_finished_good = db.Column(db.Boolean, default=False)  # opt-in: WO Complete produces this item's qty_on_hand; see docs/specs/production-receipt-on-wo-complete.md
    supplier = db.Column(db.String(255))  # most-frequent supplier from PO history, CSV-sourced
    lead_time_weeks = db.Column(db.Float, default=0.0)  # avg lead time in weeks, CSV-sourced
    amu = db.Column(db.Float, default=0.0)  # average monthly usage, CSV-sourced; 0.0 = not computed
    suggested_min = db.Column(db.Float, default=0.0)  # AMU-based suggested reorder point, CSV-sourced, informational only
    suggested_max = db.Column(db.Float, default=0.0)  # AMU-based suggested max level, CSV-sourced, informational only

    # Relationships
    movements = db.relationship('StockMovement', backref='item', lazy=True)
    bom_lines = db.relationship('BOMLine', backref='item', lazy=True)

PAYMENT_STATUS_OPTIONS = (
    'Cash Sale - Unpaid', 'Cash Sale - Paid', 'Cash Sale - Partial',
    'Account - Pending', 'Account - Up to Date', 'Account - On Hold', 'Account - Overdue',
)

class SalesOrder(db.Model):
    __tablename__ = 'sales_order'
    
    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(100), unique=True, nullable=False)
    job_numbers = db.Column(db.String(255))
    reference = db.Column(db.String(100))
    so_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    customer_name = db.Column(db.String(255))
    customer_vat = db.Column(db.String(100))
    delivery_address = db.Column(db.Text)
    sales_rep = db.Column(db.String(255))
    raw_pdf_text = db.Column(db.Text)
    status = db.Column(db.String(50), default='Draft')  # Draft / Open / Closed
    payment_status = db.Column(db.String(50), default='Account - Pending')  # Cash Sale - Unpaid/Paid/Partial / Account - Pending/Up to Date/On Hold/Overdue
    amount_paid = db.Column(db.Float, default=0.0)  # only read/written/displayed when payment_status == 'Cash Sale - Partial'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    line_items = db.relationship('SOLineItem', backref='sales_order', lazy=True, cascade="all, delete-orphan")
    works_orders = db.relationship('WorksOrder', backref='sales_order', lazy=True)

    @property
    def job_reference(self):
        if self.job_numbers:
            return f"{self.job_numbers} - {self.so_number}"
        return self.so_number

    @property
    def total_incl(self):
        return sum(li.incl_total or 0 for li in self.line_items)

    @property
    def balance_due(self):
        return self.total_incl - (self.amount_paid or 0.0)

class SOLineItem(db.Model):
    __tablename__ = 'so_line_item'
    
    id = db.Column(db.Integer, primary_key=True)
    so_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    description = db.Column(db.Text)
    qty = db.Column(db.Float)
    excl_price = db.Column(db.Float)
    vat_pct = db.Column(db.Float)
    excl_total = db.Column(db.Float)
    incl_total = db.Column(db.Float)
    job_number = db.Column(db.String(50))  # Per-line FM/Job number

class WorksOrder(db.Model):
    __tablename__ = 'works_order'
    
    id = db.Column(db.Integer, primary_key=True)
    wo_number = db.Column(db.String(100), unique=True, nullable=False)
    so_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    order_type = db.Column(db.String(50))  # 'ASSEMBLY' or 'STOCK'
    status = db.Column(db.String(50), default='Open')  # Open / In Progress / Complete / Cancelled
    issued_by = db.Column(db.String(255))
    job_number = db.Column(db.String(50))  # FM/Job number of the originating Fan line
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship for combined orders
    related_wo_id = db.Column(db.Integer, db.ForeignKey('works_order.id'), nullable=True)
    related_order = db.relationship('WorksOrder', remote_side=[id], foreign_keys=[related_wo_id])

    # Relationships
    bom_lines = db.relationship('BOMLine', backref='works_order', lazy=True, cascade="all, delete-orphan")

class BOMLine(db.Model):
    __tablename__ = 'bom_line'
    
    id = db.Column(db.Integer, primary_key=True)
    wo_id = db.Column(db.Integer, db.ForeignKey('works_order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    qty_required = db.Column(db.Float)
    qty_issued = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    # NEW FIELDS for nested BOM structure
    line_type = db.Column(db.String(20), default='COMPONENT')  # 'ASSEMBLY_ITEM' | 'COMPONENT'
    parent_line_id = db.Column(db.Integer, db.ForeignKey('bom_line.id'), nullable=True)
    
    # Self-referential relationship for children
    children = db.relationship('BOMLine', backref=db.backref('parent', remote_side=[id]), lazy=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movement'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    movement_type = db.Column(db.String(50))  # 'ISSUE' / 'RECEIPT' / 'ADJUSTMENT' / 'OPENING'
    reference = db.Column(db.String(100))
    qty_change = db.Column(db.Float)  # positive = in, negative = out
    qty_after = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StockOrder(db.Model):
    __tablename__ = 'stock_order'

    id = db.Column(db.Integer, primary_key=True)
    stock_order_number = db.Column(db.String(100), unique=True, nullable=False)
    so_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    status = db.Column(db.String(50), default='Open')  # Open / Picking / Complete / Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('StockOrderLine', backref='stock_order', lazy=True,
                            cascade='all, delete-orphan')
    sales_order = db.relationship('SalesOrder', backref='stock_orders')

    @property
    def job_numbers(self):
        """Distinct FM/Job numbers carried by this order's lines, comma-separated."""
        seen = []
        for line in self.lines:
            if line.job_number and line.job_number not in seen:
                seen.append(line.job_number)
        return ', '.join(seen)


class StockOrderLine(db.Model):
    __tablename__ = 'stock_order_line'

    id = db.Column(db.Integer, primary_key=True)
    stock_order_id = db.Column(db.Integer, db.ForeignKey('stock_order.id'), nullable=False)
    item_code = db.Column(db.String(100))
    description = db.Column(db.Text)
    qty = db.Column(db.Float)
    qty_issued = db.Column(db.Float, default=0.0)  # mirrors BOMLine.qty_issued
    notes = db.Column(db.Text)
    job_number = db.Column(db.String(50))  # Per-line FM/Job number (optional)


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(100), unique=True, nullable=False)
    reference = db.Column(db.String(100))  # FM job number(s), from filename/REFERENCE field
    supplier_name = db.Column(db.String(255))
    supplier_vat = db.Column(db.String(100))
    po_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    overall_discount_pct = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Draft')  # Draft / Open / Partially Received / Received / Cancelled
    raw_pdf_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    lines = db.relationship('POLine', backref='purchase_order', lazy=True,
                             cascade='all, delete-orphan')


class POLine(db.Model):
    __tablename__ = 'po_line'

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)  # null until matched/linked
    item_code_raw = db.Column(db.String(100))  # as extracted from PDF, even if unmatched
    description = db.Column(db.Text)
    qty_ordered = db.Column(db.Float)
    qty_received = db.Column(db.Float, default=0.0)
    excl_price = db.Column(db.Float)
    disc_pct = db.Column(db.Float)
    vat_pct = db.Column(db.Float)
    excl_total = db.Column(db.Float)
    incl_total = db.Column(db.Float)

    item = db.relationship('Item')


class Setting(db.Model):
    __tablename__ = 'setting'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255))
