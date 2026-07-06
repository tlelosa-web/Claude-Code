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

    # Relationships
    movements = db.relationship('StockMovement', backref='item', lazy=True)
    bom_lines = db.relationship('BOMLine', backref='item', lazy=True)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    line_items = db.relationship('SOLineItem', backref='sales_order', lazy=True, cascade="all, delete-orphan")
    works_orders = db.relationship('WorksOrder', backref='sales_order', lazy=True)

    @property
    def job_reference(self):
        if self.job_numbers:
            return f"{self.job_numbers} - {self.so_number}"
        return self.so_number

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
    status = db.Column(db.String(50), default='Open')  # Open / Complete / Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('StockOrderLine', backref='stock_order', lazy=True,
                            cascade='all, delete-orphan')
    sales_order = db.relationship('SalesOrder', backref='stock_orders')


class StockOrderLine(db.Model):
    __tablename__ = 'stock_order_line'

    id = db.Column(db.Integer, primary_key=True)
    stock_order_id = db.Column(db.Integer, db.ForeignKey('stock_order.id'), nullable=False)
    item_code = db.Column(db.String(100))
    description = db.Column(db.Text)
    qty = db.Column(db.Float)
    notes = db.Column(db.Text)
