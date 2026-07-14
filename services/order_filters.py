"""Single source of truth for "open/active" status definitions.

Used by the 4 list_orders() routes (Sales Orders, Works Orders, Stock
Orders, Purchase Orders) and the Dashboard to filter out
completed/closed/cancelled records when the user opts into the
"Open only" view. Centralised here so the status strings aren't
duplicated (and drift) across route files.

See docs/specs/dashboard-open-filter.md for the decision record.
"""

# SalesOrder.status: Draft / Open / Closed
SO_ACTIVE = ('Draft', 'Open')

# WorksOrder.status: Open / In Progress / Complete / Cancelled
WO_ACTIVE = ('Open', 'In Progress')

# StockOrder.status: Open / Picking / Complete / Cancelled
STO_ACTIVE = ('Open', 'Picking')

# PurchaseOrder.status: Draft / Open / Partially Received / Received / Cancelled
PO_ACTIVE = ('Draft', 'Open', 'Partially Received')
