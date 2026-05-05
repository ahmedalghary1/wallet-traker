from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import BankAccount, SystemSettings, Transaction, Wallet


FORM_CONTROL = "form-control"
FORM_SELECT = "form-select"


def apply_widget_classes(form):
    for field in form.fields.values():
        widget = field.widget
        existing = widget.attrs.get("class", "")

        if isinstance(widget, forms.CheckboxInput):
            css_class = "form-check-input"
        elif isinstance(widget, forms.RadioSelect):
            css_class = "segmented-options"
        elif isinstance(widget, forms.Select):
            css_class = FORM_SELECT
        else:
            css_class = FORM_CONTROL

        widget.attrs["class"] = f"{existing} {css_class}".strip()


def validate_image_file(uploaded_file):
    if not uploaded_file:
        return

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    content_type = getattr(uploaded_file, "content_type", "")
    if content_type and content_type not in allowed_types:
        raise forms.ValidationError("يجب رفع ملف صورة فقط بصيغة JPG أو PNG أو WEBP.")


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ["name", "wallet_type", "phone_number", "opening_balance", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "مثال: محفظة المبيعات"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "مثال: 01000000000"}),
            "opening_balance": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_classes(self)


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ["bank_name", "account_name", "account_number", "notes", "is_active"]
        widgets = {
            "bank_name": forms.TextInput(attrs={"placeholder": "اسم البنك"}),
            "account_name": forms.TextInput(attrs={"placeholder": "اسم صاحب الحساب"}),
            "account_number": forms.TextInput(attrs={"placeholder": "رقم الحساب أو IBAN"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "ملاحظات اختيارية"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_classes(self)


class TransactionForm(forms.ModelForm):
    net_amount = forms.DecimalField(
        label="الصافي",
        required=False,
        decimal_places=2,
        max_digits=14,
        widget=forms.NumberInput(attrs={"readonly": "readonly", "step": "0.01"}),
    )

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "wallet",
            "bank_account",
            "customer_name",
            "customer_phone",
            "amount",
            "fee",
            "reference_number",
            "transaction_date",
            "receipt_image",
            "notes",
        ]
        widgets = {
            "transaction_type": forms.RadioSelect(),
            "customer_name": forms.TextInput(attrs={"placeholder": "اسم العميل"}),
            "customer_phone": forms.TextInput(attrs={"placeholder": "رقم العميل"}),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "fee": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "reference_number": forms.TextInput(attrs={"placeholder": "رقم العملية إن وجد"}),
            "transaction_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "receipt_image": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "ملاحظات اختيارية"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["wallet"].queryset = Wallet.objects.filter(is_active=True).order_by("name")
        self.fields["bank_account"].queryset = BankAccount.objects.filter(is_active=True).order_by(
            "bank_name", "account_name"
        )
        self.fields["bank_account"].required = False
        self.fields["transaction_date"].input_formats = ["%Y-%m-%dT%H:%M"]

        if not self.is_bound:
            self.fields["transaction_date"].initial = timezone.localtime().strftime(
                "%Y-%m-%dT%H:%M"
            )
            if self.instance and self.instance.pk:
                self.fields["net_amount"].initial = self.instance.net_amount
                self.fields["transaction_date"].initial = timezone.localtime(
                    self.instance.transaction_date
                ).strftime("%Y-%m-%dT%H:%M")
            else:
                self.fields["net_amount"].initial = Decimal("0.00")

        apply_widget_classes(self)

    def clean_receipt_image(self):
        receipt = self.cleaned_data.get("receipt_image")
        validate_image_file(receipt)
        return receipt

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get("transaction_type")
        amount = cleaned_data.get("amount") or Decimal("0.00")
        fee = cleaned_data.get("fee") or Decimal("0.00")

        if amount <= 0:
            self.add_error("amount", "المبلغ يجب أن يكون أكبر من صفر.")
        if fee < 0:
            self.add_error("fee", "العمولة لا يمكن أن تكون أقل من صفر.")
        if amount - fee < 0:
            self.add_error("fee", "الصافي لا يمكن أن يكون أقل من صفر.")

        if transaction_type == Transaction.WALLET_TO_BANK and not cleaned_data.get(
            "bank_account"
        ):
            self.add_error("bank_account", "الحساب البنكي مطلوب عند التحويل إلى البنك.")

        if transaction_type == Transaction.CUSTOMER_PAYMENT:
            cleaned_data["bank_account"] = None

        if transaction_type == Transaction.WALLET_TO_BANK:
            cleaned_data["customer_name"] = ""
            cleaned_data["customer_phone"] = ""

        return cleaned_data


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            "company_name",
            "company_logo",
            "default_currency",
            "backup_directory",
            "notes",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"placeholder": "اسم الشركة"}),
            "company_logo": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "default_currency": forms.TextInput(attrs={"placeholder": "جنيه"}),
            "backup_directory": forms.TextInput(
                attrs={"placeholder": r"C:\Backups\Wallet Tracker"}
            ),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "ملاحظات اختيارية"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_classes(self)

    def clean_company_logo(self):
        logo = self.cleaned_data.get("company_logo")
        validate_image_file(logo)
        return logo

    def clean_backup_directory(self):
        return (self.cleaned_data.get("backup_directory") or "").strip()
