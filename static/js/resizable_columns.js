/**
 * Lightweight drag-to-resize columns for plain <table class="data-table">
 * list pages (Sales/Works/Stock/Purchase Orders). No dependency, no CDN.
 * Widths persist per-table in localStorage so a resize survives a reload.
 */
(function () {
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

    function applyStoredColumnWidths(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;
        var widths = loadWidths(tableId);
        if (!widths) return;

        var headerCells = table.querySelectorAll('thead th');
        table.style.tableLayout = 'fixed';
        headerCells.forEach(function (th, i) {
            if (widths[i]) th.style.width = widths[i] + 'px';
        });
    }

    function makeColumnsResizable(tableId) {
        var table = document.getElementById(tableId);
        if (!table) return;

        applyStoredColumnWidths(tableId);
        table.style.tableLayout = 'fixed';

        var headerCells = Array.prototype.slice.call(table.querySelectorAll('thead th'));
        headerCells.forEach(function (th, index) {
            th.style.position = 'relative';

            var handle = document.createElement('div');
            handle.className = 'col-resize-handle';
            handle.style.cssText =
                'position:absolute; top:0; right:0; width:6px; height:100%; ' +
                'cursor:col-resize; user-select:none; z-index:1;';
            th.appendChild(handle);

            var startX, startWidth;

            handle.addEventListener('mousedown', function (e) {
                startX = e.pageX;
                startWidth = th.offsetWidth;
                document.body.style.userSelect = 'none';

                function onMouseMove(e) {
                    var newWidth = Math.max(40, startWidth + (e.pageX - startX));
                    th.style.width = newWidth + 'px';
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
    }

    window.applyStoredColumnWidths = applyStoredColumnWidths;
    window.makeColumnsResizable = makeColumnsResizable;
})();
