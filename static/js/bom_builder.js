/* ============================================
   SOPS — BOM Builder JavaScript
   Handles item selection, shortfall detection,
   and order configuration for BOM generation
   ============================================ */

(function() {
    'use strict';

    if (typeof window.SOPS_BOM === 'undefined') {
        console.warn('SOPS_BOM config not found. BOM Builder may not work correctly.');
        return;
    }

    const config = window.SOPS_BOM;
    const items = config.items || [];
    const initialQty = config.initialQty || 1;

    // State
    let selectedItems = {};  // keyed by item id

    // DOM refs
    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const instockToggle = document.getElementById('instock-toggle');
    const selectedBody = document.getElementById('selected-items-body');
    const selectedCount = document.getElementById('selected-count');
    const totalCostEl = document.getElementById('total-cost');
    const shortfallCountEl = document.getElementById('shortfall-count');
    const bomItemsJson = document.getElementById('bom-items-json');
    const generateBtn = document.getElementById('generate-btn');

    // Render the item selection table
    function renderItemTable(filteredItems) {
        const tableEl = document.getElementById('item-table');
        if (!tableEl) return;

        if (filteredItems.length === 0) {
            tableEl.innerHTML = '<div style="padding: 40px; text-align: center; color: var(--text-muted);">No items match your filter criteria.</div>';
            return;
        }

        let html = '<table class="data-table" style="font-size: 0.85rem;"><thead><tr>' +
            '<th style="width: 40px;"></th>' +
            '<th>Code</th>' +
            '<th>Description</th>' +
            '<th>Category</th>' +
            '<th style="text-align: right;">Qty on Hand</th>' +
            '<th style="text-align: right;">Excl. Price</th>' +
            '</tr></thead><tbody>';

        filteredItems.forEach(function(item) {
            const isSelected = selectedItems[item.id] !== undefined;
            const isLowStock = item.qty_on_hand <= 0;

            html += '<tr class="' + (isLowStock ? 'row-amber' : '') + '" style="' + (isSelected ? 'background: rgba(232, 97, 10, 0.08);' : '') + '">' +
                '<td><input type="checkbox" class="item-select" data-id="' + item.id + '" ' + (isSelected ? 'checked' : '') + '></td>' +
                '<td><strong>' + escHtml(item.code) + '</strong></td>' +
                '<td>' + escHtml(item.description) + '</td>' +
                '<td>' + escHtml(item.category || '-') + '</td>' +
                '<td style="text-align: right; ' + (isLowStock ? 'color: var(--brand-danger); font-weight: 600;' : '') + '">' + item.qty_on_hand + '</td>' +
                '<td style="text-align: right;">R ' + (item.excl_price || 0).toFixed(2) + '</td>' +
                '</tr>';
        });

        html += '</tbody></table>';
        tableEl.innerHTML = html;

        // Bind checkbox events
        tableEl.querySelectorAll('.item-select').forEach(function(cb) {
            cb.addEventListener('change', function() {
                const itemId = parseInt(this.dataset.id);
                if (this.checked) {
                    addItem(itemId);
                } else {
                    removeItem(itemId);
                }
            });
        });
    }

    // Add item to selection
    function addItem(itemId) {
        if (selectedItems[itemId]) return;

        const item = items.find(function(i) { return i.id === itemId; });
        if (!item) return;

        selectedItems[itemId] = {
            item_id: itemId,
            qty_required: initialQty,
            unit_cost: item.avg_cost > 0 ? item.avg_cost : item.last_cost,
            notes: ''
        };

        updateSelectedTable();
        updateSummary();
    }

    // Remove item from selection
    function removeItem(itemId) {
        delete selectedItems[itemId];
        updateSelectedTable();
        updateSummary();

        // Uncheck the checkbox in the item table
        const cb = document.querySelector('.item-select[data-id="' + itemId + '"]');
        if (cb) cb.checked = false;
    }

    // Update quantity for a selected item
    function updateQty(itemId, qty) {
        if (!selectedItems[itemId]) return;

        qty = Math.max(0, parseFloat(qty) || 0);
        selectedItems[itemId].qty_required = qty;

        updateSelectedTable();
        updateSummary();
    }

    // Render the selected items table
    function updateSelectedTable() {
        const ids = Object.keys(selectedItems);
        if (ids.length === 0) {
            selectedBody.innerHTML = '';
            return;
        }

        let html = '';
        ids.forEach(function(id) {
            const entry = selectedItems[id];
            const item = items.find(function(i) { return i.id === parseInt(id); });
            if (!item) return;

            const totalCost = entry.qty_required * entry.unit_cost;
            const shortfall = Math.max(0, entry.qty_required - item.qty_on_hand);

            html += '<tr class="' + (shortfall > 0 ? 'row-amber' : '') + '">' +
                '<td><strong>' + escHtml(item.code) + '</strong></td>' +
                '<td>' + escHtml(item.description) + '</td>' +
                '<td style="' + (shortfall > 0 ? 'color: var(--brand-amber); font-weight: 600;' : '') + '">' +
                    item.qty_on_hand + 
                    (shortfall > 0 ? ' <span style="color: var(--brand-danger); font-size: 0.75rem;">(short ' + shortfall + ')</span>' : '') +
                '</td>' +
                '<td><input type="number" class="qty-input form-input" data-id="' + id + '" value="' + entry.qty_required + '" min="0" step="0.01" style="width: 80px; padding: 4px 6px; font-size: 0.85rem;"></td>' +
                '<td>R ' + entry.unit_cost.toFixed(2) + '</td>' +
                '<td>R ' + totalCost.toFixed(2) + '</td>' +
                '<td><button type="button" class="btn btn-danger remove-btn" data-id="' + id + '" style="padding: 2px 6px; font-size: 0.7rem;">&times;</button></td>' +
                '</tr>';
        });

        selectedBody.innerHTML = html;

        // Bind qty input events
        selectedBody.querySelectorAll('.qty-input').forEach(function(input) {
            input.addEventListener('input', function() {
                updateQty(parseInt(this.dataset.id), this.value);
            });
        });

        // Bind remove button events
        selectedBody.querySelectorAll('.remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                removeItem(parseInt(this.dataset.id));
            });
        });
    }

    // Update summary panels
    function updateSummary() {
        const ids = Object.keys(selectedItems);
        const count = ids.length;

        let totalCost = 0;
        let shortfallCount = 0;

        ids.forEach(function(id) {
            const entry = selectedItems[id];
            const item = items.find(function(i) { return i.id === parseInt(id); });
            if (!item) return;

            totalCost += entry.qty_required * entry.unit_cost;
            if (entry.qty_required > item.qty_on_hand) {
                shortfallCount++;
            }
        });

        selectedCount.textContent = count + ' item' + (count !== 1 ? 's' : '') + ' selected';
        totalCostEl.textContent = 'R ' + totalCost.toFixed(2);

        if (shortfallCount > 0) {
            shortfallCountEl.textContent = shortfallCount + ' item' + (shortfallCount !== 1 ? 's' : '') + ' with shortfall';
        } else {
            shortfallCountEl.textContent = '';
        }

        // Enable/disable generate button
        if (generateBtn) {
            generateBtn.disabled = count === 0;
            generateBtn.style.opacity = count === 0 ? '0.5' : '1';
        }

        // Update hidden JSON input
        const bomData = ids.map(function(id) {
            const entry = selectedItems[id];
            return {
                item_id: parseInt(id),
                qty_required: entry.qty_required,
                notes: entry.notes || ''
            };
        });
        bomItemsJson.value = JSON.stringify(bomData);
    }

    // Filter items based on search, category, in-stock
    function filterItems() {
        const search = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const category = categoryFilter ? categoryFilter.value : '';
        const instockOnly = instockToggle ? instockToggle.checked : false;

        let filtered = items.filter(function(item) {
            // Search filter
            if (search) {
                const codeMatch = item.code.toLowerCase().includes(search);
                const descMatch = item.description.toLowerCase().includes(search);
                if (!codeMatch && !descMatch) return false;
            }

            // Category filter
            if (category && item.category !== category) return false;

            // In-stock only filter
            if (instockOnly && item.qty_on_hand <= 0) return false;

            return true;
        });

        renderItemTable(filtered);
    }

    // Utility: escape HTML
    function escHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Initialize event listeners
    function init() {
        if (searchInput) {
            searchInput.addEventListener('input', filterItems);
        }
        if (categoryFilter) {
            categoryFilter.addEventListener('change', filterItems);
        }
        if (instockToggle) {
            instockToggle.addEventListener('change', filterItems);
        }

        // Initial render
        filterItems();
        updateSummary();
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();