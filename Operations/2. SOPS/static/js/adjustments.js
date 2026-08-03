/* ============================================
   SOPS — Stock Adjustment JavaScript
   Handles inline quantity adjustment modals
   and form validation
   ============================================ */

(function() {
    'use strict';

    // Validate adjustment form before submission
    function initAdjustmentForm() {
        const adjustForm = document.querySelector('form[action*="adjust"]');
        if (!adjustForm) return;

        adjustForm.addEventListener('submit', function(e) {
            const newQtyInput = document.getElementById('new_qty');
            const reasonInput = document.getElementById('reason');
            let valid = true;

            // Validate quantity
            if (newQtyInput) {
                const qty = parseFloat(newQtyInput.value);
                if (isNaN(qty) || qty < 0) {
                    alert('Please enter a valid non-negative quantity.');
                    valid = false;
                }
            }

            // Validate reason
            if (reasonInput) {
                const reason = reasonInput.value.trim();
                if (!reason) {
                    alert('Please provide a reason for the adjustment.');
                    valid = false;
                }
            }

            if (!valid) {
                e.preventDefault();
            }
        });
    }

    // Quick-adjust inline on catalogue pages (future use)
    function initInlineAdjustment() {
        document.querySelectorAll('.inline-adjust-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.id;
                const itemCode = this.dataset.code;
                const currentQty = parseFloat(this.dataset.qty) || 0;

                const newQty = prompt('Adjust stock for ' + itemCode + ' (current: ' + currentQty + '):', currentQty);
                if (newQty !== null) {
                    // Navigate to adjustment endpoint via fetch or form submit
                    const form = document.getElementById('inline-adjust-form-' + itemId);
                    if (form) {
                        form.querySelector('[name="new_qty"]').value = newQty;
                        form.submit();
                    }
                }
            });
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initAdjustmentForm();
            initInlineAdjustment();
        });
    } else {
        initAdjustmentForm();
        initInlineAdjustment();
    }
})();