(function () {
    function toNumber(value) {
        var number = parseFloat(value);
        return Number.isFinite(number) ? number : 0;
    }

    function formatMoney(value) {
        return Math.max(value, 0).toFixed(2);
    }

    function updateNetAmount(form) {
        var amountInput = form.querySelector("#id_amount");
        var feeInput = form.querySelector("#id_fee");
        var netInput = form.querySelector("#id_net_amount");

        if (!amountInput || !feeInput || !netInput) {
            return;
        }

        var net = toNumber(amountInput.value) - toNumber(feeInput.value);
        netInput.value = Number.isFinite(net) ? net.toFixed(2) : "0.00";
        netInput.classList.toggle("is-invalid", net < 0);
    }

    function selectedTransactionType(form) {
        var checked = form.querySelector("input[name='transaction_type']:checked");
        var select = form.querySelector("select[name='transaction_type']");
        return checked ? checked.value : select ? select.value : "";
    }

    function toggleTransactionFields(form) {
        var type = selectedTransactionType(form);
        var bankFields = form.querySelectorAll("[data-bank-field]");
        var customerFields = form.querySelectorAll("[data-customer-field]");
        var bankSelect = form.querySelector("#id_bank_account");
        var isBankTransfer = type === "wallet_to_bank";

        bankFields.forEach(function (field) {
            field.hidden = !isBankTransfer;
        });

        customerFields.forEach(function (field) {
            field.hidden = isBankTransfer;
        });

        if (bankSelect) {
            bankSelect.required = isBankTransfer;
            if (!isBankTransfer) {
                bankSelect.value = "";
            }
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var sidebarToggle = document.querySelector("[data-sidebar-toggle]");
        if (sidebarToggle) {
            sidebarToggle.addEventListener("click", function () {
                document.body.classList.toggle("sidebar-open");
            });
        }

        document.querySelectorAll("[data-net-form]").forEach(function (form) {
            var amountInput = form.querySelector("#id_amount");
            var feeInput = form.querySelector("#id_fee");
            var typeInputs = form.querySelectorAll("input[name='transaction_type'], select[name='transaction_type']");

            if (amountInput) {
                amountInput.addEventListener("input", function () {
                    updateNetAmount(form);
                });
            }

            if (feeInput) {
                feeInput.addEventListener("input", function () {
                    updateNetAmount(form);
                });
            }

            typeInputs.forEach(function (input) {
                input.addEventListener("change", function () {
                    toggleTransactionFields(form);
                });
            });

            form.addEventListener("submit", function (event) {
                updateNetAmount(form);
                var amount = toNumber(amountInput ? amountInput.value : 0);
                var fee = toNumber(feeInput ? feeInput.value : 0);

                if (amount <= 0 || fee < 0 || amount - fee < 0) {
                    event.preventDefault();
                    alert("برجاء مراجعة المبلغ والعمولة، الصافي لا يمكن أن يكون أقل من صفر.");
                }
            });

            updateNetAmount(form);
            toggleTransactionFields(form);
        });

        document.querySelectorAll(".js-confirm-delete").forEach(function (button) {
            button.addEventListener("click", function (event) {
                var confirmed = window.confirm("هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذا الإجراء.");
                if (!confirmed) {
                    event.preventDefault();
                }
            });
        });

        document.querySelectorAll("[data-backup-directory-picker]").forEach(function (button) {
            button.addEventListener("click", function () {
                var targetSelector = button.getAttribute("data-target");
                var targetInput = targetSelector ? document.querySelector(targetSelector) : null;

                if (
                    !targetInput ||
                    !window.walletTracker ||
                    typeof window.walletTracker.selectBackupDirectory !== "function"
                ) {
                    alert("اختيار المجلد متاح داخل نسخة سطح المكتب فقط. يمكنك كتابة المسار يدويًا هنا.");
                    return;
                }

                window.walletTracker.selectBackupDirectory().then(function (directory) {
                    if (directory) {
                        targetInput.value = directory;
                    }
                });
            });
        });
    });
})();
