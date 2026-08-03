/* item_picker.js — lightweight offline inline catalogue autocomplete.
 *
 * Shared by the Purchase Order upload review screen and the PO edit screen.
 * No vendor libraries: filters a plain JS array (window.SOPS_ITEMS, an array
 * of item_to_bom_json payloads) and renders a small dropdown under a text
 * input. Selecting a hit writes the chosen item back onto the owning row and
 * fires an onSelect callback so the page can re-sync its lines_json.
 *
 * Usage:
 *   ItemPicker.attach(inputEl, {
 *       items: window.SOPS_ITEMS,
 *       onSelect: function (item) { ... },   // item may be null when cleared
 *       max: 20
 *   });
 */
window.ItemPicker = (function () {
    'use strict';

    function escHtml(str) {
        if (str === null || str === undefined) return '';
        var d = document.createElement('div');
        d.appendChild(document.createTextNode(String(str)));
        return d.innerHTML;
    }

    function attach(input, opts) {
        opts = opts || {};
        var items = opts.items || [];
        var max = opts.max || 20;
        var onSelect = typeof opts.onSelect === 'function' ? opts.onSelect : function () {};

        // Wrap the input so the dropdown can position relative to it.
        var wrap = document.createElement('div');
        wrap.className = 'item-picker';
        wrap.style.position = 'relative';
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);

        var menu = document.createElement('div');
        menu.className = 'item-picker-menu';
        menu.style.cssText =
            'position:absolute;z-index:50;left:0;right:0;top:100%;max-height:240px;' +
            'overflow-y:auto;background:var(--bg-primary,#fff);border:1px solid ' +
            'var(--border-color,#ccc);border-radius:6px;box-shadow:0 4px 12px ' +
            'rgba(0,0,0,0.15);display:none;';
        wrap.appendChild(menu);

        function close() { menu.style.display = 'none'; menu.innerHTML = ''; }

        function filter(term) {
            term = (term || '').toLowerCase().trim();
            if (!term) return [];
            var out = [];
            for (var i = 0; i < items.length && out.length < max; i++) {
                var it = items[i];
                var code = (it.code || '').toLowerCase();
                var desc = (it.description || '').toLowerCase();
                if (code.indexOf(term) !== -1 || desc.indexOf(term) !== -1) out.push(it);
            }
            return out;
        }

        function render(hits) {
            if (!hits.length) { close(); return; }
            var html = '';
            for (var i = 0; i < hits.length; i++) {
                var it = hits[i];
                html += '<div class="item-picker-opt" data-idx="' + i + '" ' +
                    'style="padding:6px 10px;cursor:pointer;font-size:0.85rem;' +
                    'border-bottom:1px solid var(--border-color,#eee);">' +
                    '<strong>' + escHtml(it.code) + '</strong> — ' +
                    escHtml(it.description) + '</div>';
            }
            menu.innerHTML = html;
            menu.style.display = 'block';
            var opts_ = menu.querySelectorAll('.item-picker-opt');
            for (var j = 0; j < opts_.length; j++) {
                (function (idx) {
                    var el = opts_[idx];
                    el.addEventListener('mousedown', function (e) {
                        // mousedown (not click) so it fires before input blur
                        e.preventDefault();
                        pick(hits[idx]);
                    });
                    el.addEventListener('mouseenter', function () {
                        el.style.background = 'rgba(232, 97, 10, 0.08)';
                    });
                    el.addEventListener('mouseleave', function () {
                        el.style.background = '';
                    });
                })(j);
            }
        }

        function pick(item) {
            input.value = item.code + ' — ' + (item.description || '');
            close();
            onSelect(item);
        }

        input.addEventListener('input', function () {
            // Editing the text invalidates any prior selection until re-picked.
            onSelect(null);
            render(filter(input.value));
        });
        input.addEventListener('focus', function () {
            if (input.value) render(filter(input.value));
        });
        input.addEventListener('blur', function () {
            // Delay so a menu mousedown selection lands first.
            setTimeout(close, 150);
        });

        return { close: close };
    }

    return { attach: attach };
})();
