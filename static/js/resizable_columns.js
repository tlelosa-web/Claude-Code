/**
 * Lightweight drag-to-resize columns for plain <table class="data-table">
 * list pages (Sales/Works/Stock/Purchase Orders). No dependency, no CDN.
 * Widths persist per-table in localStorage so a resize survives a reload.
 *
 * Design (Batch 35 — frozen headers + no horizontal scroll):
 * - Zero-sum drag: the handle on column i grows/shrinks the pair
 *   (i, i+1) by the same amount, so the table's total width never
 *   changes. The last column (Actions on all 4 lists) has no right-hand
 *   neighbour and gets no handle.
 * - Scale-to-fit on load and on window resize: stored/current widths are
 *   proportionally rescaled to exactly fill the table's container, with
 *   every column clamped to MIN_COL_WIDTH. This self-heals legacy saved
 *   widths (oversized totals, sub-minimum columns) instead of erroring or
 *   resetting, and guarantees the table can never overflow its card.
 */
(function () {
    var MIN_COL_WIDTH = 40;
    var RESIZE_DEBOUNCE_MS = 150;
    var registeredTables = [];

    function storageKey(tableId) {
        return 'colwidths:' + tableId;
    }

    function loadWidths(tableId) {
        try {
            var raw = window.localStorage.getItem(storageKey(tableId));
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function saveWidths(tableId, widths) {
        try {
            window.localStorage.setItem(storageKey(tableId), JSON.stringify(widths));
        } catch (e) {
            // localStorage unavailable — resizing still works, just doesn't persist.
        }
    }

    function getContainerWidth(table) {
        var container = table.parentElement;
        return (container && container.clientWidth) || table.clientWidth || 0;
    }

    // Proportionally scale `widths` (array of px numbers, one per header
    // cell) so they sum to exactly `targetWidth`, clamping each column at
    // MIN_COL_WIDTH and assigning any rounding remainder to the last
    // column. Self-heals legacy saved data (oversized totals, columns
    // dragged below the floor) rather than erroring or resetting.
    function scaleToFit(widths, targetWidth) {
        var n = widths.length;
        if (n === 0) return [];

        var sum = widths.reduce(function (a, b) { return a + b; }, 0);
        if (sum <= 0) {
            widths = widths.map(function () { return 1; });
            sum = n;
        }

        var target = Math.round(targetWidth);
        var scaled = widths.map(function (w) {
            return Math.max(MIN_COL_WIDTH, Math.round((w / sum) * target));
        });

        if (n > 1) {
            var sumExceptLast = 0;
            for (var i = 0; i < n - 1; i++) sumExceptLast += scaled[i];
            scaled[n - 1] = Math.max(MIN_COL_WIDTH, target - sumExceptLast);
        } else {
            scaled[0] = Math.max(MIN_COL_WIDTH, target);
        }

        return scaled;
    }

    function applyStoredColumnWidths(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;
        var widths = loadWidths(tableId);
        if (!widths || !widths.length) return;

        var headerCells = table.querySelectorAll('thead th');
        if (!headerCells.length) return;
        table.style.tableLayout = 'fixed';

        var n = headerCells.length;
        var normalizedInput = [];
        for (var i = 0; i < n; i++) {
            var w = widths[i];
            normalizedInput.push((typeof w === 'number' && w > 0) ? w : MIN_COL_WIDTH);
        }

        var targetWidth = getContainerWidth(table);
        if (!targetWidth || targetWidth <= 0) {
            // Container not yet laid out (rare) — apply raw values; the
            // next resize pass will scale-to-fit once real geometry exists.
            headerCells.forEach(function (th, i) { th.style.width = normalizedInput[i] + 'px'; });
            return;
        }

        var scaled = scaleToFit(normalizedInput, targetWidth);
        headerCells.forEach(function (th, i) { th.style.width = scaled[i] + 'px'; });
        saveWidths(tableId, scaled);
    }

    function rescaleTable(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;
        var headerCells = table.querySelectorAll('thead th');
        if (!headerCells.length) return;

        var currentWidths = Array.prototype.map.call(headerCells, function (th) {
            return th.offsetWidth;
        });
        var targetWidth = getContainerWidth(table);
        if (!targetWidth || targetWidth <= 0) return;

        var scaled = scaleToFit(currentWidths, targetWidth);
        headerCells.forEach(function (th, i) { th.style.width = scaled[i] + 'px'; });
        saveWidths(tableId, scaled);
    }

    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var args = arguments;
            var ctx = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, wait);
        };
    }

    function makeColumnsResizable(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;

        applyStoredColumnWidths(tableId);
        table.style.tableLayout = 'fixed';

        var headerCells = Array.prototype.slice.call(table.querySelectorAll('thead th'));
        var n = headerCells.length;

        headerCells.forEach(function (th, index) {
            // Also the positioned ancestor for the absolutely-positioned
            // resize handle below.
            th.style.position = 'sticky';

            // Zero-sum resize: the last column has no right-hand neighbour
            // to trade width with, so it gets no handle.
            if (index >= n - 1) return;

            var handle = document.createElement('div');
            handle.className = 'col-resize-handle';
            handle.style.cssText =
                'position:absolute; top:0; right:0; width:6px; height:100%; ' +
                'cursor:col-resize; user-select:none; z-index:1;';
            th.appendChild(handle);

            var rightTh = headerCells[index + 1];
            var startX, leftStartWidth, rightStartWidth, pairWidth;

            handle.addEventListener('mousedown', function (e) {
                startX = e.pageX;
                leftStartWidth = th.offsetWidth;
                rightStartWidth = rightTh.offsetWidth;
                pairWidth = leftStartWidth + rightStartWidth;
                document.body.style.userSelect = 'none';

                function onMouseMove(e) {
                    var delta = e.pageX - startX;
                    var newLeft = leftStartWidth + delta;
                    var newRight = pairWidth - newLeft;

                    if (newLeft < MIN_COL_WIDTH) {
                        newLeft = MIN_COL_WIDTH;
                        newRight = pairWidth - newLeft;
                    } else if (newRight < MIN_COL_WIDTH) {
                        newRight = MIN_COL_WIDTH;
                        newLeft = pairWidth - newRight;
                    }

                    th.style.width = newLeft + 'px';
                    rightTh.style.width = newRight + 'px';
                }

                function onMouseUp() {
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    document.body.style.userSelect = '';

                    var widths = headerCells.map(function (cell) { return cell.offsetWidth; });
                    saveWidths(tableId, widths);
                }

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
                e.preventDefault();
            });
        });

        if (registeredTables.indexOf(tableId) === -1) {
            registeredTables.push(tableId);
        }
    }

    window.addEventListener('resize', debounce(function () {
        registeredTables.forEach(rescaleTable);
    }, RESIZE_DEBOUNCE_MS));

    window.applyStoredColumnWidths = applyStoredColumnWidths;
    window.makeColumnsResizable = makeColumnsResizable;
})();
