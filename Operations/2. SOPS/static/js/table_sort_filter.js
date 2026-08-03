/**
 * Click-to-sort + per-column text filter for plain <table class="data-table">
 * list pages (Sales/Works/Stock/Purchase Orders). No dependency, no CDN.
 *
 * - Click a sortable <th> to sort tbody rows by that column (toggles asc/desc).
 * - Sort key per row: td.dataset.sort if present, else the cell's trimmed textContent.
 * - Each sortable <th> gets a small text filter <input> injected below its label.
 *   Multiple active column filters combine with AND (case-insensitive substring).
 * - <th data-sortable="false"> (e.g. the Actions column) gets no sort/filter UI.
 * - Exposes window.updateTableRowVisibility(row) so other scripts (e.g. the
 *   Sales Orders free-text search box) can compose with column filtering
 *   without both features fighting over row.style.display directly.
 */
(function () {
    function isNumericString(str) {
        return str !== '' && /^-?\d+(\.\d+)?$/.test(str);
    }

    function getSortValue(td) {
        if (!td) return '';
        if (td.dataset && 'sort' in td.dataset) return td.dataset.sort;
        return (td.textContent || '').trim();
    }

    function compareSortValues(a, b) {
        if (isNumericString(a) && isNumericString(b)) {
            return parseFloat(a) - parseFloat(b);
        }
        return a.toLowerCase().localeCompare(b.toLowerCase());
    }

    function sortRows(table, colIndex, ascending) {
        var tbody = table.tBodies[0];
        if (!tbody) return;
        var rows = Array.prototype.slice.call(tbody.rows);
        rows.sort(function (rowA, rowB) {
            var cmp = compareSortValues(getSortValue(rowA.cells[colIndex]), getSortValue(rowB.cells[colIndex]));
            return ascending ? cmp : -cmp;
        });
        rows.forEach(function (row) { tbody.appendChild(row); });
    }

    function applyColumnFilters(table, filterInputs) {
        var tbody = table.tBodies[0];
        if (!tbody) return;

        var activeFilters = [];
        filterInputs.forEach(function (input, colIndex) {
            if (input && input.value.trim() !== '') {
                activeFilters.push({ colIndex: colIndex, value: input.value.trim().toLowerCase() });
            }
        });

        Array.prototype.slice.call(tbody.rows).forEach(function (row) {
            var hidden = false;
            for (var i = 0; i < activeFilters.length; i++) {
                var filter = activeFilters[i];
                var cell = row.cells[filter.colIndex];
                var text = cell ? (cell.textContent || '').trim().toLowerCase() : '';
                if (text.indexOf(filter.value) === -1) {
                    hidden = true;
                    break;
                }
            }
            row.dataset.hiddenByColumnFilter = hidden ? '1' : '0';
            window.updateTableRowVisibility(row);
        });
    }

    function makeTableSortableFilterable(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;

        var headerRow = table.tHead && table.tHead.rows[0];
        if (!headerRow) return;

        var headerCells = Array.prototype.slice.call(headerRow.cells);
        var filterInputs = [];
        var indicators = [];
        var sortState = { colIndex: -1, ascending: true };

        headerCells.forEach(function (th, index) {
            if (th.dataset.sortable === 'false') {
                filterInputs.push(null);
                indicators.push(null);
                return;
            }

            // Move the header's existing content (but not a resize handle that
            // resizable_columns.js may have already injected) into a label
            // wrapper, so we can append a sort indicator + filter input below
            // without disturbing the resize handle's absolute positioning.
            var label = document.createElement('span');
            label.className = 'th-label';

            Array.prototype.slice.call(th.childNodes).forEach(function (node) {
                if (node.nodeType === 1 && node.classList && node.classList.contains('col-resize-handle')) {
                    return;
                }
                label.appendChild(node);
            });

            var indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.style.marginLeft = '4px';
            label.appendChild(indicator);
            indicators.push(indicator);

            th.insertBefore(label, th.firstChild);
            th.style.cursor = 'pointer';

            th.addEventListener('click', function (e) {
                if (e.target && e.target.classList &&
                    (e.target.classList.contains('col-filter-input') || e.target.classList.contains('col-resize-handle'))) {
                    return;
                }

                sortState.ascending = (sortState.colIndex === index) ? !sortState.ascending : true;
                sortState.colIndex = index;

                indicators.forEach(function (ind) { if (ind) ind.textContent = ''; });
                indicator.textContent = sortState.ascending ? '▲' : '▼';

                sortRows(table, index, sortState.ascending);
            });

            var filterInput = document.createElement('input');
            filterInput.type = 'text';
            filterInput.className = 'col-filter-input';
            filterInput.placeholder = 'Filter…';
            filterInput.style.cssText =
                'display:block; width:calc(100% - 4px); margin-top:4px; margin-right:4px; ' +
                'padding:3px 6px; font-size:0.72rem; font-weight:400; text-transform:none; ' +
                'letter-spacing:normal; box-sizing:border-box;';
            filterInput.addEventListener('click', function (e) { e.stopPropagation(); });
            filterInput.addEventListener('input', function () {
                applyColumnFilters(table, filterInputs);
            });

            th.appendChild(filterInput);
            filterInputs.push(filterInput);
        });
    }

    window.updateTableRowVisibility = function (row) {
        var hiddenByColumnFilter = row.dataset.hiddenByColumnFilter === '1';
        var hiddenBySearch = row.dataset.hiddenBySearch === '1';
        row.style.display = (hiddenByColumnFilter || hiddenBySearch) ? 'none' : '';
    };

    window.makeTableSortableFilterable = makeTableSortableFilterable;
})();
